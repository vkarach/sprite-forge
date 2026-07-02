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

First generation downloads ~7 GB of model weights into `models/`.

## Use

1. Run `start-server.bat` (keep the window open; minimize it). Stop it
   with Ctrl+C; cmd may ask "Terminate batch job (Y/N)?" — answer y.
2. In Aseprite: **Sprite → SpriteForge → Open SpriteForge**. One panel:
   pick the task (Generate / Edit with AI / Inpaint Selection), type the
   prompt, press Run. Variants appear in the same panel; click one to
   insert it as a new layer. Your pixels are never modified.

## Tuning without Aseprite

`.venv\Scripts\python -m server.tests.smoke "demonic sword" --size 64`
writes raw + postprocessed variants into `output/`.

## Tests

`.venv\Scripts\python -m pytest server/tests/ --ignore=server/tests/smoke.py`
