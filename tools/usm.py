"""CRI USM rebuilding: swap the H.264 access units, keep everything else in order and byte for byte.

Tables are recomputed from the stream, so feeding back the original access units reproduces the file exactly
(36 of the game's 38 videos; imv043 has a stale size in its table and imv038 has no seek points to find).
"""
import os, struct, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cpk

SIZES = {0: 1, 1: 1, 2: 2, 3: 2, 4: 4, 5: 4, 6: 8, 7: 8, 8: 4, 9: 8, 0xA: 4, 0xB: 8}


def chunks(d):
    p = 0
    out = []
    while p + 8 <= len(d):
        tag = d[p:p + 4]
        size = struct.unpack_from(">I", d, p + 4)[0]
        hdr, pad = struct.unpack_from(">HH", d, p + 8)
        out.append(dict(tag=tag, typ=d[p + 15], hdr=hdr, pad=pad, head=d[p + 8:p + 8 + hdr], body=d[p + 8 + hdr:p + 8 + size - pad]))
        p += 8 + size
    assert p == len(d), (p, len(d))
    return out


def video_units(d):
    return [c["body"] for c in chunks(d) if c["tag"] == b"@SFV" and c["typ"] == 0]


def utf_set(body, row, values):
    """Patch fixed-width per-row integer fields of an unmasked @UTF table."""
    b = bytearray(body)
    _, rows_off, str_off, _, _, ncol, rowlen, _ = struct.unpack_from(">IIIIIHHI", b, 4)
    p = 32
    q = 8 + rows_off + row * rowlen
    seen = set()
    for _ in range(ncol):
        fl = b[p]
        o = struct.unpack_from(">I", b, p + 1)[0]
        nm = b[8 + str_off + o:b.index(0, 8 + str_off + o)].decode()
        p += 5
        st, ty = fl & 0xF0, fl & 0x0F
        if st == 0x30:
            p += SIZES[ty]
        elif st == 0x50:
            if nm in values:
                struct.pack_into(cpk.TYPES[ty], b, q, values[nm])
                seen.add(nm)
            q += SIZES[ty]
    assert seen == set(values), (seen, values)
    return bytes(b)


def is_idr(au):
    i = 0
    while True:
        i = au.find(b"\0\0\1", i)
        if i < 0:
            return False
        t = au[i + 3] & 0x1F
        if t == 5:
            return True
        if t == 1:
            return False
        i += 3


def split_annexb(data):
    """Split an encoder's stream at its access unit delimiters, dropping x264's user-data SEI (the source has none)."""
    starts = []
    i = 0
    while True:
        i = data.find(b"\0\0\1\x09", i)
        if i < 0:
            break
        starts.append(i - 1 if i and data[i - 1] == 0 else i)
        i += 4
    starts.append(len(data))
    return [_strip_user_sei(data[a:b]) for a, b in zip(starts, starts[1:])]


def _strip_user_sei(au):
    nals = []
    i = 0
    while True:
        j = au.find(b"\0\0\1", i)
        if j < 0:
            break
        nals.append(j)
        i = j + 3
    out = bytearray()
    for n, s in enumerate(nals):
        a = s - 1 if s and au[s - 1] == 0 else s
        e = len(au)
        if n + 1 < len(nals):
            e = nals[n + 1]
            e = e - 1 if au[e - 1] == 0 else e
        if au[s + 3] & 0x1F == 6 and au[s + 4] == 5:
            continue
        out += au[a:e]
    return bytes(out)


def remux(orig, new_aus):
    """Rebuild `orig` with `new_aus` in place of its video. Frame count and seek point count must match."""
    cs = chunks(orig)
    vid = [c for c in cs if c["tag"] == b"@SFV" and c["typ"] == 0]
    assert len(new_aus) == len(vid), (len(new_aus), len(vid))
    tables = {}
    for c in cs:
        if c["body"][:4] == b"@UTF":
            nm, rows = cpk.parse_utf(c["body"])
            tables[nm] = rows
    k = pos = 0
    plan, frames = [], []
    for c in cs:
        body, pad = c["body"], c["pad"]
        if c["tag"] == b"@SFV" and c["typ"] == 0:
            body = new_aus[k]
            k += 1
            pad = -(8 + c["hdr"] + len(body)) % 32
            frames.append((pos, body))
        plan.append((c, body, pad))
        pos += 8 + c["hdr"] + len(body) + pad
    total = pos
    idr = [i for i, (_, b) in enumerate(frames) if is_idr(b)]
    info = tables["VIDEO_HDRINFO"][0]
    fps = info["framerate_n"] / info["framerate_d"]
    vbytes = sum(len(b) for _, b in frames)
    maxau = max(len(b) for _, b in frames)
    grow = max(0, maxau - max(len(c["body"]) for c in vid))
    out = bytearray()
    for c, body, pad in plan:
        if body[:4] == b"@UTF":
            nm, rows = cpk.parse_utf(body)
            if nm == "CRIUSF_DIR_STREAM":
                avb = int(vbytes * 8 / (len(frames) / fps))
                body = utf_set(body, 0, {"filesize": total, "avbps": avb + sum(r["avbps"] for r in rows[2:]), "minbuf": rows[0]["minbuf"] + grow})
                body = utf_set(body, 1, {"filesize": vbytes, "minbuf": maxau, "avbps": avb})
            elif nm == "VIDEO_HDRINFO":
                body = utf_set(body, 0, {"ixsize": rows[0]["ixsize"] + grow})
            elif nm == "VIDEO_SEEKINFO":
                assert len(rows) == len(idr), ("seek points", len(rows), len(idr))
                for i, f in enumerate(idr):
                    body = utf_set(body, i, {"ofs_byte": frames[f][0], "ofs_frmid": f})
        out += c["tag"] + struct.pack(">I", c["hdr"] + len(body) + pad) + struct.pack(">HH", c["hdr"], pad) + c["head"][4:] + body + bytes(pad)
    return bytes(out)
