"""Turn AI output into actual pixel art: downscale, palette, transparency."""
import numpy as np
from PIL import Image
from scipy import ndimage


def downscale(img: Image.Image, target_size: tuple[int, int],
              keep: float = 0.3,
              palette: list[tuple[int, int, int]] | None = None
              ) -> Image.Image:
    """Palette-majority downscale: each opaque pixel votes for its nearest
    palette color, the cell takes the winner. Unlike a median this never
    invents in-between colors, so outlines survive. A cell stays opaque
    when at least `keep` of its pixels are opaque."""
    tw, th = target_size
    arr = np.asarray(img.convert("RGBA"))
    h, w = arr.shape[:2]
    if palette is None:
        palette = subject_palette(img, 16)
    pal = np.asarray(palette, dtype=np.float32)

    flat = arr.reshape(-1, 4)
    rgb = flat[:, :3].astype(np.float32)
    dists = ((rgb ** 2).sum(1)[:, None] - 2.0 * (rgb @ pal.T)
             + (pal ** 2).sum(1)[None, :])
    nearest = dists.argmin(1)

    ci = np.minimum(np.arange(w) * tw // w, tw - 1)
    cj = np.minimum(np.arange(h) * th // h, th - 1)
    cell = (cj[:, None] * tw + ci[None, :]).ravel()
    opaque = flat[:, 3] > 0
    votes = np.zeros((tw * th, len(pal)), dtype=np.int32)
    np.add.at(votes, (cell[opaque], nearest[opaque]), 1)
    total = np.bincount(cell, minlength=tw * th)
    opq = votes.sum(1)

    out = np.zeros((tw * th, 4), dtype=np.uint8)
    solid = (opq > 0) & (opq >= keep * total)
    out[solid, :3] = pal[votes.argmax(1)[solid]].astype(np.uint8)
    out[solid, 3] = 255
    return Image.fromarray(out.reshape(th, tw, 4), "RGBA")


def extract_palette(img: Image.Image, max_colors: int = 16) -> list[tuple[int, int, int]]:
    """Median-cut palette of an AI-generated image."""
    q = img.convert("RGB").quantize(colors=max_colors)
    raw = q.getpalette()[: max_colors * 3]
    used = sorted(set(q.getdata()))
    return [tuple(raw[i * 3: i * 3 + 3]) for i in used]


def mirror_symmetry(img: Image.Image) -> Image.Image:
    """Mirror the left half onto the right (center column kept for odd
    widths). For front/back views this guarantees symmetric features -
    a standard pixel-art technique."""
    arr = np.asarray(img.convert("RGBA")).copy()
    h, w = arr.shape[:2]
    half = w // 2
    arr[:, w - half:] = arr[:, :half][:, ::-1]
    return Image.fromarray(arr, "RGBA")


def crop_to_subject(img: Image.Image, margin: float = 0.04) -> Image.Image:
    """Crop a background-removed image to its opaque bounding box (plus a
    small margin) so the subject, not the empty canvas, gets the pixels
    after downscaling."""
    arr = np.asarray(img.convert("RGBA"))
    ys, xs = np.nonzero(arr[:, :, 3])
    if len(xs) == 0:
        return img.convert("RGBA")
    pad = int(margin * max(img.width, img.height))
    x0 = max(int(xs.min()) - pad, 0)
    x1 = min(int(xs.max()) + 1 + pad, img.width)
    y0 = max(int(ys.min()) - pad, 0)
    y1 = min(int(ys.max()) + 1 + pad, img.height)
    return img.convert("RGBA").crop((x0, y0, x1, y1))


def fit_into(img: Image.Image, target_size: tuple[int, int],
             palette: list[tuple[int, int, int]] | None = None
             ) -> Image.Image:
    """Downscale preserving aspect ratio and center on a transparent canvas
    of target_size (pixel-art letterboxing)."""
    tw, th = target_size
    scale = min(tw / img.width, th / img.height)
    fw = max(1, round(img.width * scale))
    fh = max(1, round(img.height * scale))
    small = downscale(img, (fw, fh), palette=palette)
    canvas = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    canvas.paste(small, ((tw - fw) // 2, (th - fh) // 2))
    return canvas


def subject_palette(img: Image.Image, max_colors: int = 16) -> list[tuple[int, int, int]]:
    """Median-cut palette from OPAQUE pixels only. On background-removed
    images this spends every palette slot on the subject instead of wasting
    most of them on background shades."""
    arr = np.asarray(img.convert("RGBA"))
    opaque = arr[arr[:, :, 3] > 0][:, :3]
    if len(opaque) == 0:
        return [(0, 0, 0)]
    strip = Image.fromarray(opaque.reshape(1, -1, 3), "RGB")
    q = strip.quantize(colors=max_colors)
    raw = q.getpalette()[: max_colors * 3]
    used = sorted(set(q.getdata()))
    return [tuple(raw[i * 3: i * 3 + 3]) for i in used]


def sprite_palette(img: Image.Image, limit: int = 64) -> list[tuple[int, int, int]] | None:
    """Unique opaque colors of a hand-made sprite; None if not palette-like."""
    arr = np.asarray(img.convert("RGBA")).reshape(-1, 4)
    opaque = arr[arr[:, 3] > 0][:, :3]
    colors = np.unique(opaque, axis=0)
    if len(colors) == 0 or len(colors) > limit:
        return None
    return [tuple(int(v) for v in c) for c in colors]


def snap_to_palette(img: Image.Image, palette: list[tuple[int, int, int]]) -> Image.Image:
    """Snap every pixel's RGB to the nearest palette color; keep alpha."""
    arr = np.asarray(img.convert("RGBA")).astype(int)
    h, w = arr.shape[:2]
    flat = arr.reshape(-1, 4)
    pal = np.array(palette, dtype=int)
    dists = ((flat[:, None, :3] - pal[None, :, :]) ** 2).sum(axis=2)
    snapped = pal[dists.argmin(axis=1)]
    out = np.concatenate([snapped, flat[:, 3:4]], axis=1).astype(np.uint8)
    out[out[:, 3] == 0] = 0  # fully transparent pixels carry no stray color
    return Image.fromarray(out.reshape(h, w, 4), "RGBA")


def remove_background(img: Image.Image, tolerance: int = 12,
                      force: bool = False) -> Image.Image:
    """Flood-fill from border pixels matching the dominant border color;
    reached pixels become transparent, enclosed regions are kept. Skipped
    when under 60% of the border matches, unless `force` is set."""
    arr = np.asarray(img.convert("RGBA")).astype(int).copy()
    h, w = arr.shape[:2]
    border = np.concatenate([arr[0, :, :3], arr[-1, :, :3],
                             arr[:, 0, :3], arr[:, -1, :3]])
    # snap the median to a real border color (a 50/50 border would otherwise
    # yield a blend that matches nothing)
    med = np.median(border, axis=0)
    bg = border[np.abs(border - med).sum(axis=1).argmin()]
    matching = (np.abs(border - bg).max(axis=1) <= tolerance).mean()
    if not force and matching < 0.6:
        return img.convert("RGBA")  # no dominant background color detected

    bgmask = np.abs(arr[:, :, :3] - bg).max(axis=2) <= tolerance
    seed = np.zeros((h, w), dtype=bool)
    seed[0, :], seed[-1, :] = bgmask[0, :], bgmask[-1, :]
    seed[:, 0], seed[:, -1] = bgmask[:, 0], bgmask[:, -1]
    cross = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=bool)
    cleared = ndimage.binary_propagation(seed, mask=bgmask, structure=cross)
    arr[cleared, 3] = 0
    return Image.fromarray(arr.astype(np.uint8), "RGBA")
