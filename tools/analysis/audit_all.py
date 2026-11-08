"""Read-only audit of every script: character use per scene, Steam-to-Vita code evidence, control-code differences."""
import collections, os, struct, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cpk import layla, parse_utf
from PIL import Image, ImageDraw

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = sys.argv[1]
GAME = f"{ROOT}/game/PCSE00644/gamedata"


def expr_end(b, i):
    while True:
        c = b[i]
        if c == 0:
            return i + 1
        i += ((c & 0xE0) - 0x80) // 0x20 + 2 if c >= 0x80 else 2


def expr_val(e):
    c = e[0]
    n = ((c & 0xE0) - 0x80) // 0x20 + 1
    return (c & 0x1F) if n == 1 else int.from_bytes(e[1:n], "little")


def parse(b, i, vita):
    codes, ops = [], []
    while b[i] != 0xFF:
        c = b[i]
        if c >= 0x80:
            codes.append((c << 8 | b[i + 1]) & 0x7FFF)
            i += 2
            continue
        i += 1
        if c == 4:
            if vita:
                ops.append((4, b[i]))
                i += 1
            else:
                e = expr_end(b, i)
                ops.append((4, expr_val(b[i:e])))
                i = e
        elif c == 0x15:
            e = expr_end(b, i)
            ops.append((c, bytes(b[i:e])))
            i = e
        elif c in (0xC, 0x11, 0x12, 0x13):
            ops.append((c, bytes(b[i:i + 2])))
            i += 2
        else:
            ops.append((c, None))
    return codes, ops


def strings(d, vita):
    st, rt = struct.unpack_from("<LL", d, 4)
    return [parse(d, struct.unpack_from("<L", d, st + 4 * k)[0], vita) for k in range((rt - st) // 4)]


raw = open(f"{GAME}/script.cpk", "rb").read()
_, r = parse_utf(raw[16:16 + struct.unpack_from("<I", raw, 8)[0]])
hd = r[0]
toc = hd["TocOffset"]
_, t = parse_utf(raw[toc + 16:toc + 16 + struct.unpack_from("<I", raw, toc + 8)[0]])
vita = {}
for e in t:
    o = e["FileOffset"] + toc
    d = raw[o:o + e["FileSize"]]
    vita[e["FileName"].rsplit(".", 1)[0].upper()] = layla(d) if d[:8] == b"CRILAYLA" else d
mpk = open(f"{ROOT}/sources/sg-fr-patch/script.mpk", "rb").read()
steam = {}
for i in range(struct.unpack_from("<Q", mpk, 8)[0]):
    b = 0x40 + i * 0x100
    _, _, off, _, u = struct.unpack_from("<LLQQQ", mpk, b)
    steam[mpk[b + 0x20:b + 0x100].split(b"\0")[0].decode().rsplit(".", 1)[0].upper()] = mpk[off:off + u]
steam["_STARTUP"] = steam.pop("_STARTUP_WIN")

parsed_v = {k: strings(v, True) for k, v in vita.items() if v[:4] == b"SC3\0"}
parsed_s = {k: strings(v, False) for k, v in steam.items() if v[:4] == b"SC3\0"}

print("=== per-scene Latin style (only scenes with text; share of Vita chars in halfwidth 1-62)")
styles = {}
for k, ss in sorted(parsed_v.items()):
    c = collections.Counter(x for cs, _ in ss for x in cs)
    tot = sum(c.values())
    if not tot:
        continue
    half = sum(n for x, n in c.items() if 1 <= x <= 62)
    full = sum(n for x, n in c.items() if 128 <= x <= 189)
    styles[k] = (half, full)
print("non-story or mixed:", [(k, h, f) for k, (h, f) in styles.items() if not k.startswith("SG") or h > f * 0.05])

print("\n=== structure differences on index-aligned strings, by scene")
tot_diff = 0
samples = []
per = collections.Counter()
kinds = collections.Counter()
for k in sorted(parsed_v):
    if k not in parsed_s or len(parsed_v[k]) != len(parsed_s[k]):
        continue
    for idx, ((vc, vo), (sc, so)) in enumerate(zip(parsed_v[k], parsed_s[k])):
        if vo != so:
            tot_diff += 1
            per[k] += 1
            a, b = collections.Counter(x[0] for x in vo), collections.Counter(x[0] for x in so)
            kinds[tuple(sorted(((a - b) + (b - a)).items()))] += 1
            if len(samples) < 14 and k.startswith("SG"):
                samples.append((k, idx, [x[0] for x in vo], [x[0] for x in so]))
print("total differing strings", tot_diff)
print("by scene:", per.most_common(30))
print("difference kinds:", kinds.most_common(12))
for s in samples:
    print(" ", s)

print("\n=== Steam codes with position-aligned evidence: code in FR -> Vita non-Latin codes in the same English string")
ev = collections.defaultdict(collections.Counter)
use = collections.Counter()
for k in parsed_v:
    if k not in parsed_s or len(parsed_v[k]) != len(parsed_s[k]):
        continue
    for (vc, _), (sc, _) in zip(parsed_v[k], parsed_s[k]):
        vs = {x for x in vc if not (128 <= x <= 189 or 1 <= x <= 62 or x in (63, 192, 193, 196, 197, 201, 202, 203, 66))}
        for c in set(sc):
            use[c] += 1
            for v in vs:
                ev[c][v] += 1
rare = [c for c in use if not (1 <= c <= 62 or 100 <= c <= 127 or 128 <= c <= 189)]
for c in sorted(rare):
    print(f"  {c}: in {use[c]} strings -> {ev[c].most_common(4)}")

print("\n=== Vita-only symbol codes across all scripts")
allv = collections.Counter(x for ss in parsed_v.values() for cs, _ in ss for x in cs)
print([(c, n) for c, n in sorted(allv.items()) if not (128 <= c <= 189 or 1 <= c <= 62)])


# Labelled font sheets for reading the Vita character table by eye.
d = open(f"{ROOT}/build/archive/B2_script_and_font/rePatch/PCSE00644/gamedata/system.cpk", "rb").read()
g = open(sys.argv[2], "rb").read()
off, size = struct.unpack_from("<II", g, 0x20)
atlas = g[off:off + size]


def sheet(path, start, stop, per_row=24):
    n = stop - start
    rows = (n + per_row - 1) // per_row
    cw, ch = 54, 52
    im = Image.new("L", (cw * per_row, ch * rows), 30)
    dr = ImageDraw.Draw(im)
    for i in range(n):
        c = start + i
        x0, y0 = (c % 64) * 32, (c // 64) * 32
        t = Image.frombytes("L", (32, 32), b"".join(atlas[(y0 + r) * 2048 + x0:(y0 + r) * 2048 + x0 + 32] for r in range(32)))
        px, py = (i % per_row) * cw + 8, (i // per_row) * ch + 16
        im.paste(t, (px, py), t)
        dr.text(((i % per_row) * cw + 8, (i // per_row) * ch + 2), str(c), fill=170)
    im.save(path)


os.makedirs(f"{ROOT}/build/sheets", exist_ok=True)
sheet(f"{ROOT}/build/sheets/a_64-99.png", 64, 100)
sheet(f"{ROOT}/build/sheets/b_256-330.png", 256, 330)
sheet(f"{ROOT}/build/sheets/c_440-600.png", 440, 600)
sheet(f"{ROOT}/build/sheets/d_600-833.png", 600, 833)
print("sheets written")
