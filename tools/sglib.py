"""Shared code for the Steins;Gate Vita patch: font accents, CRILAYLA compressor, system.cpk handling.

The font output of this module is what ran correctly on real hardware in test C1 (story text, backlog and
phone menus). Changing it means retesting on the Vita.
"""
import io, os, struct, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cpk import layla, parse_utf
from PIL import Image, ImageDraw

ALIGN = 2048

# Accent slots from the Steam FR. The Vita font leaves 97..127 blank, with table width 17.
ACCENTS = {
    100: ("a", "grave"), 101: ("a", "circ"), 102: ("a", "uml"), 103: ("c", "cedil"), 104: ("e", "grave"),
    105: ("e", "acute"), 106: ("e", "circ"), 107: ("e", "uml"), 108: ("i", "circ"), 109: ("i", "uml"),
    110: ("o", "circ"), 111: ("o", "uml"), 112: ("u", "grave"), 113: ("u", "circ"), 114: ("u", "uml"),
    115: ("oe", None), 117: ("A", "grave"), 118: ("A", "circ"), 119: ("C", "cedil"), 120: ("E", "grave"),
    121: ("E", "acute"), 122: ("E", "circ"), 126: ("OE", None),
}


def latin_slot(ch):
    if ch.isupper():
        return 138 + ord(ch) - 65
    return 164 + ord(ch) - 97


def fixed_slot(ch):
    return latin_slot(ch) - 127


# ---------------------------------------------------------------- CRILAYLA compressor
PAD_MIN, PAD_MAX = 4, 7  # unused front bytes observed in CRI's own streams


def layla_compress(data, exact_size):
    """Compress to exactly exact_size stored bytes, padding unused stream bytes at the front."""
    prefix, body = data[:0x100], data[0x100:]
    rev = body[::-1]
    n = len(rev)
    head = {}
    prev = [-1] * n
    bits = bytearray()
    acc = nb = 0

    def put(value, count):
        nonlocal acc, nb
        for s in range(count - 1, -1, -1):
            acc = (acc << 1) | ((value >> s) & 1)
            nb += 1
            if nb == 8:
                bits.append(acc)
                acc = nb = 0

    def insert(i):
        if i + 3 <= n:
            k = rev[i] | rev[i + 1] << 8 | rev[i + 2] << 16
            prev[i] = head.get(k, -1)
            head[k] = i

    def find(i):
        best = bl = 0
        if i + 3 > n:
            return 0, 0
        j = head.get(rev[i] | rev[i + 1] << 8 | rev[i + 2] << 16, -1)
        tries = 96
        while j >= 0 and tries:
            d = i - j
            if d > 8194:
                break
            tries -= 1
            if d >= 3:
                m = 3 if rev[i:i + 3] == rev[j:j + 3] else 0
                if m:
                    lim = n - i
                    while m < lim and rev[j + m] == rev[i + m]:
                        m += 1
                    if m > bl:
                        best, bl = d, m
                        if m > 4096:
                            break
            j = prev[j]
        return best, bl

    def match_bits(l):
        r = l - 3
        cost = 14
        for w in (2, 3, 5):
            m = (1 << w) - 1
            cost += w
            if r < m:
                return cost
            r -= m
        while r >= 255:
            cost += 8
            r -= 255
        return cost + 8

    # Tokenise first, so spare room can be spent on real data rather than padding.
    tokens = []  # (position, distance, length); distance 0 means literal
    i = 0
    while i < n:
        d, l = find(i)
        if l >= 3:
            insert(i)
            d2, l2 = find(i + 1) if i + 1 < n else (0, 0)
            if l2 > l + 1:  # lazy: take a literal when the next match is clearly longer
                tokens.append((i, 0, 1))
                i += 1
                continue
            tokens.append((i, d, l))
            for k in range(1, l):
                insert(i + k)
            i += l
        else:
            insert(i)
            tokens.append((i, 0, 1))
            i += 1

    csize = exact_size - 16 - 0x100
    total = sum(9 if d == 0 else match_bits(l) for _, d, l in tokens)
    if (total + 7) // 8 > csize - PAD_MIN:
        raise OverflowError(f"compressed stream {(total + 7) // 8} > available {csize - PAD_MIN}")
    # CRI's streams leave 4-7 unused bytes at the front. Expand matches into literals to land there.
    target_hi = (csize - PAD_MIN) * 8
    target_lo = (csize - PAD_MAX) * 8 + 1
    literalise = set()
    for t, (pos, d, l) in enumerate(tokens):
        if total >= target_lo:
            break
        if d and total + 9 * l - match_bits(l) <= target_hi:
            total += 9 * l - match_bits(l)
            literalise.add(t)
    if total < target_lo:
        raise OverflowError(f"could not fill stream: {total} bits, need {target_lo}")

    for t, (pos, d, l) in enumerate(tokens):
        if d == 0 or t in literalise:
            for k in range(l):
                put(0, 1)
                put(rev[pos + k], 8)
            continue
        put(1, 1)
        put(d - 3, 13)
        r = l - 3
        for w in (2, 3, 5):
            m = (1 << w) - 1
            if r < m:
                put(r, w)
                break
            put(m, w)
            r -= m
        else:
            while r >= 255:
                put(255, 8)
                r -= 255
            put(r, 8)
    if nb:
        bits.append(acc << (8 - nb))
    pad = csize - len(bits)
    if not PAD_MIN <= pad <= PAD_MAX:
        raise ValueError(f"front gap {pad} outside {PAD_MIN}-{PAD_MAX}")
    stream = bytes(pad) + bytes(bits[::-1])
    return b"CRILAYLA" + struct.pack("<II", len(body), csize) + stream + prefix, len(bits)


# ---------------------------------------------------------------- font
TILE, COLS = 32, 64


def get_tile(a, c):
    x, y = (c % COLS) * TILE, (c // COLS) * TILE
    return Image.frombytes("L", (TILE, TILE), b"".join(a[(y + r) * 2048 + x:(y + r) * 2048 + x + TILE] for r in range(TILE)))


def put_tile(a, c, im):
    x, y = (c % COLS) * TILE, (c // COLS) * TILE
    raw = im.tobytes()
    for r in range(TILE):
        a[(y + r) * 2048 + x:(y + r) * 2048 + x + TILE] = raw[r * TILE:(r + 1) * TILE]


def diacritic(kind, cx, top):
    S = 8
    im = Image.new("L", (TILE * S, TILE * S), 0)
    dr = ImageDraw.Draw(im)
    w = int(2.4 * S)

    def L(pts):
        dr.line([(x * S, y * S) for x, y in pts], fill=255, width=w, joint="curve")

    if kind == "acute":
        L([(cx - 2.0, top + 5.2), (cx + 2.2, top + 0.4)])
    elif kind == "grave":
        L([(cx + 2.0, top + 5.2), (cx - 2.2, top + 0.4)])
    elif kind == "circ":
        L([(cx - 4.2, top + 5.0), (cx, top + 0.6), (cx + 4.2, top + 5.0)])
    elif kind == "uml":
        for sx in (-3.6, 3.6):
            r = 1.8 * S
            cy = (top + 3.0) * S
            dr.ellipse([(cx + sx) * S - r, cy - r, (cx + sx) * S + r, cy + r], fill=255)
    elif kind == "cedil":
        L([(cx - 0.2, 26.5), (cx + 0.8, 28.6), (cx + 2.2, 29.6), (cx + 0.4, 31.0), (cx - 2.0, 31.0)])
    return im.resize((TILE, TILE), Image.BOX)


def compose(a, slot, base, kind, layer, advance=17):
    """Layer 1 is font file 10 (story, backlog). Layer 2 is font file 11, which the phone draws clipped to the
    table width: its fixed-width letters sit at the left of a 17px cell, so accents must be built from those."""
    source = latin_slot if layer == 1 else fixed_slot
    if base in ("oe", "OE"):
        p1, p2 = get_tile(a, source(base[0])), get_tile(a, source(base[1]))
        b1, b2 = p1.getbbox(), p2.getbbox()
        c1, c2 = p1.crop(b1), p2.crop(b2)
        wide = Image.new("L", (c1.width + c2.width - 1, max(c1.height, c2.height)), 0)
        wide.paste(c1, (0, wide.height - c1.height))
        wide.paste(c2, (c1.width - 1, wide.height - c2.height))
        target = 16
        sq = wide.resize((target, wide.height), Image.LANCZOS)
        out = Image.new("L", (TILE, TILE), 0)
        x = (advance - target) // 2
        out.paste(sq, (x, 28 - sq.height))
        return out
    t = get_tile(a, source(base))
    if base == "i":  # drop the tittle
        px = t.load()
        for y in range(0, 10):
            for x in range(TILE):
                px[x, y] = 0
    box = t.getbbox()
    glyph = t.crop(box)
    top = box[1]
    if base.isupper() and kind != "cedil":  # shorten capitals to make room above
        newh = 19
        glyph = glyph.resize((glyph.width, newh), Image.LANCZOS)
        top = box[3] - newh
        acc_top = 1.5
    else:
        acc_top = top - 6.8
    x = (advance - glyph.width) // 2 if layer == 1 else box[0]
    out = Image.new("L", (TILE, TILE), 0)
    out.paste(glyph, (x, top))
    cx = x + glyph.width / 2
    if base == "c" or base == "C":
        cx -= 0.5
    d = diacritic(kind, cx, acc_top)
    return _max(out, d)


def _max(a, b):
    return Image.frombytes("L", a.size, bytes(max(x, y) for x, y in zip(a.tobytes(), b.tobytes())))


# ---------------------------------------------------------------- system.cpk
def itoc_rows(raw):
    n = struct.unpack_from("<I", raw, 8)[0]
    _, r = parse_utf(raw[16:16 + n])
    hd = r[0]
    o = hd["ItocOffset"]
    nn = struct.unpack_from("<I", raw, o + 8)[0]
    _, t = parse_utf(raw[o + 16:o + 16 + nn])
    rows = []
    for key in ("DataL", "DataH"):
        d = t[0].get(key)
        if d:
            rows += parse_utf(d)[1]
    rows.sort(key=lambda x: x["ID"])
    pos = hd["ContentOffset"]
    for e in rows:
        e["pos"] = pos
        pos += e["FileSize"]
        if pos % ALIGN:
            pos += ALIGN - pos % ALIGN
    return rows


def build_font(raw):
    rows = {e["ID"]: e for e in itoc_rows(raw)}
    results = {}
    for fid, layer in ((10, 1), (11, 2)):
        e = rows[fid]
        stored = raw[e["pos"]:e["pos"] + e["FileSize"]]
        gxt = bytearray(layla(stored))
        off, size = struct.unpack_from("<II", gxt, 0x20)
        atlas = bytearray(gxt[off:off + size])
        for slot, (base, kind) in ACCENTS.items():
            put_tile(atlas, slot, compose(atlas, slot, base, kind, layer))
        gxt[off:off + size] = atlas
        comp, used = layla_compress(bytes(gxt), e["FileSize"])
        check = layla(comp)
        assert check == bytes(gxt), f"layla round-trip failed for {fid}"
        results[fid] = (e, comp, atlas)
        print(f"font file {fid}: stream {used} bytes in {e['FileSize'] - 272} available, front gap {e['FileSize'] - 272 - used}; round-trip OK")
    out = bytearray(raw)
    for fid, (e, comp, _) in results.items():
        assert len(comp) == e["FileSize"]
        out[e["pos"]:e["pos"] + e["FileSize"]] = comp
    return bytes(out), results


