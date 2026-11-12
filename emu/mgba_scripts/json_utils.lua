--[[
    Simple JSON encoder/decoder for mGBA Lua environment
    This provides basic JSON functionality without external dependencies
]]

local log_manager = require("log_manager")
local lm = log_manager.create_logger("JSON_UTILS")

local json_utils = {}

-- Simple JSON encoder with pretty printing
function json_utils.encode(obj, indent_level)
    indent_level = indent_level or 0
    local indent = string.rep("  ", indent_level)
    local next_indent = string.rep("  ", indent_level + 1)
    
    local t = type(obj)
    if t == "table" then
        -- Check if it's an array (sequential numeric keys starting from 1)
        local is_array = true
        local max_index = 0
        for k, v in pairs(obj) do
            if type(k) ~= "number" or k < 1 or k ~= math.floor(k) then
                is_array = false
                break
            end
            max_index = math.max(max_index, k)
        end
        
        if is_array and max_index == #obj then
            -- It's an array, encode as array
            if #obj == 0 then
                return "[]"
            end
            local result = "[\n"
            for i = 1, #obj do
                if i > 1 then result = result .. ",\n" end
                result = result .. next_indent .. json_utils.encode(obj[i], indent_level + 1)
            end
            return result .. "\n" .. indent .. "]"
        else
            -- It's an object, encode as object
            local keys = {}
            for k in pairs(obj) do
                table.insert(keys, k)
            end
            if #keys == 0 then
                return "{}"
            end
            local result = "{\n"
            for i, k in ipairs(keys) do
                if i > 1 then result = result .. ",\n" end
                result = result .. next_indent .. '"' .. tostring(k) .. '": ' .. json_utils.encode(obj[k], indent_level + 1)
            end
            return result .. "\n" .. indent .. "}"
        end
    elseif t == "string" then
        return '"' .. obj:gsub('"', '\\"') .. '"'
    elseif t == "number" or t == "boolean" then
        return tostring(obj)
    else
        return "null"
    end
end

-- Simple JSON decoder for basic cases
function json_utils.decode(str)
    -- Handle empty or whitespace-only strings
    if not str or str:match("^%s*$") then
        return {}
    end
    
    -- Handle empty array
    if str:match("^%s*%[%s*%]%s*$") then
        return {}
    end
    
    -- Handle array with objects: [{...}, {...}, ...]
    if str:match("^%s*%[%s*{.*}%s*%]%s*$") then
        lm.log("Parsing array: " .. str)
        
        -- Extract content between [ and ]
        local content = str:match("^%s*%[%s*(.*)%s*%]%s*$")
        if not content then
            return {}
        end
        
        -- Simple parsing: split by "},{"
        local result = {}
        local objects = {}
        
        -- Find all complete objects
        for obj_str in content:gmatch("{[^}]+}") do
            table.insert(objects, obj_str)
        end
        
        lm.log("Found " .. #objects .. " objects")
        
        -- Convert each object string to a simple table
        for i, obj_str in ipairs(objects) do
            -- Create a simple table with the object data
            local obj = {}
            -- Extract key-value pairs
            for key, value in obj_str:gmatch('"([^"]+)"%s*:%s*([^,}]+)') do
                -- Convert value to appropriate type
                if value == "true" then
                    obj[key] = true
                elseif value == "false" then
                    obj[key] = false
                elseif tonumber(value) then
                    obj[key] = tonumber(value)
                else
                    -- Remove quotes from string values
                    obj[key] = value:gsub('^"', ''):gsub('"$', '')
                end
            end
            table.insert(result, obj)
        end
        
        return result
    end
    
    -- For other cases, return empty array
    lm.log("Unrecognized JSON format, returning empty array")
    return {}
end

return json_utils 