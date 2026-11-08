"""Read menu, TIPS and phone strings back from the built patch: decode them, compare widths with the English, render a sample.

Usage: python -I tools/check_ui.py <project root>
Writes build/report/ui_widths.tsv and build/report/preview_menus.png. A simulation, not a capture.
"""
import collections, os, struct, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cpk import layla, parse_utf
from sglib import itoc_rows, get_tile
from PIL import Image, ImageDraw

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = sys.argv[1]
d = f"{ROOT}/build/patch/rePatch/PCSE00644/gamedata"
W = open(f"{ROOT}/game/PCSE00644/mai_moe/eboot_origin.bin", "rb").read()[0x1061E0:0x1061E0 + 836]
system = open(f"{d}/system.cpk", "rb").read()
e = {x["ID"]: x for x in itoc_rows(system)}[10]
g = layla(system[e["pos"]:e["pos"] + e["FileSize"]])
off, size = struct.unpack_from("<II", g, 0x20)
atlas = g[off:off + size]


def load(path):
    raw = open(path, "rb").read()
    _, r = parse_utf(raw[16:16 + struct.unpack_from("<I", raw, 8)[0]])
    toc = r[0]["TocOffset"]
    _, t = parse_utf(raw[toc + 16:toc + 16 + struct.unpack_from("<I", raw, toc + 8)[0]])
    out = {}
    for row in t:
        o = row["FileOffset"] + toc
        x = raw[o:o + row["FileSize"]]
        out[row["FileName"].rsplit(".", 1)[0].upper()] = layla(x) if x[:8] == b"CRILAYLA" else x
    return out


def expr_end(b, i):
    while True:
        c = b[i]
        if c == 0:
            return i + 1
        i += ((c & 0xE0) - 0x80) // 0x20 + 2 if c >= 0x80 else 2


def strings(b):
    st, rt = struct.unpack_from("<LL", b, 4)
    res = []
    for k in range((rt - st) // 4):
        i = struct.unpack_from("<L", b, st + 4 * k)[0]
        cur = []
        while b[i] != 0xFF:
            c = b[i]
            if c >= 0x80:
                cur.append((c << 8 | b[i + 1]) & 0x7FFF)
                i += 2
                continue
            i += 1
            if c == 0:
                cur.append(-1)
            elif c == 4:
                i += 1
            elif c == 0x15:
                i = expr_end(b, i)
            elif c in (0xC, 0x11, 0x12, 0x13):
                i += 2
        res.append(cur)
    return res


TXT = {63: " ", 0: " ", -1: "|", 64: "/", 65: ":", 66: "-", 68: "!", 69: "?", 70: "’", 71: ".", 75: ",", 79: "(", 80: ")", 93: '"', 192: ",", 193: ".", 194: ":", 195: ";", 196: "?", 197: "!", 201: "’", 202: "“", 203: "”", 204: "(", 205: ")", 510: "■",
       100: "à", 101: "â", 102: "ä", 103: "ç", 104: "è", 105: "é", 106: "ê", 107: "ë", 108: "î", 109: "ï", 110: "ô", 111: "ö", 112: "ù", 113: "û", 114: "ü", 115: "œ", 117: "À", 118: "Â", 119: "Ç", 120: "È", 121: "É", 122: "Ê", 126: "Œ"}
for i in range(10):
    TXT[1 + i] = TXT[128 + i] = str(i)
for i in range(26):
    TXT[11 + i] = TXT[138 + i] = chr(65 + i)
    TXT[37 + i] = TXT[164 + i] = chr(97 + i)


def text(s):
    return "".join(TXT.get(c, f"<{c}>") for c in s)


def widest(s):
    best = cur = 0
    for c in s:
        if c == -1:
            best = max(best, cur)
            cur = 0
        else:
            cur += W[c]
    return max(best, cur)


old = load(f"{ROOT}/game/PCSE00644/gamedata/script.cpk")
new = load(f"{d}/script.cpk")
out = open(f"{ROOT}/build/report/ui_widths.tsv", "w", encoding="utf-8")
out.write("scene\tstring\tenglish_width\tfrench_width\tenglish\tfrench\n")
for scene in ("_SYSTEM", "_STARTUP", "_TIPS", "MACROSYS"):
    a, b = strings(old[scene]), strings(new[scene])
    assert len(a) == len(b), scene
    changed = sum(x != y for x, y in zip(a, b))
    top = max(widest(x) for x in a)
    grown = [(k, widest(x), widest(y)) for k, (x, y) in enumerate(zip(a, b)) if x != y and widest(y) > widest(x) * 1.15 and len(x) < 90]
    print(f"{scene}: {len(a)} strings, {changed} changed, English widest {top}; French over the widest English: {sum(widest(y) > top for y in b)}; short strings over 115% of their English: {len(grown)}")
    for k, (x, y) in enumerate(zip(a, b)):
        if x != y:
            out.write(f"{scene}\t{k}\t{widest(x)}\t{widest(y)}\t{text(x)}\t{text(y)}\n")
out.close()

# French accents and punctuation must never reach odd slots in fixed-row strings
for scene in ("_MAIL", "_ATCH", "_STARTUP"):
    c = collections.Counter(x for s in strings(new[scene]) for x in s if x >= 128)
    print(scene, "slots from 128 up in French:", c.most_common(14))

a, b = strings(old["_STARTUP"]), strings(new["_STARTUP"])
print("_STARTUP widest French lines:", sorted(((widest(y), k, text(y)) for k, y in enumerate(b) if k >= 8), reverse=True)[:6])
print("_STARTUP widest English lines:", sorted(((widest(y), k, text(y)) for k, y in enumerate(a) if k >= 8), reverse=True)[:4])

items = [("_SYSTEM", k) for k in (2, 4, 5, 9, 18, 20, 23, 30, 36, 38, 52, 60, 76, 157)] + [("_STARTUP", k) for k in (8, 9, 11, 13, 14, 25, 31, 61, 76)] + [("_TIPS", k) for k in (0, 2, 6, 11, 12, 15, 20, 30)] + [("MACROSYS", 6)]
page = Image.new("L", (1560, len(items) * 38 + 12), 24)
dr = ImageDraw.Draw(page)
y = 6
for scene, k in items:
    dr.text((6, y + 12), f"{scene} {k}", fill=150)
    x = 110
    for c in strings(new[scene])[k]:
        if c == -1:
            c = 63
        im = get_tile(atlas, c)
        page.paste(im, (x, y), im)
        x += W[c]
        if x > 1530:
            break
    y += 38
page.save(f"{ROOT}/build/report/preview_menus.png")
print("wrote previews")
