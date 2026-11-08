"""Package the release zip: the rePatch folder, with the notice and licence the text's licence requires.

Usage: python -I tools/make_release.py <project root> <version>
Reads    build/assets/{system,bg,movie}.cpk, script.cpk from build/assets if there is one there or else build/patch,
         release/LISEZMOI.txt, LICENSE
Writes   dist/SteinsGate-Vita-FR-<version>.zip
"""
import os, sys, zipfile

ROOT, VERSION = sys.argv[1], sys.argv[2]
patched = f"{ROOT}/build/patch/rePatch/PCSE00644/gamedata/script.cpk"
script = f"{ROOT}/build/assets/script.cpk"
if not os.path.exists(script):
    script = patched
elif os.path.getmtime(script) < os.path.getmtime(patched):
    raise SystemExit("build/assets/script.cpk is older than build_patch.py's output; rebuild it")
files = {"script.cpk": script, **{f"{n}.cpk": f"{ROOT}/build/assets/{n}.cpk" for n in ("system", "bg", "movie")}}
missing = [p for p in files.values() if not os.path.exists(p)]
if missing:
    raise SystemExit(f"run the build first; missing: {missing}")
os.makedirs(f"{ROOT}/dist", exist_ok=True)
out = f"{ROOT}/dist/SteinsGate-Vita-FR-{VERSION}.zip"
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for name, path in files.items():
        z.write(path, f"rePatch/PCSE00644/gamedata/{name}")
    z.write(f"{ROOT}/release/LISEZMOI.txt", "LISEZMOI.txt")
    z.write(f"{ROOT}/LICENSE", "LICENSE.txt")
print(out, os.path.getsize(out), "bytes")
