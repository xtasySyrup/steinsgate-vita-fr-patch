"""Paint French labels into the paletted textures of system.cpk.

A texture must go back into its exact stored slot, and slots have under 1% to spare. So only pixels that really
change get a new palette index: re-quantising the rest adds entropy and overflows the slot (measured).
"""
import os, struct

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT_DIR = r"C:\Windows\Fonts"


class Sheet:
    """A P8 linear GXT texture: palette as RGBA, pixels as indices, editable in place."""

    def __init__(self, gxt):
        self.gxt = bytearray(gxt)
        n4, n8 = struct.unpack_from("<II", gxt, 0x14)
        self.off, self.size, _, _, ttype, fmt, self.w, self.h = struct.unpack_from("<IIiIIIHH", gxt, 0x20)
        if fmt != 0x95001000 or ttype != 0x60000000:
            raise ValueError(f"unsupported texture {ttype:08x}/{fmt:08x}")
        self.stride = self.size // self.h
        pal = np.frombuffer(bytes(gxt[len(gxt) - n8 * 1024:len(gxt) - (n8 - 1) * 1024]), dtype=np.uint8).reshape(256, 4)
        self.pal = pal[:, [2, 1, 0, 3]].astype(np.int32)  # stored BGRA
        self.px = np.frombuffer(bytes(gxt[self.off:self.off + self.size]), dtype=np.uint8).reshape(self.h, self.stride).copy()

    def rgba(self, box=None):
        px = self.px if box is None else self.px[box[1]:box[3], box[0]:box[2]]
        return self.pal[px].astype(np.float32)

    def nearest(self, rgba):
        """Closest palette entry. Alpha counts for more than colour: a wrong alpha shows as a hole or a box."""
        flat = rgba.reshape(-1, 4).round().astype(np.int32)
        uniq, inv = np.unique(flat, axis=0, return_inverse=True)
        out = np.empty(len(uniq), dtype=np.uint8)
        weight = np.array([1, 1, 1, 4], dtype=np.int64)
        for s in range(0, len(uniq), 2048):
            d = (((self.pal[None, :, :] - uniq[s:s + 2048, None, :]) ** 2) * weight).sum(axis=2)
            out[s:s + 2048] = d.argmin(axis=1)
        return out[inv.reshape(-1)].reshape(rgba.shape[:2])

    def tobytes(self):
        d = bytearray(self.gxt)
        d[self.off:self.off + self.size] = self.px.tobytes()
        return bytes(d)

    def preview(self, path, background=(70, 40, 90)):
        im = Image.fromarray(self.pal[self.px].astype(np.uint8), "RGBA")
        bg = Image.new("RGBA", im.size, background + (255,))
        bg.alpha_composite(im)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        bg.convert("RGB").crop((0, 0, self.w, self.h)).save(path)


def _render(text, font, cap, hscale_limit, tracking=0, stroke=0.0):
    """Text coverage as floats, sized so a capital is `cap` pixels tall; squeezed sideways only if `hscale_limit` asks."""
    scale = 6
    path = os.path.join(FONT_DIR, font)
    probe = ImageFont.truetype(path, 200)
    box = probe.getbbox("H")
    size = max(4, int(round(cap * scale * 200 / (box[3] - box[1]))))
    f = ImageFont.truetype(path, size)
    if tracking:
        widths = [f.getlength(c) + tracking * scale for c in text]
        total = int(sum(widths)) + 8 * scale
    else:
        total = int(f.getlength(text)) + 8 * scale
    bb = f.getbbox("Hgjpqy" + text + "ÉÈÀÊ")
    im = Image.new("L", (total, bb[3] - bb[1] + 4 * scale), 0)
    dr = ImageDraw.Draw(im)
    if tracking:
        x = 4 * scale
        for c, w in zip(text, widths):
            dr.text((x, 2 * scale - bb[1]), c, font=f, fill=255)
            x += w
    else:
        dr.text((4 * scale, 2 * scale - bb[1]), text, font=f, fill=255, stroke_width=int(round(stroke * scale)), stroke_fill=255)
    ink = im.getbbox()
    baseline = 2 * scale - bb[1] + box[3] * size / 200 - ink[1]  # capital bottom, measured from the ink top
    im = im.crop(ink)
    w = im.width / scale
    squeezed = 1.0
    if hscale_limit and w > hscale_limit:
        squeezed = hscale_limit / w
        w = hscale_limit
    h = im.height / scale
    out = im.resize((max(1, int(round(w))), max(1, int(round(h)))), Image.LANCZOS)
    return np.asarray(out, dtype=np.float32) / 255, baseline / scale, squeezed


def _grow(mask, n):
    for _ in range(n):
        g = mask.copy()
        g[1:, :] |= mask[:-1, :]
        g[:-1, :] |= mask[1:, :]
        g[:, 1:] |= mask[:, :-1]
        g[:, :-1] |= mask[:, 1:]
        mask = g
    return mask


def label(sheet, box, string, font="arial.ttf", cap=None, align="l", t=45, halo=2, limit=None, color=None, shadow=None, tracking=0, dy=0, erase_only=False, opacity=1.0, ax=None):
    """Replace the word inside `box`. `box` must contain that word with clear background at both sides; the word's exact bounds are measured.

    t: contrast that makes a pixel count as text. halo: pixels around the text also cleaned.
    limit: width the French may take (default: from the anchor to the box edge). Returns a report line.
    """
    x0, y0, x1, y1 = box
    rgba = sheet.rgba(box)
    # Background per row, taken from the box's side margins (always clear of the word), so vertical gradients survive.
    margin = np.concatenate((rgba[:, :3], rgba[:, -3:]), axis=1)
    med = np.median(margin, axis=1, keepdims=True)
    diff = np.abs(rgba[:, :, :3] - med[:, :, :3]).mean(axis=2) * (np.maximum(rgba[:, :, 3], med[:, :, 3]) / 255) + np.abs(rgba[:, :, 3] - med[:, :, 3])
    ink = diff > t
    if not ink.any():
        raise ValueError(f"no text found in {box} for {string!r}")
    ys, xs = np.where(ink)
    tx0, tx1, ty0, ty1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    if color is None:
        strongest = diff >= np.percentile(diff[ink], 70)
        color = np.median(rgba[strongest][:, :3], axis=0)
    # Clean: only the old word and its halo. Everything else keeps its exact index.
    clean = _grow(ink, halo)
    fill = np.repeat(med, rgba.shape[1], axis=1)
    new = sheet.nearest(fill)
    view = sheet.px[y0:y1, x0:x1]
    view[clean] = new[clean]
    note = f"{x0 + tx0},{y0 + ty0} {tx1 - tx0}x{ty1 - ty0}"
    if erase_only:
        return note
    target = cap if cap else ty1 - ty0
    baseline = y0 + (ty0 + target if cap else ty1) + dy
    room = limit if limit else {"l": x1 - x0 - tx0, "r": tx1, "c": x1 - x0}[align]
    anchor = ax if ax is not None else {"l": x0 + tx0, "r": x0 + tx1, "c": x0 + (tx0 + tx1) // 2}[align]
    return note + " " + text(sheet, anchor, baseline, string, font, target, align, room, tuple(float(c) for c in color), shadow, opacity, tracking)


def text(sheet, x, y, string, font="arial.ttf", cap=14, align="l", limit=None, color=(255, 255, 255), shadow=None, opacity=1.0, tracking=0, rough=0.0, stroke=0.0):
    """Draw with no measuring: (x, y) is the left, right or centre end of the baseline, depending on `align`."""
    a, base, squeezed = _render(string, font, cap, limit, tracking, stroke)
    h, w = a.shape
    ox = {"l": x, "r": x - w, "c": x - w // 2}[align]
    oy = int(round(y - base))
    pad = shadow[1] + 1 if shadow else 0
    x0, y0 = max(0, ox - pad), max(0, oy - pad)
    x1, y1 = min(sheet.stride, ox + w + pad), min(sheet.h, oy + h + pad)
    cover = np.zeros((y1 - y0, x1 - x0), dtype=np.float32)
    sx, sy = x0 - (ox - pad) - pad if ox - pad < 0 else 0, y0 - (oy - pad) - pad if oy - pad < 0 else 0
    tx, ty = max(0, ox - x0), max(0, oy - y0)
    ch, cw = min(h - sy, cover.shape[0] - ty), min(w - sx, cover.shape[1] - tx)
    cover[ty:ty + ch, tx:tx + cw] = a[sy:sy + ch, sx:sx + cw] * opacity
    if rough:  # stamped look: fixed seed, so the build stays reproducible
        grain = np.random.default_rng(len(string) * 7919 + x).random(cover.shape, dtype=np.float32)
        cover *= grain > rough
    out = sheet.rgba((x0, y0, x1, y1))
    touched = cover > 0.02
    if shadow:
        s = cover.copy()
        for _ in range(shadow[1]):
            g = s.copy()
            g[1:, :] = np.maximum(g[1:, :], s[:-1, :])
            g[:-1, :] = np.maximum(g[:-1, :], s[1:, :])
            g[:, 1:] = np.maximum(g[:, 1:], s[:, :-1])
            g[:, :-1] = np.maximum(g[:, :-1], s[:, 1:])
            s = g
        out = _over(out, np.array(shadow[0], dtype=np.float32), s)
        touched |= s > 0.02
    out = _over(out, np.array(color, dtype=np.float32), cover)
    view = sheet.px[y0:y1, x0:x1]
    view[touched] = sheet.nearest(out)[touched]
    return f"{string!r} squeezed {squeezed:.2f}" + (" TIGHT" if squeezed < 0.72 else "")


def wipe(sheet, box, t=10, halo=1):
    """Flatten a large faint word into its surroundings: everything in `box` that stands out from the row margins."""
    x0, y0, x1, y1 = box
    rgba = sheet.rgba(box)
    margin = np.concatenate((rgba[:, :3], rgba[:, -3:]), axis=1)
    med = np.median(margin, axis=1, keepdims=True)
    # Blend the two margins across the box, so a sideways gradient survives as well.
    left, right = _smooth(np.median(rgba[:, :3], axis=1, keepdims=True)), _smooth(np.median(rgba[:, -3:], axis=1, keepdims=True))
    ramp = np.linspace(0, 1, rgba.shape[1], dtype=np.float32)[None, :, None]
    fill = left * (1 - ramp) + right * ramp
    diff = np.abs(rgba[:, :, :3] - fill[:, :, :3]).mean(axis=2)
    ink = _grow(diff > t, halo)
    new = sheet.nearest(fill)
    view = sheet.px[y0:y1, x0:x1]
    view[ink] = new[ink]


def _smooth(column, radius=4):
    """Average along the rows of a per-row colour, so a wiped area shows no horizontal streaks."""
    h = column.shape[0]
    out = column.copy()
    for y in range(h):
        out[y] = column[max(0, y - radius):y + radius + 1].mean(axis=0)
    return out


def ghost(sheet, box, x, y, string, font="arialbd.ttf", cap=40, t=9, align="l", limit=None, opacity=0.85, rough=0.0, halo=1):
    """Wipe a large faint word and redraw it in the colour the old word had (each skin has its own)."""
    rgba = sheet.rgba(box)
    margin = np.concatenate((rgba[:, :3], rgba[:, -3:]), axis=1)
    med = np.median(margin, axis=1, keepdims=True)
    diff = np.abs(rgba[:, :, :3] - med[:, :, :3]).mean(axis=2)
    color = np.median(rgba[diff >= np.percentile(diff, 95)][:, :3], axis=0)
    wipe(sheet, box, t=t, halo=halo)
    return text(sheet, x, y, string, font, cap, align, limit, tuple(float(c) for c in color), None, opacity, 0, rough)


def inside_components(mask):
    """The parts of `mask` that do not reach its border: words in a box, but not the bubble lines crossing it."""
    h, w = mask.shape
    keep = mask.copy()
    stack = [(y, x) for y in range(h) for x in (0, w - 1) if mask[y, x]] + [(y, x) for x in range(w) for y in (0, h - 1) if mask[y, x]]
    while stack:
        y, x = stack.pop()
        if not keep[y, x]:
            continue
        keep[y, x] = False
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and keep[ny, nx]:
                    stack.append((ny, nx))
    return keep


def inpaint(sheet, box, mask, iterations=90):
    """Fill masked pixels by diffusing their surroundings inward. Only those pixels change."""
    x0, y0, x1, y1 = box
    rgba = sheet.rgba(box)
    grid = rgba.copy()
    known = ~mask
    grid[mask] = grid[known].mean(axis=0)
    for _ in range(iterations):
        p = np.pad(grid, ((1, 1), (1, 1), (0, 0)), mode="edge")
        avg = (p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:]) / 4
        grid[mask] = avg[mask]
    new = sheet.nearest(grid)
    view = sheet.px[y0:y1, x0:x1]
    view[mask] = new[mask]


def rotated_text(sheet, cx, cy, string, font, cap, angle, fill, outline, thickness, limit=None):
    """Outlined text, centred on (cx, cy), turned by `angle` degrees (positive is counter-clockwise)."""
    scale = 4
    path = os.path.join(FONT_DIR, font)
    probe = ImageFont.truetype(path, 200)
    box = probe.getbbox("H")
    f = ImageFont.truetype(path, max(4, int(round(cap * scale * 200 / (box[3] - box[1])))))
    bb = f.getbbox(string, stroke_width=int(thickness * scale))
    layer = Image.new("RGBA", (bb[2] - bb[0] + 8 * scale, bb[3] - bb[1] + 8 * scale), tuple(outline) + (0,))
    ImageDraw.Draw(layer).text((4 * scale - bb[0], 4 * scale - bb[1]), string, font=f, fill=tuple(fill) + (255,), stroke_width=int(thickness * scale), stroke_fill=tuple(outline) + (255,))
    w = layer.width
    squeezed = 1.0
    if limit and w / scale > limit:
        squeezed = limit * scale / w
        w = int(limit * scale)
    layer = layer.resize((w, layer.height), Image.LANCZOS).rotate(angle, resample=Image.BICUBIC, expand=True)
    layer = layer.resize((layer.width // scale, layer.height // scale), Image.LANCZOS)
    x0, y0 = cx - layer.width // 2, cy - layer.height // 2
    src = np.asarray(layer, dtype=np.float32)
    x1, y1 = x0 + layer.width, y0 + layer.height
    a0, b0 = max(0, -y0), max(0, -x0)
    y0c, x0c, y1c, x1c = max(0, y0), max(0, x0), min(sheet.h, y1), min(sheet.w, x1)
    src = src[a0:a0 + y1c - y0c, b0:b0 + x1c - x0c]
    alpha = src[:, :, 3:] / 255
    dst = sheet.rgba((x0c, y0c, x1c, y1c))
    out = dst.copy()
    out[:, :, :3] = dst[:, :, :3] * (1 - alpha) + src[:, :, :3] * alpha
    touched = alpha[:, :, 0] > 0.02
    view = sheet.px[y0c:y1c, x0c:x1c]
    view[touched] = sheet.nearest(out)[touched]
    return f"{string!r} squeezed {squeezed:.2f}" + (" TIGHT" if squeezed < 0.72 else "")


def _over(dst, color, cover):
    """Source-over onto RGBA floats, keeping colour correct where the destination is transparent."""
    a_src = cover
    a_dst = dst[:, :, 3] / 255
    a_out = a_src + a_dst * (1 - a_src)
    safe = np.maximum(a_out, 1e-4)
    res = dst.copy()
    for c in range(3):
        res[:, :, c] = (color[c] * a_src + dst[:, :, c] * a_dst * (1 - a_src)) / safe
    res[:, :, 3] = a_out * 255
    return res


def blank(sheet, box):
    """Make an unused region fully transparent, which also frees bytes in the slot."""
    x0, y0, x1, y1 = box
    idx = np.where(sheet.pal[:, 3] == 0)[0]
    sheet.px[y0:y1, x0:x1] = idx[0]
