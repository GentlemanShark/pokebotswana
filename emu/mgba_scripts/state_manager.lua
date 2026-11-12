--[[
    Maintains things like the ports and times created of the running instances, so the client
    knows where to connect to them.
]]

local json = require("json_utils")
local log_manager = require("log_manager")
local lm = log_manager.create_logger("STATE_MGR")

local FILE_PATH = "temp/pkbt_app_state.json"
local STARTING_PORT = 8888

local state_manager = {}

-- Create a new instance with dynamically chosen port
function state_manager.create_instance()
    lm.log("Creating new instance", "STATE_MGR")
    
    -- Try to read existing file
    local file = io.open(FILE_PATH, "r")
    local content = ""
    if file then
        lm.log("Found existing file, reading content", "STATE_MGR")
        content = file:read("*a")
        file:close()
    else
        lm.log("No existing file found, starting with empty array", "STATE_MGR")
        content = "[]"
    end

    -- Parse JSON
    local state = json.decode(content)
    if type(state) ~= "table" then
        lm.error("Invalid JSON content", "STATE_MGR")
        return nil
    end

    -- Find the highest port number from existing instances
    local highest_port = STARTING_PORT - 1
    for _, instance in ipairs(state) do
        if instance.port and instance.port > highest_port then
            highest_port = instance.port
        end
    end
    
    -- Choose next port
    local new_port = highest_port + 1
    lm.log("Chose port: " .. new_port, "STATE_MGR")
    
    -- Create new instance object
    local new_instance = {
        port = new_port,
        timestamp = os.time()
    }
    
    -- Add to state
    table.insert(state, new_instance)
    lm.log("Added new instance, total items: " .. #state, "STATE_MGR")

    -- Write back to file
    file = io.open(FILE_PATH, "w")
    if not file then
        lm.error("Could not write to " .. FILE_PATH, "STATE_MGR")
        return nil
    end
    file:write(json.encode(state))
    file:close()
    lm.log("Successfully wrote state to " .. FILE_PATH, "STATE_MGR")
    
    return new_instance
end

-- Avoid calling this function directly. Instead, use state_manager.create_instance()
-- to create a new instance with a dynamically chosen port.
function state_manager.add_instance(new_obj)
    lm.log("Attempting to read/write: " .. FILE_PATH, "STATE_MGR")
    
    -- Try to read existing file
    local file = io.open(FILE_PATH, "r")
    local content = ""
    if file then
        lm.log("Found existing file, reading content", "STATE_MGR")
        content = file:read("*a")
        file:close()
    else
        lm.log("No existing file found, starting with empty array", "STATE_MGR")
        content = "[]"
    end

    -- Parse JSON
    local state = json.decode(content)
    if type(state) ~= "table" then
        lm.error("Invalid JSON content", "STATE_MGR")
        return
    end

    -- Add the new object
    table.insert(state, new_obj)
    lm.log("Added object to state, total items: " .. #state, "STATE_MGR")

    -- Write back to file
    file = io.open(FILE_PATH, "w")
    if not file then
        lm.error("Could not write to " .. FILE_PATH, "STATE_MGR")
        return
    end
    file:write(json.encode(state))
    file:close()
    lm.log("Successfully wrote state to " .. FILE_PATH, "STATE_MGR")
end

-- Initialize the state file with an empty array
function state_manager.initialize_state()
    -- Check if file exists
    local file = io.open(FILE_PATH, "r")
    if file then
        lm.log("State file exists, clearing it", "STATE_MGR")
        file:close()
    else
        lm.log("State file does not exist, creating it", "STATE_MGR")
    end
    
    -- Create empty array
    local empty_state = {}
    
    -- Write empty array to file
    file = io.open(FILE_PATH, "w")
    if not file then
        lm.error("Could not write to " .. FILE_PATH, "STATE_MGR")
        return false
    end
    file:write(json.encode(empty_state))
    file:close()
    lm.log("Successfully initialized state file with empty array", "STATE_MGR")
    return true
end

return state_manager