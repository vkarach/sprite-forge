# SpriteForge

Local AI pixel-art assistant for Aseprite: generate sprites from text,
edit existing sprites with a prompt, or redraw a selected region.
Runs entirely on your own GPU — no subscriptions.

## Requirements

- Windows, NVIDIA GPU with 12+ GB VRAM (built on an RTX 5080)
- Python 3.11+
- Aseprite 1.3+

## Setup

1. `py -3 -m venv .venv`
2. `.venv\Scripts\python -m pip install -r server\requirements.txt`
3. `.venv\Scripts\python -m pip install torch --index-url https://download.pytorch.org/whl/cu128`
4. `install-plugin.bat` (then restart Aseprite)

Every task runs on one model (FLUX.2 Klein, ~15 GB downloaded on first
use), so there are no model swaps: after the first load all tasks
respond in seconds.

## Use

1. Run `start-server.bat` (keep the window open; minimize it). Stop it
   with Ctrl+C; cmd may ask "Terminate batch job (Y/N)?" — answer y.
2. In Aseprite: **Sprite → SpriteForge → Open SpriteForge**. One panel:
   pick the task (Generate / Edit with AI / Inpaint Selection /
   Rotate + Instruct), fill the fields, press Run. Results open in a
   separate window; click a variant to insert it as a new layer. Your
   pixels are never modified.
3. Generate runs on FLUX.2 Klein, which understands full sentences: pick a
   **View** preset, name the **Subject** ("closed book with dark brown
   leather cover"), add **Extra** details if needed — the panel shows the
   exact text it will send. "Custom (text only)" sends your subject text
   as-is.
4. Edit with AI takes instructions, not strength: say what to change and
   how much ("make the sword glow slightly blue", "repaint the roof in
   red tiles") — the sprite's style and everything you didn't mention
   stay put. Inpaint works the same but only ever touches the selected
   region.
5. The **Background** option controls transparency: Auto detects and strips
   a uniform background, Remove strips the dominant border color even when
   detection is unsure, Keep leaves the image fully opaque.
6. **History** opens past generations (stored in `output/`), newest first:
   a scrollable list (or a 3-column grid — toggle at the bottom); click a
   run to see its variants, click a variant to insert it as a layer.
7. Rotate / Instruct tips: name the subject explicitly (e.g.
   "four-legged brown horse" — a generic "character" mutates it), use the
   Extra field for refinements, and enable Mirror symmetry for front/back
   views.

## Tuning without Aseprite

`.venv\Scripts\python -m server.tests.smoke "demonic sword" --size 64`
writes raw + postprocessed variants into `output/`.

## Tests

Server: `.venv\Scripts\python -m pytest server/tests/ --ignore=server/tests/smoke.py`

Plugin (needs `scoop install lua luacheck`, both user-scoped):

```
luacheck plugin\*.lua plugin\tests\*.lua
lua plugin\tests\test_prompt.lua
lua plugin\tests\test_panel.lua
```

`luacheck` bundles Lua 5.4, the version Aseprite runs, and `.luacheckrc`
declares the API globals it injects. `test_panel.lua` loads every module
against a stubbed Aseprite API and repaints the status canvas in each
server state, which catches broken cross-module calls without launching
the editor. Anything about layout or ghosting still needs a real Aseprite.

## Plugin layout

| file | holds |
|---|---|
| `main.lua` | entry point, registers the menu command |
| `dialogs.lua` | the control panel |
| `results.lua` | results window (fresh variants) |
| `history.lua` | history list and single-run windows |
| `ui.lua` | theme colors, checkerboard, variant grid, prompt preview |
| `sprite.lua` | frame/mask export, inserting variants as layers |
| `prompt.lua` | prompt assembly and key maps (pure Lua, unit-tested) |
| `client.lua` | WebSocket client |
| `base64.lua` | base64 codec |
