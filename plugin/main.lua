local pluginDir

function init(plugin)
  pluginDir = plugin.path
  local client = dofile(app.fs.joinPath(pluginDir, "client.lua"))

  plugin:newMenuGroup{
    id = "spriteforge_menu",
    title = "SpriteForge",
    group = "sprite_properties",
  }

  plugin:newCommand{
    id = "SpriteForgePing",
    title = "Check Server",
    group = "spriteforge_menu",
    onclick = function()
      client.ping(
        function() app.alert("SpriteForge server: OK") end,
        function(msg) app.alert("SpriteForge: " .. msg) end)
    end,
  }
  -- Generate / Edit / Inpaint commands are added in Tasks 10-11.
end

function exit(plugin) end
