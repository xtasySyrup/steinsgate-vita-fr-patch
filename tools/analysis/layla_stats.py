"""Compare CRI's CRILAYLA streams with ours: consumption, match stats, in-place margins, plus exhaustive CRC range search."""
import collections, os, re, struct, sys, zlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cpk import parse_utf, unmask

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = sys.argv[1]
orig = open(f"{ROOT}/game/PCSE00644/gamedata/system.cpk", "rb").read()
mine = open(f"{ROOT}/build/archive/B2_script_and_font/rePatch/PCSE00644/gamedata/system.cpk", "rb").read()
exe = open(f"{ROOT}/game/PCSE00644/mai_moe/eboot_origin.bin", "rb").read()


def rows_of(raw):
    n = struct.unpack_from("<I", raw, 8)[0]
    _, r = parse_utf(raw[16:16 + n])
    hd = r[0]
    o = hd["ItocOffset"]
    nn = struct.unpack_from("<I", raw, o + 8)[0]
    _, t = parse_utf(raw[o + 16:o + 16 + nn])
    rows = []
    for key in ("DataL", "DataH"):
        if t[0].get(key):
            rows += parse_utf(t[0][key])[1]
    rows.sort(key=lambda x: x["ID"])
    pos = hd["ContentOffset"]
    for e in rows:
        e["pos"] = pos
        pos += e["FileSize"]
        if pos % 2048:
            pos += 2048 - pos % 2048
    return rows, hd, o, nn


def analyse(d, label):
    usize, csize = struct.unpack_from("<II", d, 8)
    pos = 16 + csize - 1
    w = usize - 1
    bits = nb = 0
    nbits = 0

    def get(n):
        nonlocal bits, nb, pos, nbits
        v = 0
        nbits += n
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

    lens = collections.Counter()
    dist = collections.Counter()
    lits = matches = 0
    maxlen = 0
    margin_left = margin_right = 10**12
    while w >= 0:
        # read-head vs write-head, for in-place layouts
        margin_left = min(margin_left, (0x100 + w) - (pos))          # compressed at start of buffer
        if get(1):
            back = get(13) + 3
            ln = 3
            for n in (2, 3, 5):
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
            matches += 1
            maxlen = max(maxlen, ln)
            lens[min(ln, 300)] += 1
            dist[back] += 1
            w -= ln
        else:
            get(8)
            lits += 1
            w -= 1
    print(f"{label}: usize {usize} csize {csize} ends at pos {pos} (first stream byte index 16) overshoot {w}, leftover bits {nb}")
    print(f"   literals {lits} matches {matches} maxlen {maxlen} min-dist {min(dist)} max-dist {max(dist)} in-place margin {margin_left}")
    print(f"   first bytes of stream area {d[16:32].hex()}  last {d[16 + csize - 8:16 + csize].hex()}")
    print(f"   len>255 matches {sum(n for l, n in lens.items() if l > 255)}; top lens {lens.most_common(5)}")


ro, hd, o, nn = rows_of(orig)
rm = rows_of(mine)[0]
for i in (10, 11):
    analyse(orig[ro[i]["pos"]:ro[i]["pos"] + ro[i]["FileSize"]], f"CRI file {i}")
    analyse(mine[rm[i]["pos"]:rm[i]["pos"] + rm[i]["FileSize"]], f"OUR file {i}")
for i in (0, 8, 39):
    analyse(orig[ro[i]["pos"]:ro[i]["pos"] + ro[i]["FileSize"]], f"CRI file {i}")
print("EnabledDataSize", hd.get("EnabledDataSize"), "EnabledPackedSize", hd.get("EnabledPackedSize"))
for i in (10, 11):
    print(i, "row", {k: v for k, v in ro[i].items()})

print("\ncontext strings near CRC messages:")
for m in re.finditer(rb"[ -~]{8,}", exe[0xF2400:0xF2700]):
    print(f"{0xF2400 + m.start():#08x} {m.group().decode()[:110]}")

# Exhaustive zlib-CRC range search: does any (start,end) inside the ITOC or file give the stored CRC?
ib = orig[o:o + hd["ItocSize"]]
plain = bytearray(ib)
plain[16:16 + nn] = unmask(bytes(ib[16:16 + nn]))
target = hd["ItocCrc"]
for name, buf in (("itoc raw", ib), ("itoc plain", bytes(plain))):
    for start in range(0, 40):
        c0 = 0
        crc = 0
        for end in range(start, len(buf)):
            crc = zlib.crc32(buf[end:end + 1], crc)
            if crc == target:
                print(f"ITOC CRC MATCH {name} [{start}:{end + 1}]")
e = ro[57]
s = orig[e["pos"]:e["pos"] + e["FileSize"]]
for start in range(0, 64):
    crc = 0
    for end in range(start, len(s)):
        crc = zlib.crc32(s[end:end + 1], crc)
        if crc == e["CRC"]:
            print(f"file57 CRC MATCH [{start}:{end + 1}]")
print("search done")
