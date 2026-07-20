-- Results window: fixed-size grid of fresh variants, click to insert/remove.
local pluginDir = ...
local ui = dofile(app.fs.joinPath(pluginDir, "ui.lua"))
local sprite = assert(loadfile(
  app.fs.joinPath(pluginDir, "sprite.lua")))(pluginDir)

local R = {}

function R.showResults(imgs, seeds, onInserted)
  local g = ui.gridLayout(imgs, 600, 440)
  local W, H = g.cols * g.cw, g.rows * g.ch
  local inserted = {}  -- variant index -> {sprite, layer}, toggled by clicks

  local dlg = Dialog("SpriteForge - Results (click to insert / remove)")
  dlg:canvas{
    id = "grid", width = W, height = H,
    onpaint = function(ev)
      local gc = ev.context
      gc.color = ui.face()
      gc:fillRect(Rectangle(0, 0, W, H))
      ui.drawVariants(gc, imgs, g, inserted)
    end,
    onmouseup = function(ev)
      local n = ui.variantAt(ev, g, imgs)
      if not n then return end
      local added = sprite.toggleVariant(inserted, n, imgs[n], "SpriteForge ")
      if onInserted then onInserted(n, added) end
      -- entry, not label: its width is fixed, so setting the text never
      -- relayouts the window (a label would resize it and leave a ghost)
      dlg:modify{ id = "seed", text = ui.seedText(seeds, n) }
      dlg:repaint()
    end,
  }
  -- read the number here, select it and Ctrl+C; Aseprite has no text clipboard
  dlg:entry{ id = "seed", label = "Seed (click a variant):",
             text = ui.seedText(seeds, nil) }
  dlg:button{ text = "Close" }
  dlg:show{ wait = true }  -- opened from a WS callback, no nested modal loop
  app.refresh()
end

return R
