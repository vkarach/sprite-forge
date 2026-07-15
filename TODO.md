# TODO

- Edit / Inpaint still run on SDXL: consider Klein image-to-image for
  detailed edit prompts once its editing quality at low strength is tested.
- 8-bit quantized Klein TRANSFORMER outputs pure noise in text-to-image
  (edits fine) — investigate or report upstream. Current setup avoids it:
  8-bit text encoder + bf16 transformer, fully resident.
