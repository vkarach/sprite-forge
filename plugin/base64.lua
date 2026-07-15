-- Pure-Lua base64 (RFC 4648), lookup-table based: the old bit-string
-- implementation took seconds on raw RGBA payloads.
local M = {}
local chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'

local enc = {}   -- 0..63 -> char
local dec = {}   -- char -> 0..63
for i = 1, 64 do
  enc[i - 1] = chars:sub(i, i)
  dec[chars:sub(i, i)] = i - 1
end

function M.encode(data)
  local out = {}
  local n = #data
  local full = n - n % 3
  for i = 1, full, 3 do
    local a, b, c = data:byte(i, i + 2)
    local v = a * 65536 + b * 256 + c
    out[#out + 1] = enc[v // 262144] .. enc[v // 4096 % 64]
                    .. enc[v // 64 % 64] .. enc[v % 64]
  end
  local rem = n % 3
  if rem == 1 then
    local a = data:byte(n)
    out[#out + 1] = enc[a // 4] .. enc[a % 4 * 16] .. '=='
  elseif rem == 2 then
    local a, b = data:byte(n - 1, n)
    out[#out + 1] = enc[a // 4] .. enc[a % 4 * 16 + b // 16]
                    .. enc[b % 16 * 4] .. '='
  end
  return table.concat(out)
end

function M.decode(data)
  data = data:gsub('[^%w%+%/%=]', '')
  local out = {}
  local n = #data
  while n > 0 and data:sub(n, n) == '=' do n = n - 1 end
  local full = n - n % 4
  for i = 1, full, 4 do
    local a, b, c, d = data:sub(i, i), data:sub(i + 1, i + 1),
                       data:sub(i + 2, i + 2), data:sub(i + 3, i + 3)
    local v = dec[a] * 262144 + dec[b] * 4096 + dec[c] * 64 + dec[d]
    out[#out + 1] = string.char(v // 65536, v // 256 % 256, v % 256)
  end
  local rem = n % 4
  if rem == 2 then
    local a, b = data:sub(full + 1, full + 1), data:sub(full + 2, full + 2)
    out[#out + 1] = string.char(dec[a] * 4 + dec[b] // 16)
  elseif rem == 3 then
    local a = data:sub(full + 1, full + 1)
    local b = data:sub(full + 2, full + 2)
    local c = data:sub(full + 3, full + 3)
    local v = dec[a] * 1024 + dec[b] * 16 + dec[c] // 4
    out[#out + 1] = string.char(v // 256, v % 256)
  end
  return table.concat(out)
end

return M
