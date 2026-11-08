"""Simulate phone text: font file 11, each glyph clipped to its table width. Old font on the left, new on the right.

A simulation, not a capture. The old column should reproduce the clipped accents seen on real hardware.
Writes build/report/preview_phone.png.
"""
import os, struct, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cpk import layla, parse_utf
from sglib import itoc_rows, get_tile
from PIL import Image, ImageDraw

ROOT = sys.argv[1]
d = f"{ROOT}/build/patch/rePatch/PCSE00644/gamedata"
script = open(f"{d}/script.cpk", "rb").read()
W = open(f"{ROOT}/game/PCSE00644/mai_moe/eboot_origin.bin", "rb").read()[0x1061E0:0x1061E0 + 836]


def atlas(path):
    raw = open(path, "rb").read()
    e = {x["ID"]: x for x in itoc_rows(raw)}[11]
    g = layla(raw[e["pos"]:e["pos"] + e["FileSize"]])
    off, size = struct.unpack_from("<II", g, 0x20)
    return g[off:off + size]


old = atlas(f"{ROOT}/build/archive/B2_script_and_font/rePatch/PCSE00644/gamedata/system.cpk")
new = atlas(f"{d}/system.cpk")

_, r = parse_utf(script[16:16 + struct.unpack_from("<I", script, 8)[0]])
toc = r[0]["TocOffset"]
_, t = parse_utf(script[toc + 16:toc + 16 + struct.unpack_from("<I", script, toc + 8)[0]])
row = next(x for x in t if x["FileName"].rsplit(".", 1)[0].upper() == "_MAIL")
b = script[row["FileOffset"] + toc:row["FileOffset"] + toc + row["FileSize"]]
st = struct.unpack_from("<L", b, 4)[0]


def lines(k):
    i = struct.unpack_from("<L", b, st + 4 * k)[0]
    out, cur = [], []
    while b[i] != 0xFF:
        c = b[i]
        if c >= 0x80:
            cur.append((c << 8 | b[i + 1]) & 0x7FFF)
            i += 2
            continue
        i += 1
        if c == 0:
            out.append(cur)
            cur = []
        elif c == 4:
            i += 1
        elif c in (0xC, 0x11, 0x12, 0x13):
            i += 2
    return out + [cur]


def advance(c):
    """Hardware photo: slots from 128 up take a full cell on the phone, whatever the width table says."""
    return W[c] if c < 128 else 32


def draw(page, a, codes, x0, y):
    x = x0
    for c in codes:
        w = advance(c)
        tile = get_tile(a, c).crop((0, 0, w, 32))
        page.paste(tile, (x, y), tile)
        x += w


ITEMS = [(18, 153), (0, 267), (1, 267), (4, 360), (5, 360), (6, 360), (8, 360), (9, 308), (13, 153), (14, 153),
         (35, 388), (36, 388), (38, 388), (40, 313), (41, 313), (42, 388), (43, 388), (45, 388), (46, 388), (47, 388), (49, 388), (51, 308),
         (53, 308), (75, 308), (80, 313), (11, 360), (83, 360)]
rows = sum(len(lines(k)) for k, _ in ITEMS)
COL = 700
page = Image.new("L", (COL * 2 + 60, rows * 36 + 40), 24)
dr = ImageDraw.Draw(page)
dr.text((60, 8), "before (font on the Vita now)", fill=170)
dr.text((60 + COL, 8), "after (this build); grey line = limit estimated from photos", fill=170)
y = 28
over = []
for k, limit in ITEMS:
    dr.text((8, y + 10), str(k), fill=170)
    for ln in lines(k):
        draw(page, old, ln, 60, y)
        draw(page, new, ln, 60 + COL, y)
        dr.line([(60 + COL + limit, y), (60 + COL + limit, y + 32)], fill=110)
        width = sum(advance(c) for c in ln)
        if width > limit:
            over.append((k, width, limit))
        y += 36
os.makedirs(f"{ROOT}/build/report", exist_ok=True)
page.save(f"{ROOT}/build/report/preview_phone.png")
print("lines over the estimated limit:", over)
