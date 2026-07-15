# TODO

- **History button in the Aseprite panel**: browse past generations (the
  `output/` folders already store raw + final images and settings.json of
  every run) — a grid dialog with paging, click a variant to insert it as a
  layer, show the prompt/settings of each run.
- Edit / Inpaint still run on SDXL: consider Klein image-to-image for
  detailed edit prompts once its editing quality at low strength is tested.
- 8-bit quantized Klein transformer outputs pure noise in text-to-image
  (works for editing) — investigate or report upstream; t2i currently runs
  bf16 + CPU offload as a workaround.
