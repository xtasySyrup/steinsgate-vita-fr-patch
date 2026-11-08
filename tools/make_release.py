"""Package the release zip: byte differences and the patcher, never the game's own files.

Usage: python -I tools/make_release.py <project root> <version>
Reads    game/PCSE00644/gamedata/{script,system}.cpk and build/patch/rePatch/PCSE00644/gamedata/{script,system}.cpk
Writes   dist/SteinsGate-Vita-FR-texte-<version>.zip
"""
import hashlib, json, os, sys, zipfile

ROOT, VERSION = sys.argv[1], sys.argv[2]
GAP = 32  # join differing runs closer than this, so the list of ranges stays short


def diff(a, b):
    n = min(len(a), len(b))
    ranges = []
    i = 0
    while i < n:
        if a[i] == b[i]:
            i += 1
            continue
        j = i
        while j < n and a[j] != b[j]:
            j += 1
        if ranges and i - (ranges[-1][0] + ranges[-1][1]) < GAP:
            ranges[-1][1] = j - ranges[-1][0]
        else:
            ranges.append([i, j - i])
        i = j
    if len(b) > n:
        ranges.append([n, len(b) - n])
    return ranges


manifest = {"version": VERSION, "files": {}}
payloads = {}
for name in ("script.cpk", "system.cpk"):
    a = open(f"{ROOT}/game/PCSE00644/gamedata/{name}", "rb").read()
    b = open(f"{ROOT}/build/patch/rePatch/PCSE00644/gamedata/{name}", "rb").read()
    ranges = diff(a, b)
    payload = name + ".bin"
    payloads[payload] = b"".join(b[o:o + l] for o, l in ranges)
    manifest["files"][name] = {
        "source_sha256": hashlib.sha256(a).hexdigest(), "source_size": len(a),
        "target_sha256": hashlib.sha256(b).hexdigest(), "target_size": len(b),
        "payload": payload, "ranges": ranges,
    }
    print(f"{name}: {len(ranges)} ranges, {len(payloads[payload])} of {len(b)} bytes ({len(payloads[payload]) / len(b):.1%})")

os.makedirs(f"{ROOT}/dist", exist_ok=True)
out = f"{ROOT}/dist/SteinsGate-Vita-FR-texte-{VERSION}.zip"
top = f"SteinsGate-Vita-FR-texte-{VERSION}"
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    z.write(f"{ROOT}/patcher/appliquer_patch.py", f"{top}/appliquer_patch.py")
    z.write(f"{ROOT}/patcher/appliquer_patch.bat", f"{top}/appliquer_patch.bat")
    z.write(f"{ROOT}/patcher/LISEZMOI.txt", f"{top}/LISEZMOI.txt")
    z.write(f"{ROOT}/LICENSE", f"{top}/LICENSE.txt")
    z.writestr(f"{top}/patch/manifest.json", json.dumps(manifest, indent=1))
    for name, data in payloads.items():
        z.writestr(f"{top}/patch/{name}", data)
print(out, os.path.getsize(out), "bytes")
