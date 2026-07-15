# TODO

- 8-bit quantized Klein TRANSFORMER outputs pure noise in text-to-image
  (edits fine) — investigate or report upstream. Current setup avoids it:
  8-bit text encoder + bf16 transformer, fully resident.
