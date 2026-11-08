"""Burn French subtitles into the game's videos and append them to movie.cpk.

Usage: python -I tools/build_video.py <project root> [video names...]
Reads    game/PCSE00644/gamedata/movie.cpk, tools/video_cues.py
Writes   build/assets/movie.cpk, build/assets/video/<name>.USM, sample frames in build/report/video/

How a line is replaced:
1. Every frame of the line's cue is kept. A pixel that stays part of a thin bright stroke for 20 frames in a row is
   part of the English glyphs. This holds over moving backgrounds, and scrolling credits never last that long.
2. In each frame only those glyph pixels are repaired, from the clean pixels above and below them.
3. How far the English is revealed, and how bright it is, is read from the same mask and drives the French.

Encoder limits come from the game's own streams (High@3.1, CABAC, no B frames, closed IDR every 30 frames,
3608 kbit/s peak, 752 kbit buffer). This setup played on the Vita in the feasibility test.
"""
import os, shutil, subprocess, sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cpk, cpk_write, usm, video_cues

W, H = 960, 544
FS = W * H * 3 // 2
FONT_DIR = r"C:\Windows\Fonts"
SCALE = 4
MAX_WIDTH = 930
MARGIN = 15
PAD = 9  # the English glow reaches past the rows given for the line
STREAK = 20  # frames in a row that make a stroke part of the text


def decoder(h264):
    return subprocess.Popen(["ffmpeg", "-hide_banner", "-v", "error", "-f", "h264", "-framerate", "29.97", "-i", h264, "-f", "rawvideo", "-pix_fmt", "yuv420p", "-"], stdout=subprocess.PIPE)


def encoder(path):
    return subprocess.Popen(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", f"{W}x{H}", "-framerate", "29.97", "-i", "-",
                             "-c:v", "libx264", "-preset", "slow", "-profile:v", "high", "-level", "3.1", "-crf", "20", "-maxrate", "3608k", "-bufsize", "752k", "-vf", "setsar=1",
                             "-x264-params", "aud=1:nal-hrd=vbr:force-cfr=1:ref=2:bframes=0:weightp=1:scenecut=0:open-gop=0:keyint=30:min-keyint=30:annexb=1", "-f", "h264", path], stdin=subprocess.PIPE)


def _slide(a, radius, fn):
    out = a.copy()
    for d in range(1, radius + 1):
        out[d:, :] = fn(out[d:, :], a[:-d, :])
        out[:-d, :] = fn(out[:-d, :], a[d:, :])
    b = out.copy()
    for d in range(1, radius + 1):
        out[:, d:] = fn(out[:, d:], b[:, :-d])
        out[:, :-d] = fn(out[:, :-d], b[:, d:])
    return out


def tophat(a, radius=4):
    """Thin bright strokes: the image minus its opening. Broad bright areas, like clouds, come out near zero."""
    return a - _slide(_slide(a, radius, np.minimum), radius, np.maximum)


def grow(m, n):
    return _slide(m, n, np.logical_or) if n else m


def render(text, style):
    """The line's coverage and soft shadow on a full-width canvas, plus its baseline and ink width."""
    f0 = ImageFont.truetype(os.path.join(FONT_DIR, style["font"]), 200)
    b = f0.getbbox("H")
    size = int(round(style["cap"] * SCALE * 200 / (b[3] - b[1])))
    f = ImageFont.truetype(os.path.join(FONT_DIR, style["font"]), size)
    w = int(f.getlength(text)) + 8 * SCALE
    asc, desc = f.getmetrics()
    im = Image.new("L", (w, asc + desc + 8 * SCALE), 0)
    ImageDraw.Draw(im).text((4 * SCALE, 4 * SCALE), text, font=f, fill=255)
    target = min(int(w / SCALE * style["hscale"]), MAX_WIDTH)
    return im.resize((target, im.height // SCALE), Image.LANCZOS), (4 * SCALE + asc) // SCALE


def lay_out(line, style):
    """Place the French against the English: centred, or anchored to the side the English is anchored to."""
    im, baseline = render(line["text"], style)
    w = im.width
    align = line["align"]
    x = {"c": (W - w) // 2, "l": line["x0"] - 4, "r": line["x1"] - w + 4, "m": (line["x0"] + line["x1"] - w) // 2}[align]
    x = max(MARGIN, min(x, W - MARGIN - w))
    pad = int(style["shadow"]) + 4
    canvas = Image.new("L", (W, im.height + 2 * pad), 0)
    canvas.paste(im, (x, pad))
    blur = canvas.filter(ImageFilter.GaussianBlur(style["shadow"]))
    line["cover"] = np.asarray(canvas, dtype=np.float32) / 255
    line["soft"] = np.minimum(1.0, np.asarray(blur, dtype=np.float32) / 255 * style["shadow_gain"])
    line["baseline"] = baseline + pad
    line["ox"], line["w"] = x, w


def load_lines(h264, cues, end):
    """Collect each line's strip across its cue. Cue windows must end before the next line takes the same place."""
    lines = []
    for ci, (start, rows) in enumerate(cues):
        stop = cues[ci + 1][0] if ci + 1 < len(cues) else end
        for row in rows:
            t, b, text = row[:3]
            o = row[3] if len(row) > 3 else {}
            first, last = o.get("win", (start, stop))
            lines.append(dict(start=first, stop=last, top=t, bottom=b, text=text, align=o.get("align", "c"), xlim=o.get("xlim", (0, W)), slide=o.get("slide", False), y0=max(0, t - PAD), y1=min(H, b + PAD), strips=[]))
    dec = decoder(h264)
    n = 0
    while True:
        buf = dec.stdout.read(FS)
        if len(buf) < FS:
            break
        y = np.frombuffer(buf, dtype=np.uint8, count=W * H).reshape(H, W)
        for ln in lines:
            if ln["start"] <= n < ln["stop"]:
                ln["strips"].append(y[ln["y0"]:ln["y1"]].copy())
        n += 1
    dec.wait()
    return lines, n


def steady(stack, streak):
    """For each pixel, the brightest value it held for `streak` frames in a row."""
    m = stack.copy()
    done = 1
    while done < streak:
        step = min(done, streak - done)
        m[:-step] = np.minimum(m[:-step], m[step:])
        done += step
    return m[:max(1, len(m) - streak + 1)].max(axis=0)


def analyse(line, threshold, grow_by, streak):
    """Find the English glyphs, then follow them frame by frame."""
    stack = np.stack(line["strips"])
    hat = tophat(steady(stack, streak).astype(np.float32))
    core = hat > threshold
    core[:line["top"] - line["y0"]] = False
    core[line["bottom"] - line["y0"]:] = False
    core[:, :line["xlim"][0]] = False
    core[:, line["xlim"][1]:] = False
    if core.sum() < 20:
        raise ValueError(f"no English glyphs found for {line['text']!r} in frames {line['start']}-{line['stop']}")
    xs = np.where(core.any(axis=0))[0]
    line["x0"], line["x1"] = int(xs.min()), int(xs.max())
    line["mask"] = grow(core, grow_by)
    ring = grow(core, 7) & ~grow(core, 4)
    # Contrast of the glyph pixels over the pixels around them, column by column, in every frame.
    glyph_n = np.maximum(core.sum(axis=0), 1)
    ring_n = np.maximum(ring.sum(axis=0), 1)
    stack = stack.astype(np.float32)
    per_frame = ((stack * core).sum(axis=1) / glyph_n) - ((stack * ring).sum(axis=1) / ring_n)
    per_frame[:, ~core.any(axis=0)] = 0
    span = max(1, line["x1"] - line["x0"])
    # First the line's strength in each frame, then each frame against the line's own full strength.
    strength = []
    for frame in per_frame:
        lit = frame[frame > 14]
        strength.append(float(np.percentile(lit, 75)) if len(lit) >= 3 else 0.0)
    positive = [v for v in strength if v > 0]
    full = max(30.0, float(np.percentile(positive, 80))) if positive else 30.0
    line["progress"], line["alpha"], line["erased"] = [], [], []
    seen = gone = 0.0
    fade_on = max(14.0, full * 0.25)
    for frame, value in zip(per_frame, strength):
        lit = np.where(frame > fade_on)[0]
        if len(lit):
            seen = max(seen, (lit.max() - line["x0"]) / span)
            if line["slide"]:
                gone = max(gone, (lit.min() - line["x0"]) / span)
        line["progress"].append(seen)
        line["erased"].append(gone)
        line["alpha"].append(min(1.0, value / full * 1.05) if len(lit) else 0.0)
    # Repair only while the English is there, so credits crossing its place before or after stay untouched.
    present = [i for i, frame in enumerate(per_frame) if frame.max() > 10]
    line["first"], line["last"] = (present[0] - 2, present[-1] + 2) if present else (0, -1)
    # A frame is a good review sample when the whole line is out and bright.
    best = max(range(len(per_frame)), key=lambda i: (line["progress"][i] > 0.97) * line["alpha"][i])
    line["sample"] = line["start"] + best
    del line["strips"]


def repair(plane, mask):
    """Replace masked pixels from the nearest clean pixels above and below, weighted by distance."""
    h, w = plane.shape
    rows = np.arange(h)[:, None]
    above = np.where(~mask, rows, -1)
    above = np.maximum.accumulate(above, axis=0)
    below = np.where(~mask, rows, h)
    below = np.minimum.accumulate(below[::-1], axis=0)[::-1]
    cols = np.arange(w)[None, :].repeat(h, axis=0)
    va = plane[np.clip(above, 0, h - 1), cols].astype(np.float32)
    vb = plane[np.clip(below, 0, h - 1), cols].astype(np.float32)
    da = (rows - above).astype(np.float32)
    db = (below - rows).astype(np.float32)
    va = np.where(above < 0, vb, va)
    vb = np.where(below >= h, va, vb)
    t = da / np.maximum(da + db, 1)
    out = plane.copy()
    fill = va * (1 - t) + vb * t
    # Average sideways, or a textured background shows vertical streaks.
    edge = np.pad(fill, ((0, 0), (3, 3)), mode="edge")
    total = np.cumsum(np.pad(edge, ((0, 0), (1, 0))), axis=1)
    fill = (total[:, 7:] - total[:, :-7]) / 7
    fill = np.clip(fill, 0, 255).astype(np.uint8)
    out[mask] = fill[mask]
    return out


def clean(y, u, v, lines, n):
    """Repair every active line in one go, so that one line's glyphs are never the source for another's repair."""
    full = np.zeros((H, W), dtype=bool)
    for ln in lines:
        i = n - ln["start"]
        if not ln["first"] <= i <= ln["last"]:
            continue
        # Letters fade in ahead of the measured edge: look ahead, and keep a wide margin.
        reach = ln["x0"] + int(min(1.0, ln["progress"][min(i + 12, len(ln["progress"]) - 1)]) * (ln["x1"] - ln["x0"])) + 70
        view = full[ln["y0"]:ln["y1"]]
        view[:, :reach] |= ln["mask"][:, :reach]
    if not full.any():
        return
    rows = np.where(full.any(axis=1))[0]
    r0, r1 = max(0, rows.min() - 1) & ~1, min(H, rows.max() + 3) & ~1
    y[r0:r1] = repair(y[r0:r1], full[r0:r1])
    m = full[r0:r1]
    cm = m[0::2, 0::2] | m[1::2, 0::2] | m[0::2, 1::2] | m[1::2, 1::2]
    u[r0 // 2:r1 // 2] = repair(u[r0 // 2:r1 // 2], cm)
    v[r0 // 2:r1 // 2] = repair(v[r0 // 2:r1 // 2], cm)


def draw(y, line, i, style):
    p, a = line["progress"][i], line["alpha"][i]
    if p <= 0 or a <= 0.02:
        return
    c, s = line["cover"], line["soft"]
    edge = min(1.0, p) * (line["w"] + 26)
    xs = np.arange(W, dtype=np.float32) - line["ox"]
    ramp = np.clip((edge - xs) / 26, 0, 1) * np.clip((xs - (line["erased"][i] * (line["w"] + 26) - 26)) / 26, 0, 1)
    mid = (line["top"] + line["bottom"]) // 2
    top = mid + style["cap"] // 2 - line["baseline"]
    top = max(0, top)
    h = min(c.shape[0], H - top)
    view = y[top:top + h].astype(np.float32)
    view *= 1 - s[:h] * ramp * a * style["shadow_dark"]
    if style.get("glow"):
        view = np.maximum(view, s[:h] * ramp * a * style["glow"])
    cov = c[:h] * ramp * a
    view = view * (1 - cov) + 235 * cov
    y[top:top + h] = np.clip(view, 0, 255).astype(np.uint8)


def process(h264, out264, video, sample_dir):
    lines, total = load_lines(h264, video["cues"], video["end"])
    style = video["style"]
    for ln in lines:
        analyse(ln, video.get("threshold", 40), video.get("grow", 4), video.get("streak", STREAK))
        lay_out(ln, style)
    samples = {ln["sample"] for ln in lines}
    dec = decoder(h264)
    enc = encoder(out264)
    n = 0
    os.makedirs(sample_dir, exist_ok=True)
    while True:
        buf = dec.stdout.read(FS)
        if len(buf) < FS:
            break
        fr = np.frombuffer(buf, dtype=np.uint8).copy()
        y = fr[:W * H].reshape(H, W)
        u = fr[W * H:W * H + W * H // 4].reshape(H // 2, W // 2)
        v = fr[W * H + W * H // 4:].reshape(H // 2, W // 2)
        active = [ln for ln in lines if ln["start"] <= n < ln["stop"]]
        if active:
            clean(y, u, v, active, n)
        for ln in active:
            draw(y, ln, n - ln["start"], style)
        if n in samples:
            subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", f"{W}x{H}", "-i", "-", "-frames:v", "1", f"{sample_dir}/{n:05d}.png"], input=fr.tobytes())
        enc.stdin.write(fr.tobytes())
        n += 1
    enc.stdin.close()
    enc.wait()
    dec.wait()
    if enc.returncode:
        raise SystemExit("encoder failed")
    return n


def patch_movie(root, built):
    out = f"{root}/build/assets/movie.cpk"
    same = cpk_write.replace_by_append(f"{root}/game/PCSE00644/gamedata/movie.cpk", out, built)
    print(f"movie.cpk: {len(built)} videos replaced and read back, {same} others identical, header unchanged, {os.path.getsize(out)} bytes")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ROOT = sys.argv[1]
    names = sys.argv[2:] or list(video_cues.VIDEOS)
    work = f"{ROOT}/build/assets/video"
    os.makedirs(work, exist_ok=True)
    f, _, ents = cpk.open_cpk(f"{ROOT}/game/PCSE00644/gamedata/movie.cpk")
    by = {e["name"]: e for e in ents}
    for name in names:
        video = video_cues.VIDEOS[name]
        e = by[name]
        f.seek(e["off"])
        orig = f.read(e["csize"])
        src = f"{work}/{name}.source.264"
        with open(src, "wb") as o:
            for au in usm.video_units(orig):
                o.write(au)
        out264 = f"{work}/{name}.264"
        report = f"{ROOT}/build/report/video/{name}"
        shutil.rmtree(report, ignore_errors=True)
        frames = process(src, out264, video, report)
        aus = usm.split_annexb(open(out264, "rb").read())
        data = usm.remux(orig, aus)
        check, old = usm.chunks(data), usm.chunks(orig)
        ok_seq = [(c["tag"], c["typ"]) for c in check] == [(c["tag"], c["typ"]) for c in old]
        ok_rest = [c["body"] for c in check if c["tag"] != b"@SFV" and c["body"][:4] != b"@UTF"] == [c["body"] for c in old if c["tag"] != b"@SFV" and c["body"][:4] != b"@UTF"]
        print(f"{name}: {frames} frames, {len(aus)} units, largest {max(map(len, aus))}, {len(orig)} -> {len(data)} bytes; chunk order same: {ok_seq}; audio same: {ok_rest}")
        if not (ok_seq and ok_rest):
            raise SystemExit("rebuilt video differs structurally")
        open(f"{work}/{name}", "wb").write(data)
        os.remove(src)
        os.remove(out264)
    built = {n: open(f"{work}/{n}", "rb").read() for n in os.listdir(work) if n.endswith(".USM")}
    patch_movie(ROOT, built)
