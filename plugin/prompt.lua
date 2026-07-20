-- Prompt assembly and the mode/background key maps. No Aseprite API here:
-- this module is plain Lua so it can be tested outside the editor.
local P = {}

P.BG_KEY = { ["Auto"] = "auto", ["Remove"] = "remove", ["Keep"] = "keep" }

P.MODE_KEY = { ["Generate"] = "generate",
               ["Edit with AI"] = "edit",
               ["Inpaint Selection"] = "inpaint",
               ["Rotate / Instruct"] = "instruct" }

-- %s = the subject; smoke-tested: naming the subject explicitly is CRITICAL
-- (a generic "character" mutates it).
P.PRESETS = {
  ["Side view (right)"] = "Show the same %s from the side, facing right",
  ["Side view (left)"]  = "Show the same %s from the side, facing left",
  ["Back view"]         = "Show the same %s from behind, seen from the back",
  ["Front view"]        = "Show the same %s from the front, seen head-on",
  ["3/4 view"]          = "Show the same %s from a three-quarter view",
  ["Custom (text only)"] = "",
}
P.PRESET_ORDER = { "Side view (right)", "Side view (left)", "Back view",
                   "Front view", "3/4 view", "Custom (text only)" }

-- Klein reads full prose: templates spell out the camera angle explicitly
-- (a bare "side view" tag is not enough).
P.GEN_TEMPLATES = {
  ["Side view"] = "A %s, seen exactly from the side at eye level, in strict"
    .. " profile view: only its side silhouette is visible, the front face"
    .. " cannot be seen at all. A flat 2D side-scroller game object. The"
    .. " camera does not look down at it.",
  ["Front view"] = "A %s, seen straight from the front at eye level,"
    .. " head-on, perfectly centered.",
  ["3/4 view"] = "A %s in classic three-quarter view game perspective, seen"
    .. " from slightly above.",
  ["Top-down"] = "A %s seen directly from above, flat top-down game view.",
  ["Custom (text only)"] = "",
}
P.GEN_VIEW_ORDER = { "3/4 view", "Side view", "Front view", "Top-down",
                     "Custom (text only)" }

-- Exactly the text that will be sent; nil when there is nothing to send.
function P.assembleGenPrompt(view, subject, extra)
  local tpl = P.GEN_TEMPLATES[view] or ""
  if subject == "" then return nil end
  if tpl == "" then
    return extra ~= "" and (subject .. ", " .. extra) or subject
  end
  local text = string.format(tpl, subject)
  if extra ~= "" then text = text .. " " .. extra end
  return text
end

function P.assembleInstruction(viewPreset, subject, extra)
  local tpl = P.PRESETS[viewPreset] or ""
  if tpl == "" then
    return extra ~= "" and extra or nil
  end
  local text = string.format(tpl, (subject ~= "" and subject) or "character")
  if extra ~= "" then text = text .. ", " .. extra end
  return text
end

return P
