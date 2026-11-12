--[[
    Simple logging wrapper utility with per-module verbosity control
]]

-- Turn on to see (more) logging in mGBA scripting console

local log_manager = {}

-- Global verbosity settings
log_manager.global_verbose_log = true
log_manager.global_verbose_error = true
log_manager.global_verbose_warn = true

-- Per-module verbosity settings
log_manager.module_verbose = {
    -- Example: ["JSON_UTILS"] = true,
    -- Example: ["STATE_MGR"] = false,
}

-- Set verbosity for a specific module
function log_manager.set_module_verbose(module_id, verbose)
    log_manager.module_verbose[module_id] = verbose
end

-- Set verbosity for multiple modules at once
function log_manager.set_modules_verbose(modules, verbose)
    for _, module_id in ipairs(modules) do
        log_manager.module_verbose[module_id] = verbose
    end
end

-- Check if a module should be verbose
function log_manager.is_module_verbose(module_id)
    -- If module-specific setting exists, use it
    if log_manager.module_verbose[module_id] ~= nil then
        return log_manager.module_verbose[module_id]
    end
    -- Otherwise use global setting
    return log_manager.global_verbose_log
end

function log_manager.log(msg, module_id)
    if log_manager.is_module_verbose(module_id) then
        local prefix = module_id and ("[" .. module_id .. "] ") or ""
        console:log(prefix .. msg)
    end
end

function log_manager.error(msg, module_id)
    if log_manager.global_verbose_error then
        local prefix = module_id and ("[" .. module_id .. "] ") or ""
        console:error(prefix .. msg)
    end
end

function log_manager.warn(msg, module_id)
    if log_manager.global_verbose_warn then
        local prefix = module_id and ("[" .. module_id .. "] ") or ""
        console:warn(prefix .. msg)
    end
end

-- Convenience function to create a module-specific logger
function log_manager.create_logger(module_id)
    return {
        log = function(msg) log_manager.log(msg, module_id) end,
        error = function(msg) log_manager.error(msg, module_id) end,
        warn = function(msg) log_manager.warn(msg, module_id) end,
        set_verbose = function(verbose) log_manager.set_module_verbose(module_id, verbose) end
    }
end

return log_manager