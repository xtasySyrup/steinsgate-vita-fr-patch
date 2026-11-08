"""Render selected strings from the built patch with its own font and width table (a simulation, not a capture).

Also prints wrap bounds implied by a line observed on real hardware.
"""
import os, struct, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cpk import layla, parse_utf
from sglib import itoc_rows
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = sys.argv[1]
d = f"{ROOT}/build/patch/rePatch/PCSE00644/gamedata"
script = open(f"{d}/script.cpk", "rb").read()
system = open(f"{d}/system.cpk", "rb").read()
W = open(f"{ROOT}/game/PCSE00644/mai_moe/eboot_origin.bin", "rb").read()[0x1061E0:0x1061E0 + 836]

e = {x["ID"]: x for x in itoc_rows(system)}[10]
g = layla(system[e["pos"]:e["pos"] + e["FileSize"]])
off, size = struct.unpack_from("<II", g, 0x20)
atlas = g[off:off + size]

_, r = parse_utf(script[16:16 + struct.unpack_from("<I", script, 8)[0]])
toc = r[0]["TocOffset"]
_, t = parse_utf(script[toc + 16:toc + 16 + struct.unpack_from("<I", script, toc + 8)[0]])
files = {}
for row in t:
    o = row["FileOffset"] + toc
    x = script[o:o + row["FileSize"]]
    files[row["FileName"].rsplit(".", 1)[0].upper()] = layla(x) if x[:8] == b"CRILAYLA" else x


def expr_end(b, i):
    while True:
        c = b[i]
        if c == 0:
            return i + 1
        i += ((c & 0xE0) - 0x80) // 0x20 + 2 if c >= 0x80 else 2


def codes(name, k):
    b = files[name]
    st = struct.unpack_from("<L", b, 4)[0]
    i = struct.unpack_from("<L", b, st + 4 * k)[0]
    out = []
    while b[i] != 0xFF:
        c = b[i]
        if c >= 0x80:
            out.append((c << 8 | b[i + 1]) & 0x7FFF)
            i += 2
            continue
        i += 1
        if c == 2:
            out = []
        elif c == 4:
            i += 1
        elif c == 0x15:
            i = expr_end(b, i)
        elif c in (0xC, 0x11, 0x12, 0x13):
            i += 2
    return out


def tile(c):
    x, y = (c % 64) * 32, (c // 64) * 32
    return Image.frombytes("L", (32, 32), b"".join(atlas[(y + q) * 2048 + x:(y + q) * 2048 + x + 32] for q in range(32)))


# Hardware observation from the user's photo: line 1 of SG00_01:1 ended at "droite." and "Seulement" wrapped.
c = codes("SG00_01", 1)
sp = [i for i, x in enumerate(c) if x == 63]
acc, line = 0, []
for i, x in enumerate(c):
    acc += W[x]
    if x == 63:
        line.append((i, acc))
w1 = dict(line)
words = [i for i, _ in line]
print("space positions/widths:", line)

items = [("SG02_03", 206), ("SG02_03", 207), ("SG10_02", 144), ("SG07_11", 243), ("_MAIL", 198), ("_MAIL", 1141), ("_MAIL", 1386),
         ("_ATCH", 0), ("_ATCH", 1412), ("_ATCH", 1767), ("MACROSYS", 0), ("SG01_13", 100)]
page = Image.new("L", (1600, 40 * len(items) + 16), 24)
y = 8
for name, k in items:
    x = 8
    for code in codes(name, k):
        im = tile(code)
        page.paste(im, (x, y), im)
        x += W[code]
        if x > 1560:
            break
    y += 40
os.makedirs(f"{ROOT}/build/report", exist_ok=True)
page.save(f"{ROOT}/build/report/preview_full.png")
print("wrote preview")
