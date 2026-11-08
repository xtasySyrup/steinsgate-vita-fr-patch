"""Show the splash image after the company logos: writes build/assets/script.cpk.

Usage: python -I tools/build_splash.py <project root>
Reads    build/patch/rePatch/PCSE00644/gamedata/script.cpk (from build_patch.py)

Offsets in _STARTUP stay where they are. The new code goes at the end of the file, and it borrows three label
slots nothing refers to. The logos' two exits are redirected to it:
- the normal exit jumps to label 23, whose table entry now points at the new code;
- the exit taken when a button skips the CRI logo runs into offset 2292, which becomes a jump to label 23.
The routine copies the PQube logo's, without its two calls to _SYSTEM: those play the logo's voice jingle.
"""
import os, struct, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cpk, cpk_write
from bg_labels import SPLASH_SLOT

STARTUP = "_Startup.scr"
FREE_FADE_IN, FREE_HOLD, FREE_FADE_OUT = 175, 308, 309
EXIT_LABEL, NEXT_LABEL = 23, 24
EXIT_AT = 2292
EXIT_CODE = bytes.fromhex("00 13 a9 60 00 00")  # ResetFlag 0x960, which the new code now does last

# (start, end) of the PQube routine, and the operands to redirect. Each is checked before it is changed.
PQUBE_LOAD = (1822, 1831)
PQUBE_FADE_IN = (1831, 1859)
PQUBE_HOLD = (1873, 1948)
PQUBE_FADE_OUT = (1948, 1993)
PQUBE_BG = 453


def add_splash(d):
    st, rt = struct.unpack_from("<LL", d, 4)
    first = struct.unpack_from("<L", d, 12)[0]
    count = (first - 12) // 4
    labels = list(struct.unpack_from(f"<{count}L", d, 12))
    # Nothing may refer to the borrowed labels, in this script's own code.
    code = d[first:st]
    for lab in (FREE_FADE_IN, FREE_HOLD, FREE_FADE_OUT):
        assert struct.pack("<H", lab) not in code, f"label {lab} is in use"
    assert labels[EXIT_LABEL] == EXIT_AT and d[EXIT_AT:EXIT_AT + 6] == EXIT_CODE
    assert labels[NEXT_LABEL] == EXIT_AT + 6
    assert labels[12] == PQUBE_LOAD[0] and labels[13] == PQUBE_FADE_IN[0] and labels[14] == PQUBE_HOLD[0] and labels[15] == PQUBE_FADE_OUT[0]

    def relabel(block, old, new, expected):
        """Every instruction in these blocks ends in its label, so match that label as the last two operand bytes."""
        raw = struct.pack("<H", old)
        b = bytearray(block)
        found = 0
        i = 0
        while True:
            i = b.find(raw, i)
            if i < 0:
                break
            b[i:i + 2] = struct.pack("<H", new)
            found += 1
            i += 2
        assert found == expected, (old, found, expected)
        return bytes(b)

    load = bytearray(d[PQUBE_LOAD[0]:PQUBE_LOAD[1]])
    assert load[:2] == b"\x10\x01" and load[5:7] == bytes((0xA0 | PQUBE_BG >> 8, PQUBE_BG & 0xFF))
    load[5:7] = bytes((0xA0 | SPLASH_SLOT >> 8, SPLASH_SLOT & 0xFF))
    fade_in = relabel(d[PQUBE_FADE_IN[0]:PQUBE_FADE_IN[1]], 13, FREE_FADE_IN, 1)
    hold = d[PQUBE_HOLD[0]:PQUBE_HOLD[1]]
    hold = relabel(hold, 15, FREE_FADE_OUT, 5)  # five buttons skip to the fade out
    hold = relabel(hold, 14, FREE_HOLD, 1)  # the hold loop
    fade_out = relabel(d[PQUBE_FADE_OUT[0]:PQUBE_FADE_OUT[1]], 15, FREE_FADE_OUT, 1)
    tail = EXIT_CODE + b"\x00\x07" + struct.pack("<H", NEXT_LABEL)

    out = bytearray(d)
    while len(out) % 4:
        out.append(0)
    start = len(out)
    out += load
    labels[FREE_FADE_IN] = len(out)
    out += fade_in
    labels[FREE_HOLD] = len(out)
    out += hold
    labels[FREE_FADE_OUT] = len(out)
    out += fade_out + tail
    labels[EXIT_LABEL] = start
    struct.pack_into(f"<{count}L", out, 12, *labels)
    out[EXIT_AT:EXIT_AT + 4] = b"\x00\x07" + struct.pack("<H", EXIT_LABEL)
    out[EXIT_AT + 4:EXIT_AT + 6] = b"\0\0"  # never reached: label 24 starts right after
    return bytes(out), start


if __name__ == "__main__":
    ROOT = sys.argv[1]
    if not os.path.exists(f"{ROOT}/sources/splash.png"):
        raise SystemExit("sources/splash.png not found; script.cpk from build_patch.py is complete without this step")
    src = f"{ROOT}/build/patch/rePatch/PCSE00644/gamedata/script.cpk"
    f, _, ents = cpk.open_cpk(src)
    e = next(x for x in ents if x["name"] == STARTUP)
    old = cpk.read_entry(f, e)
    f.close()
    new, start = add_splash(old)
    # Read back: only the four label slots, the one redirected jump and the appended code differ.
    n = (struct.unpack_from("<L", old, 12)[0] - 12) // 4
    a, b = struct.unpack_from(f"<{n}L", old, 12), struct.unpack_from(f"<{n}L", new, 12)
    changed = [i for i in range(n) if a[i] != b[i]]
    assert changed == sorted((EXIT_LABEL, FREE_FADE_IN, FREE_HOLD, FREE_FADE_OUT)), changed
    bytes_off = [i for i in range(12 + n * 4, len(old)) if old[i] != new[i]]
    assert bytes_off == [i for i in range(EXIT_AT, EXIT_AT + 6) if old[i] != new[i]], bytes_off[:12]
    assert all(start <= v < len(new) for v in (b[EXIT_LABEL], b[FREE_FADE_IN], b[FREE_HOLD], b[FREE_FADE_OUT]))
    os.makedirs(f"{ROOT}/build/assets", exist_ok=True)
    same = cpk_write.replace_by_append(src, f"{ROOT}/build/assets/script.cpk", {STARTUP: new})
    print(f"_STARTUP {len(old)} -> {len(new)} bytes, splash code at {start}; labels changed: {changed}; other scripts identical: {same}")
    print("new code:", new[start:].hex(" "))
