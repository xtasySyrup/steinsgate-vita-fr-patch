"""Translate backgrounds and add the splash image: writes build/assets/bg.cpk.

Usage: python -I tools/build_bg.py <project root> [ids...]
Reads    game/PCSE00644/gamedata/bg.cpk, tools/bg_labels.py, sources/splash.png if it exists
Writes   build/assets/bg.cpk and previews in build/report/bg/
With ids it only paints and previews those, without fitting them into the archive.
"""
import os, struct, sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cpk import layla
from sglib import itoc_rows, layla_compress
import bg_labels, ui_paint


def stored(raw, row):
    return raw[row["pos"]:row["pos"] + row["FileSize"]]


def splash_gxt(gxt, path):
    """The splash on black, its flat bottom edge on the screen's bottom edge, stored in the format of the slot."""
    sheet = ui_paint.Sheet(gxt)
    src = Image.open(path).convert("RGBA")
    line = bg_labels.SPLASH_LINE
    box = line["clear"]
    src.paste((0, 0, 0, 0), box)
    mask = Image.new("L", src.size, 0)
    font = ImageFont.truetype(os.path.join(ui_paint.FONT_DIR, line["font"]), line["size"])
    ImageDraw.Draw(mask).text(line["at"], line["text"], font=font, fill=255, anchor="ls")
    layer = Image.new("RGBA", src.size, (255, 255, 255, 0))
    layer.putalpha(mask)
    src.alpha_composite(layer)
    a = np.asarray(src)
    ys, xs = np.where(a[..., 3] > 10)
    W, H = bg_labels.SPLASH_SIZE
    scale = (H - 28) / (ys.max() + 1 - ys.min())
    crop = src.crop((0, int(ys.min()), src.width, int(ys.max()) + 1))
    size = (int(round(crop.width * scale)), H - 28)
    crop = crop.resize(size, Image.LANCZOS)
    canvas = Image.new("RGBA", (W, H), bg_labels.SPLASH_BACKGROUND)
    x = W // 2 - int(round((xs.min() + xs.max()) / 2 * scale))
    canvas.alpha_composite(crop, (x, 28))
    quant = canvas.convert("RGB").quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG)
    palette = (quant.getpalette() + [0] * 768)[:768]
    alpha = int(sheet.pal[:, 3].max())
    d = bytearray(gxt)
    n8 = struct.unpack_from("<I", gxt, 0x18)[0]
    at = len(gxt) - n8 * 1024
    for i in range(256):
        r, g, b = palette[i * 3:i * 3 + 3]
        d[at + i * 4:at + i * 4 + 4] = bytes((b, g, r, alpha))
    px = np.asarray(quant, dtype=np.uint8)
    d[sheet.off:sheet.off + sheet.size] = px.tobytes()
    assert sheet.stride == W and sheet.h == H
    return bytes(d)


def whiteboard(gxt, paper_rgb, fid):
    """Lift each English word back to bare paper, then write the French. Pixels not in a word keep their index."""
    sheet = ui_paint.Sheet(gxt)
    log = []
    for x0, y0, x1, y1, text, cap, limit, align, *rest in bg_labels.WHITEBOARD:
        opts = rest[0] if rest else {}
        # Read the sheet afresh: a word lifted just before must not count as touching this box's border.
        rgb = sheet.rgba((x0, y0, x1, y1))[:, :, :3]
        ink = np.abs(rgb - paper_rgb[y0:y1, x0:x1]).mean(axis=2) > 22
        if "inner" in opts:
            cx, cy, rx, ry = opts["inner"]
            yy, xx = np.mgrid[y0:y1, x0:x1]
            here = ink & (((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 < 1)
            mask = here
        else:
            here = ui_paint.inside_components(ink)
            mask = ui_paint._grow(here, 2)
        if here.sum() < 25:
            continue
        ys, xs = np.where(here)
        target = np.concatenate((paper_rgb[y0:y1, x0:x1], np.full((y1 - y0, x1 - x0, 1), 255, dtype=np.float32)), axis=2)
        new = sheet.nearest(target)
        view = sheet.px[y0:y1, x0:x1]
        view[mask] = new[mask]
        centre_x = x0 + (int(xs.min()) + int(xs.max())) // 2
        anchor = x0 + int(xs.min()) if align == "l" else centre_x
        middle = y0 + (int(ys.min()) + int(ys.max())) // 2
        log.append(ui_paint.text(sheet, anchor, middle + opts.get("lift", 0) + cap // 2, text, bg_labels.HAND, cap, align, limit, bg_labels.INK, stroke=0.45))
        for dy, line, line_cap, line_limit in opts.get("also", []):
            log.append(ui_paint.text(sheet, anchor, middle + dy + line_cap // 2, line, bg_labels.HAND, line_cap, align, line_limit, bg_labels.INK, stroke=0.45))
    return sheet, log


def news(gxt, fid):
    """Lift the old letters by their colours, fill the gaps from around them, and draw the French on top."""
    sheet = ui_paint.Sheet(gxt)
    log = []
    for part in bg_labels.NEWS[fid]:
        x0, y0, x1, y1 = box = part["box"]
        rgb = sheet.rgba(box)[:, :, :3]
        lum = rgb.mean(axis=2)
        spread = rgb.max(axis=2) - rgb.min(axis=2)
        mask = (lum > part["light"]) & (spread < 40)
        if part.get("dark") is not None:
            mask |= lum < part["dark"]
        if part.get("red"):
            mask |= rgb[:, :, 0] - rgb[:, :, 1] > 38  # red, and its pink soft edges
        if part.get("band"):
            yy, xx = np.mgrid[y0:y1, x0:x1]
            inside = np.zeros(mask.shape, dtype=bool)
            for ax, ay, bx, by in part["band"]:
                t = (xx - ax) / (bx - ax)
                inside |= (t > -0.02) & (t < 1.02) & (np.abs(yy - (ay + t * (by - ay))) < part["band_half"])
            mask &= inside
        ui_paint.inpaint(sheet, box, ui_paint._grow(mask, part["grow"]))
        for cx, cy, text, font, cap, angle, fill, outline, thick, limit in part["draw"]:
            log.append(ui_paint.rotated_text(sheet, cx, cy, text, font, cap, angle, fill, outline, thick, limit))
    return sheet, log


def work(job):
    fid, data, size, paper, root, splash, fit = job
    gxt = layla(data)
    log = []
    if fid == bg_labels.SPLASH_SLOT:
        out = splash_gxt(gxt, splash)
        ui_paint.Sheet(out).preview(f"{root}/build/report/bg/{fid:03d}.png")
    else:
        sheet, log = news(gxt, fid) if fid in bg_labels.NEWS else whiteboard(gxt, paper, fid)
        sheet.preview(f"{root}/build/report/bg/{fid:03d}.png")
        out = sheet.tobytes()
    if not fit:
        return fid, None, log, "painted"
    try:
        comp, used = layla_compress(out, size)
    except OverflowError as e:
        return fid, None, log, f"DOES NOT FIT: {e}"
    if layla(comp) != out or len(comp) != size:
        return fid, None, log, "round trip failed"
    return fid, comp, log, f"fits slot {size}, front gap {size - 272 - used}"


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ROOT = sys.argv[1]
    SPLASH = f"{ROOT}/sources/splash.png"
    only = [int(x) for x in sys.argv[2:]]
    raw = open(f"{ROOT}/game/PCSE00644/gamedata/bg.cpk", "rb").read()
    rows = {e["ID"]: e for e in itoc_rows(raw)}
    paper = ui_paint.Sheet(layla(stored(raw, rows[bg_labels.BLANK_PAPER]))).rgba()[:, :, :3]
    ids = only or [*bg_labels.WHITEBOARD_IDS, *bg_labels.NEWS, *([bg_labels.SPLASH_SLOT] if os.path.exists(SPLASH) else [])]
    jobs = [(i, stored(raw, rows[i]), rows[i]["FileSize"], paper, ROOT, SPLASH, not only) for i in ids]
    with Pool(min(len(jobs), max(2, (os.cpu_count() or 4) - 2))) as pool:
        results = pool.map(work, jobs, chunksize=1)
    out = bytearray(raw)
    failed = 0
    for fid, comp, log, status in results:
        print(f"id {fid}: {status}")
        for line in log:
            if "TIGHT" in line:
                print("   ", line)
        if comp:
            e = rows[fid]
            out[e["pos"]:e["pos"] + e["FileSize"]] = comp
        elif not only:
            failed += 1
    if only:
        raise SystemExit(0)
    if failed:
        raise SystemExit(f"{failed} images did not fit; nothing written")
    os.makedirs(f"{ROOT}/build/assets", exist_ok=True)
    open(f"{ROOT}/build/assets/bg.cpk", "wb").write(out)
    print("wrote build/assets/bg.cpk")
