"""JSON-over-WebSocket protocol: requests in, responses out, PNGs as base64."""
import base64
import io
import json
from dataclasses import dataclass, field

from PIL import Image

VALID_MODES = ("generate", "edit", "inpaint", "instruct")
VALID_BACKGROUNDS = ("auto", "remove", "keep")
MAX_SIDE = 4096      # a sprite side; well past pixel art, guards allocations
MAX_VARIANTS = 8     # matches the panel's slider


class ProtocolError(Exception):
    pass


@dataclass
class Frame:
    image: Image.Image | None = None
    mask: Image.Image | None = None


@dataclass
class Request:
    id: str
    mode: str
    prompt: str
    target_size: tuple[int, int]
    variants: int = 4
    symmetry: bool = False
    background: str = "auto"
    seed: int | None = None  # None = roll a fresh one per variant
    frames: list[Frame] = field(default_factory=list)


def image_to_b64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.convert("RGBA").save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def image_to_raw(img: Image.Image) -> dict:
    """RGBA pixel bytes, not PNG: the plugin turns this into an Image in
    memory (Image.bytes) - loading a PNG via a temp file spams Aseprite's
    Recent Files list."""
    rgba = img.convert("RGBA")
    return {"w": rgba.width, "h": rgba.height,
            "px": base64.b64encode(rgba.tobytes()).decode("ascii")}


def image_from_raw(d: dict) -> Image.Image:
    return Image.frombytes("RGBA", (int(d["w"]), int(d["h"])),
                           base64.b64decode(d["px"]))


def image_from_b64(s: str) -> Image.Image:
    try:
        return Image.open(io.BytesIO(base64.b64decode(s))).convert("RGBA")
    except Exception as e:
        raise ProtocolError(f"invalid image data: {e}") from e


def parse_request(text: str) -> Request:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ProtocolError(f"invalid JSON: {e}") from e

    try:
        req_id = str(data["id"])
        mode = str(data["mode"])
        prompt = str(data["prompt"])
        w, h = data["target_size"]
        target_size = (int(w), int(h))
    except (KeyError, TypeError, ValueError) as e:
        raise ProtocolError(f"missing/invalid field: {e}") from e

    if mode not in VALID_MODES:
        raise ProtocolError(f"unknown mode '{mode}'")

    # A cleared Width field sends 0, which used to divide by zero deep in
    # t2i_size; say so at the boundary instead.
    if not all(1 <= v <= MAX_SIDE for v in target_size):
        raise ProtocolError(
            f"target_size must be 1..{MAX_SIDE} per side, got "
            f"{target_size[0]}x{target_size[1]}")

    background = str(data.get("background", "auto"))
    if background not in VALID_BACKGROUNDS:
        raise ProtocolError(f"unknown background '{background}'")

    frames = []
    for f in data.get("frames", []):
        if not isinstance(f, dict):
            raise ProtocolError("frame entry must be an object")
        img = image_from_b64(f["image"]) if f.get("image") else None
        mask = image_from_b64(f["mask"]) if f.get("mask") else None
        frames.append(Frame(image=img, mask=mask))

    if mode in ("edit", "inpaint", "instruct") and (
            not frames or frames[0].image is None):
        raise ProtocolError(f"mode '{mode}' requires a frame image")
    if mode == "inpaint" and frames[0].mask is None:
        raise ProtocolError("inpaint requires a mask")

    seed = data.get("seed")
    if seed is not None:
        try:
            seed = int(seed)
        except (TypeError, ValueError) as e:
            raise ProtocolError(f"seed must be an integer: {e}") from e
        if not 0 <= seed < 2**32:
            raise ProtocolError(f"seed must be 0..2^32-1, got {seed}")

    return Request(
        id=req_id, mode=mode, prompt=prompt, target_size=target_size,
        # clamped, not rejected: an out-of-range slider is worth honouring
        # as "as many as I allow", but an unbounded count pins the GPU
        variants=max(1, min(MAX_VARIANTS, int(data.get("variants", 4)))),
        symmetry=bool(data.get("symmetry", False)),
        background=background,
        seed=seed,
        frames=frames,
    )


def progress_msg(req_id: str, value: float, stage: str | None = None) -> str:
    data = {"id": req_id, "type": "progress", "value": value}
    if stage is not None:
        data["stage"] = stage
    return json.dumps(data)


def result_msg(req_id: str, images: list[Image.Image],
               seeds: list[int] | None = None) -> str:
    data = {"id": req_id, "type": "result",
            "images": [image_to_raw(i) for i in images]}
    if seeds is not None:
        data["seeds"] = seeds  # one per variant, so a single one can be redone
    return json.dumps(data)


def error_msg(req_id: str, message: str) -> str:
    return json.dumps({"id": req_id, "type": "error", "message": message})
