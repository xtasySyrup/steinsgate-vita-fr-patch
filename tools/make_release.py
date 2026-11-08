"""Package the release zip: the rePatch folder, with the notice and licence the text's licence requires.

Usage: python -I tools/make_release.py <project root> <version>
Reads    build/patch/rePatch/PCSE00644/gamedata/{script,system}.cpk, release/LISEZMOI.txt, LICENSE
Writes   dist/SteinsGate-Vita-FR-texte-<version>.zip
"""
import os, sys, zipfile

ROOT, VERSION = sys.argv[1], sys.argv[2]
os.makedirs(f"{ROOT}/dist", exist_ok=True)
out = f"{ROOT}/dist/SteinsGate-Vita-FR-texte-{VERSION}.zip"
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for name in ("script.cpk", "system.cpk"):
        path = f"rePatch/PCSE00644/gamedata/{name}"
        z.write(f"{ROOT}/build/patch/{path}", path)
    z.write(f"{ROOT}/release/LISEZMOI.txt", "LISEZMOI.txt")
    z.write(f"{ROOT}/LICENSE", "LICENSE.txt")
print(out, os.path.getsize(out), "bytes")
