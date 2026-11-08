#!/usr/bin/env python3
"""Fabrique le dossier rePatch de la traduction française de Steins;Gate (PS Vita, PCSE00644).

Utilisation : python appliquer_patch.py [dossier gamedata du jeu]

Lit script.cpk et system.cpk de votre copie du jeu, sans jamais les modifier, puis écrit les versions
traduites dans rePatch/PCSE00644/gamedata/, à côté de ce script. Python 3 seul suffit.
"""
import hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def fail(message):
    print(f"\nERREUR : {message}")
    sys.exit(1)


def find_gamedata(path):
    path = path.strip().strip('"')
    for candidate in (path, os.path.join(path, "gamedata")):
        if os.path.isfile(os.path.join(candidate, "script.cpk")) and os.path.isfile(os.path.join(candidate, "system.cpk")):
            return candidate
    fail(f"script.cpk et system.cpk sont introuvables dans : {path}")


def main():
    with open(os.path.join(HERE, "patch", "manifest.json"), encoding="utf-8") as f:
        manifest = json.load(f)
    print(f"Steins;Gate PS Vita : traduction française, {manifest['version']}")
    path = sys.argv[1] if len(sys.argv) > 1 else input("Dossier gamedata du jeu (PCSE00644/gamedata) : ")
    gamedata = find_gamedata(path)
    out_dir = os.path.join(HERE, "rePatch", "PCSE00644", "gamedata")
    results = {}
    for name, info in manifest["files"].items():
        with open(os.path.join(gamedata, name), "rb") as f:
            source = f.read()
        if sha256(source) != info["source_sha256"]:
            fail(f"{name} ne correspond pas à la version attendue du jeu.\n"
                 f"  attendu : {info['source_sha256']}\n  trouvé  : {sha256(source)}\n"
                 "Le fichier est peut-être encore chiffré, ou issu d'une autre version du jeu.")
        with open(os.path.join(HERE, "patch", info["payload"]), "rb") as f:
            payload = f.read()
        target = bytearray(source[:info["target_size"]])
        target.extend(bytes(info["target_size"] - len(target)))
        at = 0
        for offset, length in info["ranges"]:
            target[offset:offset + length] = payload[at:at + length]
            at += length
        if sha256(target) != info["target_sha256"]:
            fail(f"le résultat pour {name} est incorrect ; le patch est peut-être endommagé.")
        results[name] = target
        print(f"  {name} : OK")
    os.makedirs(out_dir, exist_ok=True)
    for name, target in results.items():
        with open(os.path.join(out_dir, name), "wb") as f:
            f.write(target)
    print(f"\nTerminé. Copiez le dossier « rePatch » sur la Vita, à la racine de ux0: :\n  {os.path.join(HERE, 'rePatch')}")


if __name__ == "__main__":
    main()
