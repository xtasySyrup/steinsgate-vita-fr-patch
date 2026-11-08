"""Translate the labels baked into system.cpk textures, starting from the font build.

Usage: python -I tools/build_ui.py <project root> [sheet ids...]
Reads    build/patch/rePatch/PCSE00644/gamedata/system.cpk (fonts in, from build_patch.py), or the game's with fonts added
Writes   build/assets/system.cpk and previews in build/report/ui/
With sheet ids it only paints and previews those, without fitting them into the archive.
"""
import hashlib, os, struct, sys
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cpk import layla
from sglib import build_font, itoc_rows, layla_compress
import ui_labels, ui_paint

FONT_BUILD_SHA256 = "aeb69d778522243ee0a19ed33bb23fa5496e4f90126e9334f621a74c6db2addc"


def paint(sheet, ops):
    log = []
    for op in ops:
        kind = op[0]
        if kind == "L":
            log.append(ui_paint.label(sheet, op[1], op[2], **op[3]))
        elif kind == "T":
            log.append(ui_paint.text(sheet, op[1], op[2], op[3], **op[4]))
        elif kind == "G":
            log.append(ui_paint.ghost(sheet, op[1], op[2], op[3], op[4], **op[5]))
        elif kind == "W":
            ui_paint.wipe(sheet, op[1], **op[2])
        elif kind == "B":
            ui_paint.blank(sheet, op[1])
    return log


def work(job):
    fid, stored, size, root, fit = job
    sheet = ui_paint.Sheet(layla(stored))
    log = paint(sheet, ui_labels.SHEETS[fid])
    sheet.preview(f"{root}/build/report/ui/{fid:03d}.png")
    if not fit:
        return fid, None, log, "painted"
    gxt = sheet.tobytes()
    try:
        comp, used = layla_compress(gxt, size)
    except OverflowError as e:
        return fid, None, log, f"DOES NOT FIT: {e}"
    if layla(comp) != gxt or len(comp) != size:
        return fid, None, log, "round trip failed"
    return fid, comp, log, f"fits slot {size}, front gap {size - 272 - used}"


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ROOT = sys.argv[1]
    only = [int(x) for x in sys.argv[2:]]
    raw, _ = build_font(open(f"{ROOT}/game/PCSE00644/gamedata/system.cpk", "rb").read())
    if hashlib.sha256(raw).hexdigest() != FONT_BUILD_SHA256:
        raise SystemExit("font build differs from the hardware-tested one")
    rows = {e["ID"]: e for e in itoc_rows(raw)}
    ids = only or sorted(ui_labels.SHEETS)
    jobs = [(i, raw[rows[i]["pos"]:rows[i]["pos"] + rows[i]["FileSize"]], rows[i]["FileSize"], ROOT, not only) for i in ids]
    with Pool(min(len(jobs), max(2, (os.cpu_count() or 4) - 2))) as pool:
        results = pool.map(work, jobs, chunksize=1)
    out = bytearray(raw)
    failed = 0
    for fid, comp, log, status in results:
        print(f"id {fid}: {status}")
        for line in log:
            if "TIGHT" in line or "CLIPPED" in line:
                print("   ", line)
        if comp:
            e = rows[fid]
            out[e["pos"]:e["pos"] + e["FileSize"]] = comp
        elif not only:
            failed += 1
    if only:
        raise SystemExit(0)
    if failed:
        raise SystemExit(f"{failed} sheets did not fit; nothing written")
    untouched = bytearray(out)
    for i in ids:
        e = rows[i]
        untouched[e["pos"]:e["pos"] + e["FileSize"]] = raw[e["pos"]:e["pos"] + e["FileSize"]]
    assert bytes(untouched) == raw, "bytes changed outside the edited slots"
    os.makedirs(f"{ROOT}/build/assets", exist_ok=True)
    open(f"{ROOT}/build/assets/system.cpk", "wb").write(out)
    print("wrote build/assets/system.cpk; only the edited slots differ")
