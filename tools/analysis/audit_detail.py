"""Second audit pass: kana sheet, odd characters in context, speaker mismatches, spaces in fixed-width scenes, script sizes."""
import collections, os, struct, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cpk import layla, parse_utf
from PIL import Image, ImageDraw

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = sys.argv[1]
charset = open(sys.argv[3], encoding="utf-8").read().rstrip("\n")


def expr_end(b, i):
    while True:
        c = b[i]
        if c == 0:
            return i + 1
        i += ((c & 0xE0) - 0x80) // 0x20 + 2 if c >= 0x80 else 2


def parse(b, i, vita):
    toks = []
    while b[i] != 0xFF:
        c = b[i]
        if c >= 0x80:
            toks.append(("t", (c << 8 | b[i + 1]) & 0x7FFF))
            i += 2
            continue
        i += 1
        if c == 4:
            toks.append(("op", 4))
            i = i + 1 if vita else expr_end(b, i)
        elif c == 0x15:
            toks.append(("op", c))
            i = expr_end(b, i)
        elif c in (0xC, 0x11, 0x12, 0x13):
            toks.append(("op", c, bytes(b[i:i + 2])))
            i += 2
        else:
            toks.append(("op", c))
    return toks


def strings(d, vita):
    st, rt = struct.unpack_from("<LL", d, 4)
    return [parse(d, struct.unpack_from("<L", d, st + 4 * k)[0], vita) for k in range((rt - st) // 4)]


raw = open(f"{ROOT}/game/PCSE00644/gamedata/script.cpk", "rb").read()
_, r = parse_utf(raw[16:16 + struct.unpack_from("<I", raw, 8)[0]])
toc = r[0]["TocOffset"]
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
V = {k: strings(v, True) for k, v in vita.items() if v[:4] == b"SC3\0"}
S = {k: strings(v, False) for k, v in steam.items() if v[:4] == b"SC3\0"}


def txt(toks):
    out = []
    for x in toks:
        if x[0] == "t":
            c = x[1]
            if 97 <= c <= 127:
                out.append(f"<{c}>")
            else:
                out.append(charset[c] if c < len(charset) else f"<{c}>")
        elif x[1] == 1:
            out.append("{N}")
        elif x[1] == 2:
            out.append("{L}")
        elif x[1] == 3:
            out.append("{P}")
    return "".join(out)


print("=== odd Steam codes in context")
odd = {2837, 2882, 2894, 3660, 7394, 232, 237, 496, 541, 553, 584, 623, 391, 458, 460, 396, 422}
seen = collections.Counter()
for k in S:
    if k not in V or len(V[k]) != len(S[k]):
        continue
    for idx, (a, b) in enumerate(zip(V[k], S[k])):
        hit = odd & {x[1] for x in b if x[0] == "t"}
        for c in hit:
            seen[c] += 1
            if seen[c] <= 1:
                print(f"{c} {charset[c] if c < len(charset) else '?'} {k}:{idx}\n   FR {txt(b)[:90]}\n   EN {txt(a)[:90]}")

print("\n=== speaker mismatches (one side has a name)")
n = 0
for k in sorted(S):
    if k not in V or len(V[k]) != len(S[k]):
        continue
    for idx, (a, b) in enumerate(zip(V[k], S[k])):
        ha, hb = any(x[0] == "op" and x[1] == 1 for x in a), any(x[0] == "op" and x[1] == 1 for x in b)
        if ha != hb:
            n += 1
            if n <= 12:
                print(f"{k}:{idx} EN {txt(a)[:70]!r}\n         FR {txt(b)[:70]!r}")
print("total", n)

print("\n=== SG03_07 / SG02_19 present-code pattern")
for k, idx in (("SG03_07", 10), ("SG02_19", 85)):
    print(k, idx, "EN", txt(V[k][idx])[:80], "\n   FR", txt(S[k][idx])[:80])

print("\n=== margin value differences")
c = 0
for k in sorted(S):
    if k not in V or len(V[k]) != len(S[k]):
        continue
    for idx, (a, b) in enumerate(zip(V[k], S[k])):
        ma = [x for x in a if x[0] == "op" and len(x) == 3]
        mb = [x for x in b if x[0] == "op" and len(x) == 3]
        if ma != mb and c < 5:
            c += 1
            print(k, idx, [(x[1], x[2].hex()) for x in ma][:6], [(x[1], x[2].hex()) for x in mb][:6])

print("\n=== spaces in fixed-width scenes (code: count)")
for k in ("_ATCH", "_MAIL", "CLRFLG", "MACROSYS2", "_STARTUP"):
    va = collections.Counter(x[1] for s in V[k] for x in s if x[0] == "t")
    sa = collections.Counter(x[1] for s in S.get(k, []) for x in s if x[0] == "t")
    print(k, "vita 0:", va[0], "63:", va[63], "| steam 0:", sa[0], "63:", sa[63], "128-189:", sum(n for c, n in sa.items() if 128 <= c <= 189), "1-62:", sum(n for c, n in sa.items() if 1 <= c <= 62))
print("_STARTUP vita codes:", sorted(collections.Counter(x[1] for s in V["_STARTUP"] for x in s if x[0] == "t").items())[:50])
print("_STARTUP first strings raw:", [[x[1] for x in s if x[0] == "t"][:14] for s in V["_STARTUP"][:3]])

print("\n=== script sizes")
print("largest Vita:", sorted(((len(v), k) for k, v in vita.items()), reverse=True)[:6])

g = open(sys.argv[2], "rb").read()
off, size = struct.unpack_from("<II", g, 0x20)
atlas = g[off:off + size]
start, stop, per = 330, 440, 24
cw, ch = 54, 52
rows = (stop - start + per - 1) // per
im = Image.new("L", (cw * per, ch * rows), 30)
dr = ImageDraw.Draw(im)
for i in range(stop - start):
    c = start + i
    x0, y0 = (c % 64) * 32, (c // 64) * 32
    tile = Image.frombytes("L", (32, 32), b"".join(atlas[(y0 + q) * 2048 + x0:(y0 + q) * 2048 + x0 + 32] for q in range(32)))
    im.paste(tile, ((i % per) * cw + 8, (i // per) * ch + 16), tile)
    dr.text(((i % per) * cw + 8, (i // per) * ch + 2), str(c), fill=170)
im.save(f"{ROOT}/build/sheets/e_330-440.png")
