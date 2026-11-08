"""Minimal read-only CRI CPK reader (@UTF tables, TOC/ITOC, CRILAYLA)."""
import os, struct, sys

TYPES = {0: ">B", 1: ">b", 2: ">H", 3: ">h", 4: ">I", 5: ">i", 6: ">Q", 7: ">q", 8: ">f", 9: ">d"}


def unmask(b):
    out = bytearray(len(b))
    m = 0x655F
    for i, c in enumerate(b):
        out[i] = c ^ (m & 0xFF)
        m = (m * 0x4115) & 0xFFFFFFFF
    return bytes(out)


def parse_utf(b):
    if b[:4] != b"@UTF":
        b = unmask(b)
    assert b[:4] == b"@UTF", b[:8]
    size, rows_off, str_off, data_off, name_off, ncol, rowlen, nrow = struct.unpack_from(">IIIIIHHI", b, 4)
    base = 8

    def s(o):
        p = base + str_off + o
        return b[p:b.index(b"\0", p)].decode("utf-8", "replace")

    def read(p, t):
        if t in TYPES:
            f = TYPES[t]
            return struct.unpack_from(f, b, p)[0], p + struct.calcsize(f)
        if t == 0xA:
            return s(struct.unpack_from(">I", b, p)[0]), p + 4
        if t == 0xB:
            o, n = struct.unpack_from(">II", b, p)
            return b[base + data_off + o:base + data_off + o + n], p + 8
        raise ValueError(t)

    p = 32
    cols = []
    for _ in range(ncol):
        fl = b[p]
        nm = s(struct.unpack_from(">I", b, p + 1)[0])
        p += 5
        st, ty = fl & 0xF0, fl & 0x0F
        val = None
        if st == 0x30:
            val, p = read(p, ty)
        cols.append((nm, st, ty, val))
    rows = []
    for r in range(nrow):
        q = base + rows_off + r * rowlen
        row = {}
        for nm, st, ty, val in cols:
            if st == 0x50:
                row[nm], q = read(q, ty)
            elif st == 0x30:
                row[nm] = val
            else:
                row[nm] = None
        rows.append(row)
    return s(name_off), rows


def layla(d):
    assert d[:8] == b"CRILAYLA"
    usize, hsize = struct.unpack_from("<II", d, 8)
    prefix = d[16 + hsize:16 + hsize + 0x100]
    out = bytearray(usize)
    w = usize - 1
    pos = 16 + hsize - 1
    bits = 0
    nb = 0

    def get(n):
        nonlocal bits, nb, pos
        v = 0
        while n:
            if nb == 0:
                bits = d[pos]
                pos -= 1
                nb = 8
            take = min(n, nb)
            v = (v << take) | ((bits >> (nb - take)) & ((1 << take) - 1))
            nb -= take
            n -= take
        return v

    # Output is written backwards; high `usize` bytes come from the bitstream.
    while w >= 0:
        if get(1):
            back = get(13) + 3
            ln = 3
            for lvl, n in enumerate((2, 3, 5)):
                v = get(n)
                ln += v
                if v != (1 << n) - 1:
                    break
            else:
                while True:
                    v = get(8)
                    ln += v
                    if v != 0xFF:
                        break
            for _ in range(ln):
                if w < 0:
                    break
                out[w] = out[w + back]
                w -= 1
        else:
            out[w] = get(8)
            w -= 1
    return bytes(prefix) + bytes(out)


def open_cpk(path):
    f = open(path, "rb")
    h = f.read(16)
    assert h[:4] == b"CPK ", h
    n = struct.unpack_from("<I", h, 8)[0]
    _, rows = parse_utf(f.read(n))
    head = rows[0]
    toc = head.get("TocOffset")
    content = head.get("ContentOffset") or 0
    entries = []
    if toc:
        f.seek(toc)
        hh = f.read(16)
        assert hh[:4] == b"TOC ", hh
        nn = struct.unpack_from("<I", hh, 8)[0]
        _, t = parse_utf(f.read(nn))
        base = min(toc, content) if content else toc
        for r in t:
            name = (r.get("DirName") or "") + "/" + r["FileName"] if r.get("DirName") else r["FileName"]
            entries.append(dict(name=name, off=r["FileOffset"] + base, csize=r["FileSize"], usize=r["ExtractSize"], id=r.get("ID")))
    return f, head, entries


def read_entry(f, e):
    f.seek(e["off"])
    d = f.read(e["csize"])
    if d[:8] == b"CRILAYLA":
        d = layla(d)
    return d


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    src, dest = sys.argv[1], sys.argv[2]
    os.makedirs(dest, exist_ok=True)
    f, head, ents = open_cpk(src)
    print(os.path.basename(src), "files", len(ents), {k: head[k] for k in ("ContentOffset", "TocOffset", "ItocOffset", "Align", "CpkMode", "Tvers") if k in head})
    comp = sum(1 for e in ents if e["csize"] != e["usize"])
    print("compressed entries", comp)
    for e in ents:
        d = read_entry(f, e)
        if len(d) != e["usize"]:
            print("SIZE MISMATCH", e["name"], len(d), e["usize"])
        p = os.path.join(dest, e["name"])
        os.makedirs(os.path.dirname(p) or dest, exist_ok=True)
        open(p, "wb").write(d)
    for e in ents[:40]:
        print(f'{e["id"]!s:>6} {e["csize"]:>10} {e["usize"]:>10} {e["name"]}')
