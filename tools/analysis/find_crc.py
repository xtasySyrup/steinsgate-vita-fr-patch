"""Locate CRC tables and CRC/CPK strings in the plain-text game executable (read-only)."""
import re, struct, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
exe = open(sys.argv[1], "rb").read()
print("exe size", len(exe))

# A 256-entry CRC table is linear: t[0]=0 and t[a^b]=t[a]^t[b]. Test all 4-byte alignments for u32 and u16.
found = []
for o in range(0, len(exe) - 1024, 4):
    if exe[o:o + 4] != b"\0\0\0\0":
        continue
    for end in ("<", ">"):
        t = struct.unpack_from(end + "256I", exe, o)
        if len(set(t)) < 250:
            continue
        if t[1] ^ t[2] == t[3] and t[4] ^ t[8] == t[12] and t[16] ^ t[32] == t[48] and t[128] ^ t[1] == t[129]:
            found.append((o, end, t))
            print(f"u32 table at {o:#x} endian {end} t[1]={t[1]:#010x} t[128]={t[128]:#010x} t[255]={t[255]:#010x}")
for o in range(0, len(exe) - 512, 2):
    if exe[o:o + 2] != b"\0\0":
        continue
    t = struct.unpack_from("<256H", exe, o)
    if len(set(t)) > 250 and t[1] ^ t[2] == t[3] and t[4] ^ t[8] == t[12] and t[16] ^ t[32] == t[48] and t[128] ^ t[1] == t[129]:
        print(f"u16 table at {o:#x} t[1]={t[1]:#06x} t[128]={t[128]:#06x}")

print("\nstrings mentioning crc/cpk/check/cri:")
seen = 0
for m in re.finditer(rb"[ -~]{6,}", exe):
    s = m.group()
    if re.search(rb"crc|cpk|checksum|CRILAYLA|CRC|layla|verif", s, re.I):
        print(f"{m.start():#08x} {s.decode()[:150]}")
        seen += 1
        if seen > 70:
            break
