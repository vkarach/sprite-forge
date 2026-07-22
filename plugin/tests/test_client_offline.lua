-- Plain-Lua tests for a server that vanishes mid-session: run with
-- `lua plugin/tests/test_client_offline.lua` from the repo root. Aseprite
-- throws from sendText on a dead socket; nothing may escape to the Console.
local failures = 0
local function ok(cond, what)
  if not cond then
    failures = failures + 1
    print("FAIL " .. what)
  end
end

_G.app = { fs = { joinPath = function(a, b) return a .. "/" .. b end } }
_G.json = { encode = function() return "{}" end,
            decode = function() return {} end }
_G.WebSocketMessageType = { OPEN = 1, TEXT = 2, CLOSE = 3 }
_G.Timer = nil

-- a socket whose sendText behaves like Aseprite's once the peer is gone
local sockets
local function stubSocket(sendWorks)
  _G.WebSocket = function(spec)
    local self = {}
    self.connect = function() spec.onreceive(WebSocketMessageType.OPEN, nil) end
    self.sendText = function()
      if not sendWorks() then error("WebSocket failed to send text", 0) end
    end
    self.close = function() end
    sockets[#sockets + 1] = self
    return self
  end
end

local function freshClient()
  sockets = {}
  return assert(loadfile("plugin/client.lua"))(nil)
end

-- 1. the very first ping hits a dead server
local alive = false
stubSocket(function() return alive end)
local client = freshClient()
local failed
local safe = pcall(function()
  client.ping(function() end, function(msg) failed = msg end)
end)
ok(safe, "a dead socket must not throw out of ping")
ok(failed ~= nil, "a dead socket must report offline")

-- 2. the socket opens fine, then the server goes away under it
alive = true
client = freshClient()
failed = nil
client.ping(function() end, function(msg) failed = msg end)
ok(failed == nil, "a live ping must not report failure")
alive = false
safe = pcall(function()
  client.ping(function() end, function(msg) failed = msg end)
end)
ok(safe, "a server that vanished must not throw out of ping")
ok(failed ~= nil, "a server that vanished must report offline")

-- 3. the same for a request, not just the health ping
alive = false
client = freshClient()
failed = nil
safe = pcall(function()
  client.request({ type = "generate" }, { onerror = function(msg) failed = msg end })
end)
ok(safe, "a dead socket must not throw out of request")
ok(failed ~= nil, "a dead request must report offline")

if failures > 0 then
  print(failures .. " failure(s)")
  os.exit(1)
end
print("test_client_offline ok")
