"""Replace files in a named CPK: copy it, append the new files, edit only their TOC rows.

This is the method that ran on the Vita for script.cpk (plain TOC) and movie.cpk (masked TOC).
"""
import os, shutil, struct, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cpk

SIZES = {0: 1, 1: 1, 2: 2, 3: 2, 4: 4, 5: 4, 6: 8, 7: 8, 8: 4, 9: 8, 0xA: 4, 0xB: 8}
PACK = {2: ">H", 4: ">I", 6: ">Q"}


def replace_by_append(src, out, files):
    """`files` maps a name, as the TOC spells it, to its new bytes (stored uncompressed)."""
    shutil.copyfile(src, out)
    with open(out, "r+b") as f:
        n = struct.unpack_from("<I", f.read(16), 8)[0]
        _, r = cpk.parse_utf(f.read(n))
        toc = r[0]["TocOffset"]
        f.seek(toc)
        nn = struct.unpack_from("<I", f.read(16), 8)[0]
        stored = f.read(nn)
        masked = stored[:4] != b"@UTF"
        b = bytearray(cpk.unmask(stored) if masked else stored)
        rows_off, str_off, _, _, ncol, rowlen, _ = struct.unpack_from(">IIIIHHI", b, 8)
        p, q, field = 32, 0, {}
        for _ in range(ncol):
            fl = b[p]
            ns = 8 + str_off + struct.unpack_from(">I", b, p + 1)[0]
            nm = b[ns:b.index(b"\0", ns)].decode()
            p += 5
            if fl & 0xF0 == 0x30:
                p += SIZES[fl & 0x0F]
            elif fl & 0xF0 == 0x50:
                field[nm] = (q, fl & 0x0F)
                q += SIZES[fl & 0x0F]
        rows = cpk.parse_utf(bytes(b))[1]
        for name, data in files.items():
            idx = next(i for i, x in enumerate(rows) if x["FileName"] == name)
            f.seek(0, 2)
            end = f.tell()
            if end % 2048:
                f.write(bytes(2048 - end % 2048))
            pos = f.tell()
            f.write(data)
            for col, val in (("FileOffset", pos - toc), ("FileSize", len(data)), ("ExtractSize", len(data))):
                o, ty = field[col]
                struct.pack_into(PACK[ty], b, 8 + rows_off + idx * rowlen + o, val)
        f.seek(toc + 16)
        f.write(cpk.unmask(bytes(b)) if masked else bytes(b))
    # Independent read-back.
    a, _, ea = cpk.open_cpk(src)
    c, _, eb = cpk.open_cpk(out)
    same = 0
    for x, y in zip(ea, eb):
        c.seek(y["off"])
        if x["name"] in files:
            assert c.read(y["csize"]) == files[x["name"]], x["name"]
        else:
            a.seek(x["off"])
            assert a.read(x["csize"]) == c.read(y["csize"]) and x["off"] == y["off"], x["name"]
            same += 1
    a.seek(0)
    c.seek(0)
    assert a.read(2048) == c.read(2048), "CPK header changed"
    a.close()
    c.close()
    return same
