-- Plain-Lua tests for prompt.lua: run with `lua plugin/tests/test_prompt.lua`
-- from the repo root. No Aseprite needed - that is the point of the module.
local P = dofile("plugin/prompt.lua")

local failures = 0
local function eq(got, want, what)
  if got ~= want then
    failures = failures + 1
    print(string.format("FAIL %s\n  got:  %s\n  want: %s",
                        what, tostring(got), tostring(want)))
  end
end

-- Generate: empty subject means nothing to send, whatever else is filled.
eq(P.assembleGenPrompt("3/4 view", "", ""), nil, "gen: empty subject")
eq(P.assembleGenPrompt("3/4 view", "", "extra"), nil, "gen: extra alone")

-- Custom sends the subject as-is; Extra is appended with a comma.
eq(P.assembleGenPrompt("Custom (text only)", "a sword", ""), "a sword",
   "gen: custom bare")
eq(P.assembleGenPrompt("Custom (text only)", "a sword", "glowing"),
   "a sword, glowing", "gen: custom + extra")

-- A template substitutes the subject and appends Extra with a space.
eq(P.assembleGenPrompt("Top-down", "a barrel", ""),
   "A a barrel seen directly from above, flat top-down game view.",
   "gen: template")
eq(P.assembleGenPrompt("Top-down", "a barrel", "wooden"),
   "A a barrel seen directly from above, flat top-down game view. wooden",
   "gen: template + extra")

-- An unknown view falls back to the no-template path, not to a crash.
eq(P.assembleGenPrompt("Nonexistent", "a barrel", ""), "a barrel",
   "gen: unknown view")

-- Instruct: no preset and no text means nothing to send.
eq(P.assembleInstruction("Custom (text only)", "horse", ""), nil,
   "instruct: custom without text")
eq(P.assembleInstruction("Custom (text only)", "", "turn it around"),
   "turn it around", "instruct: custom with text")

-- A preset without a subject falls back to "character" (documented default).
eq(P.assembleInstruction("Back view", "", ""),
   "Show the same character from behind, seen from the back",
   "instruct: subject default")
eq(P.assembleInstruction("Back view", "brown horse", ""),
   "Show the same brown horse from behind, seen from the back",
   "instruct: named subject")
eq(P.assembleInstruction("Back view", "brown horse", "keep the saddle"),
   "Show the same brown horse from behind, seen from the back,"
   .. " keep the saddle", "instruct: extra appended with a comma")

-- Every ordered view must have a template, or the combobox offers a dead entry.
for _, v in ipairs(P.GEN_VIEW_ORDER) do
  eq(type(P.GEN_TEMPLATES[v]), "string", "gen order has template: " .. v)
end
for _, v in ipairs(P.PRESET_ORDER) do
  eq(type(P.PRESETS[v]), "string", "preset order has template: " .. v)
end

-- Panel labels must map to protocol modes the server accepts.
for _, label in ipairs({ "Generate", "Edit with AI", "Inpaint Selection",
                         "Rotate / Instruct" }) do
  eq(type(P.MODE_KEY[label]), "string", "mode key: " .. label)
end
for _, label in ipairs({ "Auto", "Remove", "Keep" }) do
  eq(type(P.BG_KEY[label]), "string", "background key: " .. label)
end

if failures == 0 then
  print("prompt.lua: all tests passed")
else
  print(failures .. " failure(s)")
  os.exit(1)
end
