--[[
	Input instructions are sent from the client as serialized bitmasks. This is the decimal equivalent
	of a binary string in which the state of each key is represented by its associated bit (1 or 0, pressed or released).
	Passing instructions in this way is efficient, and also allows for multiple keys to be changed with a single bitmask.
	These are distinguished from other messages by also being prefixed with a specific control character.

	Basic host/client communication (see functions ST_*) is based loosely on mGBA test script(s) from official repo.
]]

local state_manager = require("state_manager")
-- state_manager.initialize_state()
-- Python passes the port and slot. Falling back to the shared state file lets
-- two windows swap ports, and the restart then kills the neighbor.
local slot_id = os.getenv("PKBT_SLOT")
local env_port = os.getenv("PKBT_PORT")
local instance = nil
if not env_port then
	instance = state_manager.create_instance()
	console:log("Created instance with port " .. instance.port .. " and timestamp " .. instance.timestamp)
else
	console:log("Using assigned port " .. env_port .. " for slot " .. tostring(slot_id))
end

-- Frame counter for the host, named by the slot that launched this process.
local heartbeat_frame = 0
local heartbeat_path = slot_id and ("temp/frame_slot_" .. slot_id .. ".txt") or ("temp/frame_" .. instance.port .. ".txt")
callbacks:add("frame", function()
	heartbeat_frame = heartbeat_frame + 1
	if heartbeat_frame % 120 ~= 0 then
		return
	end
	local f = io.open(heartbeat_path, "w")
	if not f then
		return
	end
	f:write(tostring(heartbeat_frame))
	f:close()
end)

--[[ begin section Bitmask Utilities ]]
local PK_KEY_STATE_CTRL_CHAR = "\x01"

function PK_is_valid_key_state_bitmask_str(ks_str)
	-- Check if string starts with key state control character, which is used to
	-- distinguish key state messages from other messages.
	if string.sub(ks_str, 1, 1) == PK_KEY_STATE_CTRL_CHAR then
		return true
	else
		return false
	end
end

function PK_handle_key_state_bitmask(ks_bitmask)
	-- Remove control character and convert to number
    local bitmask = tonumber(string.sub(ks_bitmask, 2))
    -- console:log("Received bitmask: " .. bitmask)
    emu:setKeys(bitmask)
end
--[[ end section Bitmask Utilities ]]

--[[ begin section Reset Utilities ]]
-- Reset is a special case because it is not a key state, but rather a control character.
-- It is used to reset the game to the initial state.
local PK_RESET_CTRL_CHAR = "\x02"
function PK_is_reset_cmd(str)
	if string.sub(str, 1, 1) == PK_RESET_CTRL_CHAR then
		return true
	end
end

function PK_handle_reset()
	console:log("Resetting game")
	emu:setKeys(0)
	emu:reset()
end
--[[ end section Reset Utilities ]]

--[[ begin section Screenshot Utilities ]]
local PK_SCREENSHOT_CTRL_CHAR = "\x03"
function PK_is_screenshot_cmd(str)
	if string.sub(str, 1, 1) == PK_SCREENSHOT_CTRL_CHAR then
		return true
	end
end

function PK_handle_screenshot(str)
	local filename = string.sub(str, 2)
	console:log("Taking screenshot to " .. filename)
	emu:screenshot("temp/" .. filename)
end
--[[ end section Screenshot Utilities ]]

--[[ begin section Fast Forward Utilities ]]
local PK_FAST_FORWARD_CTRL_CHAR = "\x04"
function PK_is_fast_forward_cmd(str)
	return string.sub(str, 1, 1) == PK_FAST_FORWARD_CTRL_CHAR
end

function PK_handle_fast_forward(str)
	local enable = string.sub(str, 2, 2) ~= "0"
	local ok, err = pcall(function()
		emu:setFastForward(enable)
	end)
	if ok then
		console:log(enable and "Fast forward on" or "Fast forward off")
	else
		console:error("Fast forward is not available in this mGBA build: " .. tostring(err))
	end
end
--[[ end section Fast Forward Utilities ]]

--[[ begin section Repurposed mGBA Example Scripts Code ]]
server = nil
ST_sockets = {}
nextID = 1

function ST_stop(id)
	local sock = ST_sockets[id]
	ST_sockets[id] = nil
	sock:close()
end

function ST_format(id, msg, isError)
	local prefix = "Socket " .. id
	if isError then
		prefix = prefix .. " Error: "
	else
		prefix = prefix .. " Received: "
	end
	return prefix .. msg
end

function ST_error(id, err)
	console:error(ST_format(id, err, true))
	ST_stop(id)
end

local _buf = ""  -- single-socket buffer
function ST_received(id)
    local sock = ST_sockets[id]
    if not sock then return end

    while true do
        local chunk, err = sock:receive(1024)
        if not chunk then
            if err == socket.ERRORS.AGAIN then return end
            console:error(ST_format(id, err, true)); ST_stop(id); return
        end

        _buf = _buf .. chunk
        while true do
            local line, rest = _buf:match("^(.-)\r?\n(.*)$")  -- CRLF or LF
            if not line then break end
            _buf = rest

            if PK_is_valid_key_state_bitmask_str(line) then
                PK_handle_key_state_bitmask(line)
            elseif PK_is_reset_cmd(line) then
                PK_handle_reset()
            elseif PK_is_screenshot_cmd(line) then
                PK_handle_screenshot(line)
            elseif PK_is_fast_forward_cmd(line) then
                PK_handle_fast_forward(line)
            end
        end
    end
end

function ST_accept()
	local sock, err = server:accept()
	if err then
		console:error(ST_format("Accept", err, true))
		return
	end
	local id = nextID
	nextID = id + 1
	ST_sockets[id] = sock
	sock:add("received", function() ST_received(id) end)
	sock:add("error", function() ST_error(id) end)
	console:log(ST_format(id, "Connected"))
end

--[[ begin Main loop ]]
local function wait_seconds(seconds)
	local deadline = os.clock() + seconds
	while os.clock() < deadline do end
end

local port = env_port and tonumber(env_port) or instance.port
local fixed_port = env_port ~= nil
server = nil
local attempts = 0
local max_attempts = fixed_port and 20 or 50
while not server and attempts < max_attempts do
	attempts = attempts + 1
	server, err = socket.bind(nil, port)
	if err then
		if err == socket.ERRORS.ADDRESS_IN_USE and not fixed_port then
			port = port + 1
			server = nil
		elseif err == socket.ERRORS.ADDRESS_IN_USE then
			server = nil
			console:log("Port " .. port .. " is still in use, retrying")
			wait_seconds(0.25)
		else
			console:error(ST_format("Bind", err, true))
			break
		end
	else
		local ok
		ok, err = server:listen()
		if err then
			server:close()
			server = nil
			console:error(ST_format("Listen", err, true))
			break
		else
			console:log("Socket Server Test: Listening on port " .. port)
			server:add("received", ST_accept)
		end
	end
end
--[[ end Main loop ]]
--[[ end section Repurposed mGBA Example Scripts Code ]]