"""Build the French patch for Steins;Gate Vita (PCSE00644).

Usage: python -I tools/build_patch.py <project root> [--scenes SG00_01 SG01_01 ...]

Reads    game/PCSE00644/gamedata/{script,system}.cpk, game/PCSE00644/mai_moe/eboot_origin.bin, sources/sg-fr-patch/script.mpk
Writes   build/patch/rePatch/PCSE00644/gamedata/{script,system}.cpk
         build/report/overflow.tsv and build/report/structure.tsv
The game dump is never modified.
"""
import collections, hashlib, os, struct, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cpk import layla, parse_utf
from sglib import ACCENTS, build_font

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = sys.argv[1]
ONLY = [s.upper() for s in sys.argv[sys.argv.index("--scenes") + 1:]] if "--scenes" in sys.argv else None
GAME = f"{ROOT}/game/PCSE00644/gamedata"
ALIGN = 2048

# ZZZ is a debug menu.
SKIP = {"ZZZ"}
# The Vita shows these with the fixed-width font row, so Latin stays in slots 1-62.
MONO = {"_ATCH", "_MAIL", "CLRFLG", "MACROSYS2"}
# These mix both rows, so each string follows the row its Vita English uses.
MIXED = {"_SYSTEM", "_TIPS", "_STARTUP"}
# _SYSTEM strings 0 and 1 list the characters that may not start or end a line. The Steam script lists the apostrophe
# in both and the space in the first; the Vita's don't, which on hardware left "l’" at line ends and leading spaces.
# The engine only keeps slots 128-189 together as words, so accented letters must be listed too ("d’é / quipe").
# The hyphen may end a line, as is normal in French, but not start one.
RULE_EXTRA = {"_SYSTEM": {0: [201, 63, 66] + list(ACCENTS), 1: [201] + list(ACCENTS)}}
# TIPS pages hold 10 lines. These entries overflow in French but have room on another page, so whole sentences move
# between their pages, in order and word for word. Each value is the Vita string range of the entry's pages.
TIPS_REFLOW = [(208, 210), (696, 700), (719, 723), (862, 864)]
TIPS_WRAP, TIPS_LINES = 845, 10  # wrap width fitted to a 12-line hardware photo of string 699
# One Vita English sentence is split over two strings where the Steam script has one.
SPLITS = {"SG02_03": 206}

# ---------------------------------------------------------------- character tables
# Common to both styles: fullwidth, kana, kanji and symbols, read from the labelled Vita font sheets.
COMMON = {c: c for c in range(128, 277)}
COMMON.update({c: c for c in ACCENTS})
COMMON.update({
    277: 517, 278: 500, 351: 524, 364: 529, 368: 528, 369: 532, 372: 537, 373: 527, 385: 526, 391: 794, 394: 531,
    396: 66, 404: 535, 405: 533, 410: 518, 417: 505, 418: 514, 419: 511, 421: 498, 422: 499, 427: 519, 429: 520,
    432: 534, 454: 521, 458: 523, 460: 534, 473: 230,
    496: 370, 541: 415, 553: 427, 569: 443, 584: 458, 589: 463, 599: 473, 606: 480, 617: 491, 623: 496,
    700: 613, 750: 554, 753: 630, 754: 631, 755: 632, 1181: 655, 1182: 656, 1183: 657, 1184: 658, 1185: 659,
    2837: 522, 2882: 530, 2894: 525, 3660: 217,
})
# Proportional text (story): Latin moves to slots 128-189, punctuation to the Vita English slots.
PROP = dict(COMMON)
PROP.update({0: 63, 63: 63, 7394: 178})
PROP.update({c: c + 127 for c in range(1, 63)})
PROP.update({64: 64, 65: 194, 66: 66, 67: 195, 68: 197, 69: 196, 70: 201, 71: 193, 72: 72, 73: 73, 74: 274, 75: 228,
             76: 76, 77: 505, 78: 78, 79: 204, 80: 205, 81: 199, 82: 82, 83: 223, 84: 84, 85: 222, 86: 90, 87: 226,
             88: 88, 89: 93, 90: 516, 91: 70, 92: 192, 93: 208, 94: 531, 95: 209, 96: 77, 97: 210, 99: 211})
# Fixed-width text (mail, attachments): Latin stays put, the punctuation row has its own Vita order.
FIXED = dict(COMMON)
FIXED.update({0: 63, 63: 63, 7394: 51})
FIXED.update({c: c for c in range(1, 63)})
FIXED.update({c: c for c in (64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 76, 78, 79, 80, 81, 82, 83, 84, 88)})
FIXED.update({75: 78, 77: 505, 85: 91, 86: 90, 87: 226, 89: 93, 90: 516, 91: 70, 92: 75, 93: 95, 94: 531, 95: 96, 96: 77, 97: 210, 99: 94})
# On the phone any slot from 128 up advances a full 32 units whatever the width table says. Steam's apostrophe is
# code 201, measured 32 in a hardware photo; slot 70 advances 17 and is what the Vita English uses.
FIXED[201] = 70
# Mail and attachments use one straight double quote from the fixed row, like the Vita English.
PHONE = dict(FIXED)
PHONE.update({202: 93, 203: 93})
FIXED[510] = 510  # the box character framing a _STARTUP heading

# Phone and HUD text rewritten to fit, measured from hardware photos at 17 units per letter, 12 per space:
# status frame about 153, pop-up about 308, HUD about 313, menu list about 360, description about 388.
# Inbox and outbox titles stay within the English 267: longer text runs into something drawn at the title's right.
# The phone wraps in the middle of words, so longer strings get explicit breaks ({n}).
UI_TEXT = {"_MAIL": {
    0: "Messages reçus",
    1: "Messages envoyés",
    4: "Fond d’écran",
    7: "Vibration d’appel",
    8: "Vibration de message",
    9: "Nouveau message.",
    13: "Appel...",
    14: "Envoi...",
    15: "Appel...",
    20: "Nouveau message.",
    34: "Sonnerie{n}d’appel{n}modifiée.",
    42: "Voir les messages{n}reçus",
    43: "Voir les messages{n}envoyés",
    45: "Changer le{n}fond d’écran.",
    46: "Changer la sonnerie{n}d’appel.",
    47: "Changer la sonnerie{n}de message.",
    48: "Modifie la vibration{n}pour les appels.",
    49: "Modifie la vibration{n}pour les messages.",
    51: "Sonnerie{n}de message{n}modifiée.",
    52: "Vibration{n}d’appel{n}modifiée.",
    53: "Vibration{n}de message{n}modifiée.",
    75: "Fond d’écran{n}modifié.",
    80: "Nouveau message",
}, "_TIPS": {
    # PTSD, the one page shortened to fit. By the user's choice, other long TIPS pages stay as translated.
    817: "Abréviation de “post-traumatic stress disorder” (trouble de stress post-traumatique). D’après le DSM-IV (quatrième édition du Manuel diagnostique et statistique des troubles mentaux, American Psychiatric Association, 1994) : un trouble mental provoquant divers symptômes de stress, causé par le choc d’un accident, d’une catastrophe ou d’un crime. Symptômes : instabilité émotionnelle, insomnie, confusion et souvenirs intrusifs. Le diagnostic est posé s’ils persistent plus d’un mois.",
}, "_SYSTEM": {
    2: "Données corrompues",
    3: "Pas de données",
    4: "Durée :",
    5: "Date :",
    9: "Temps total",
    18: "Fin atteinte",
    19: "TIPS acquis",
    20: "Complétion de l’album",
    21: "Nouveau",
    22: "Non lu",
    23: "Trophée caché",
    25: "Trophées",
    26: "Trophées",
    64: "Vidéo promo ver.[A.R.]",
}, "MACROSYS": {
    2: "Prologue",
    3: "Chapitre 1  Paranoïa du Voyage Temporel",
    4: "Chapitre 2  Rendez-vous de l’Interprète",
    5: "Chapitre 3  Divergence de l’Effet Papillon",
    6: "Chapitre 4  Homéostasie de la Théorie du Chaos",
    7: "Chapitre 5  Dogme dans l’Horizon des Événements",
    8: "Chapitre 6  Nécrose Métaphysique",
    9: "Chapitre 7  Made in Complex",
    10: "Chapitre 8  Androgyne Fractal",
    11: "Chapitre 9  Apoptose sans Fin",
    12: "Chapitre 10  Fusion du Paradoxe",
    13: "Chapitre 10  Ciel de Poussière d’Étoiles",
    14: "Chapitre 11  Ouvrir le Steins Gate",
}}

# _STARTUP dialogs, keyed on the Vita English because the Steam script lists different messages.
# The Japanese strings 0-7 stay as they are.
_TO_TITLE = "Retourner au menu principal ?"
_NO_OFF = "Veuillez ne pas éteindre le système ni fermer l’application."
_RETRY = "Veuillez quitter le jeu et réessayer."
_SAVE_SYS = "Sauvegarder les données système ?"
_LOAD_SYS = "Chargement des données système."
STARTUP_TEXT = {
    "   ■■■■■ About QUICK SAVE ■■■■■": "   ■■■■■ SAUVEGARDE RAPIDE ■■■■■",
    'Progress will be lost if you do not select "SAVE"': "Sans “SAUVEGARDER” dans le menu système",
    'from the system menu or "SYSTEM SAVE",': "ou “SAUVEGARDE SYSTÈME” lors du retour",
    "when prompted, upon returning to the title screen.": "à l’écran titre, la progression sera perdue.",
    "All unsaved game progress will be lost.": "Toute progression non sauvegardée sera perdue.",
    "Return to Title Menu?": _TO_TITLE,
    "Yes": "Oui",
    "No": "Non",
    "Return to Default Settings?": "Rétablir les paramètres par défaut ?",
    "Returned to Default Settings.": "Paramètres par défaut rétablis.",
    "Load this data?": "Charger ces données ?",
    "Load": "Charger",
    "Don't load": "Ne pas charger",
    "All Save Data are locked.": "Toutes les sauvegardes sont verrouillées.",
    "If all save data will be locked, you can not select the QUICK SAVE.": "Si toutes sont verrouillées, la SAUVEGARDE RAPIDE est indisponible.",
    "If you would like to select QUICK SAVE,": "Pour utiliser la SAUVEGARDE RAPIDE,",
    "please unlock the unnecessary Save Data.": "veuillez déverrouiller les sauvegardes inutiles.",
    "The locked status of the Save Data has changed.": "Le verrouillage de la sauvegarde a changé.",
    "Save System Data?": _SAVE_SYS,
    "If you do not save the System Data, you may lose the changed settings.": "Sans cela, les paramètres modifiés pourraient être perdus.",
    "Save Data already exists.": "Une sauvegarde existe déjà.",
    "If you choose to overwrite this data, the previous save will be lost.": "Si vous l’écrasez, la sauvegarde précédente sera perdue.",
    "Overwrite the Save Data?": "Écraser la sauvegarde ?",
    "Overwrite": "Écraser",
    "Cancel": "Annuler",
    "This Save Data is locked.": "Cette sauvegarde est verrouillée.",
    "If you would like to overwrite the Save Data, please unlock it.": "Pour l’écraser, veuillez d’abord la déverrouiller.",
    "There exists the corrupted Save Data.": "Une sauvegarde corrompue a été détectée.",
    "Overwrite to the corrupted Save Data?": "Écraser la sauvegarde corrompue ?",
    "Saving data.": "Sauvegarde en cours.",
    "Please do not turn off the system or close the application.": _NO_OFF,
    "It failed to save Play Data.": "Échec de la sauvegarde.",
    "Save again?": "Réessayer ?",
    "Checking Trophy Data.": "Vérification des données de trophées.",
    "There is not enough available space on the storage.": "Espace de stockage insuffisant.",
    "To Trophy Data, at least {v} KB more space is required.": "Au moins {v} Ko de plus sont requis pour les trophées.",
    "Please exit the game and obtain the necessary space.": "Veuillez quitter le jeu et libérer l’espace nécessaire.",
    "It failed to load Trophy Data.": "Échec du chargement des données de trophées.",
    "Please exit the game and retry.": _RETRY,
    "Checking System Data.": "Vérification des données système.",
    "Loading System Data.": _LOAD_SYS,
    "System Data could not find.": "Données système introuvables.",
    "System Data are created.": "Données système créées.",
    "Creating System Data.": "Création des données système.",
    "System Data is corrupted.": "Les données système sont corrompues.",
    "System Data are repaired.": "Données système réparées.",
    "Repairing System Data.": "Réparation des données système.",
    "This System Data is another user's data.": "Ces données système appartiennent à un autre utilisateur.",
    "You cannot earn trophies in this application.": "Vous ne pouvez pas obtenir de trophées ici.",
    "It is overwritten when System Data is saved next time.": "Elles seront écrasées à la prochaine sauvegarde système.",
    "(The previous save file will be lost.)": "(La sauvegarde précédente sera perdue.)",
    "It failed to load System Data.": "Échec du chargement des données système.",
    "It failed to create System Data.": "Échec de la création des données système.",
    "System Data already exists.": "Des données système existent déjà.",
    "Overwrite this Data?": "Écraser ces données ?",
    "Saving System Data.": "Sauvegarde des données système.",
    "It failed to save System Data.": "Échec de la sauvegarde des données système.",
}

UI_CODE = {
    "à": 100, "â": 101, "ä": 102, "ç": 103, "è": 104, "é": 105, "ê": 106, "ë": 107, "î": 108, "ï": 109, "ô": 110, "ö": 111,
    "ù": 112, "û": 113, "ü": 114, "œ": 115, "À": 117, "Â": 118, "Ç": 119, "È": 120, "É": 121, "Ê": 122, "Œ": 126,
    " ": 63, "’": 201, ".": 71, ":": 65, "-": 66, "!": 68, "?": 69, "/": 64, "(": 79, ")": 80, "[": 93, "]": 95,
    ",": 192, "“": 202, "”": 203, "■": 510,
}


def ui_tokens(text):
    """Turn hand-written French into tokens in the Steam code space, ready for the character tables."""
    out = []
    i = 0
    while i < len(text):
        if text.startswith("{n}", i):
            out.append((0, b""))
            i += 3
            continue
        if text.startswith("{v}", i):  # the value placeholder; reconcile() copies its payload from the Vita string
            out.append((0x13, b""))
            i += 3
            continue
        ch = text[i]
        i += 1
        if ch in UI_CODE:
            out.append(UI_CODE[ch])
        elif ch.isascii() and ch.isdigit():
            out.append(1 + int(ch))
        elif ch.isascii() and ch.isalpha():
            out.append((11 if ch.isupper() else 37) + ord(ch.lower()) - 97)
        else:
            raise ValueError(f"no code for {ch!r} in {text!r}")
    return out


VITA_TEXT = {0: " ", 63: " ", 64: "/", 65: ":", 66: "-", 68: "!", 69: "?", 70: "'", 71: ".", 79: "(", 80: ")", 192: ",", 202: '"', 203: '"', 510: "■"}


def vita_text(toks):
    """Readable text of a fixed-row Vita string, or None if it holds anything else (Japanese, other controls)."""
    out = []
    for x in toks:
        if not isinstance(x, int):
            if x[0] != 0x13:
                return None
            out.append("{v}")
        elif 1 <= x <= 10:
            out.append(str(x - 1))
        elif 11 <= x <= 36:
            out.append(chr(65 + x - 11))
        elif 37 <= x <= 62:
            out.append(chr(97 + x - 37))
        elif x in VITA_TEXT:
            out.append(VITA_TEXT[x])
        else:
            return None
    return "".join(out)


WIDTHS = open(f"{ROOT}/game/PCSE00644/mai_moe/eboot_origin.bin", "rb").read()[0x1061E0:0x1061E0 + 836]


def aligned_french(name, en, steam_list):
    """French tokens per Vita string. None keeps the Vita string as it is."""
    n = len(en)
    if name == "_TIPS":
        # Vita 11 onward is Steam 34 onward (972 strings each). The rest is headers and sort tables.
        fr = [None] * n
        for k in (0, 1, 2, 6, 8):
            fr[k] = steam_list[k]
        for k in range(11, n):
            fr[k] = steam_list[k + 23]
        for a, b in TIPS_REFLOW:
            before = [tips_lines(fr[k]) for k in range(a, b)]
            fr[a:b] = reflow_pages(fr[a:b])
            print(f"TIPS {a}-{b - 1} lines {before} -> {[tips_lines(fr[k]) for k in range(a, b)]}")
        long_pages = [k for k in range(11, n) if tips_lines(fr[k]) > TIPS_LINES]
        print("TIPS pages estimated over", TIPS_LINES, "lines:", long_pages)
    elif name == "_SYSTEM":
        # Strings 0 and 1 are line-break rules. Song titles and timings stay as they are.
        fr = [None] * n
        fr[8] = steam_list[11]
        for k in range(28, 53):  # chapter titles
            fr[k] = steam_list[k + 80]
        for k in range(55, 64):  # scene and ending names
            fr[k] = steam_list[k + 79]
        for k, s in ((65, 145), (66, 146), (67, 147), (69, 149)):
            fr[k] = steam_list[s]
        for k in range(71, n):  # same width as the English credit words
            text = vita_text(en[k])
            if text and any(w in text for w in ("Composer", "Writer", "Vocals")):
                fr[k] = ui_tokens(text.replace("Vocals", "Chant").replace("Writer", "Paroles").replace("Composer", "Musique"))
    elif name == "_STARTUP":
        fr = [None] * n
        for k in range(8, n):
            text = vita_text(en[k])
            if text is None:
                raise ValueError(f"_STARTUP {k}: cannot read {en[k]!r}")
            if not text.strip():
                continue
            if text not in STARTUP_TEXT:
                raise ValueError(f"_STARTUP {k}: no French for {text!r}")
            fr[k] = ui_tokens(STARTUP_TEXT[text])
    else:
        fr = list(steam_list)
    return fr


def tips_lines(toks):
    """Lines a TIPS page takes, by word wrap at spaces. An estimate: it matched the photo's total, not every break."""
    lines, x, word = 1, 0, 0
    for t in toks:
        if not isinstance(t, int):
            if t[0] == 0:
                lines += 1
                x = word = 0
            continue
        c = PROP.get(t, 63)
        if c == 63:
            if x and x + WIDTHS[63] + word > TIPS_WRAP:
                lines += 1
                x = word
            else:
                x += (WIDTHS[63] if x else 0) + word
            word = 0
        else:
            word += WIDTHS[c]
    if x and x + WIDTHS[63] + word > TIPS_WRAP:
        lines += 1
    return lines


def reflow_pages(pages):
    """Split pages into sentences and redistribute them in order, keeping the fullest page as short as possible."""
    sentences = []
    for page in pages:
        cur = []
        for i, t in enumerate(page):
            cur.append(t)
            nxt = page[i + 1] if i + 1 < len(page) else None
            if t in (71, 68, 69) and nxt in (0, 63):
                sentences.append(cur)
                cur = []
        if cur:
            sentences.append(cur)
    sentences = [[t for j, t in enumerate(s) if not (j == 0 and t in (0, 63))] for s in sentences]

    def join(part):
        out = []
        for s in part:
            if out:
                out.append(63)
            out += s
        return out

    n, m = len(pages), len(sentences)
    best = {}

    def solve(p, start):
        """Smallest (fullest page, moved-away total) for sentences[start:] over pages p.. ; returns cuts."""
        if (p, start) in best:
            return best[(p, start)]
        if p == n - 1:
            res = (tips_lines(join(sentences[start:])), ())
        else:
            res = None
            for end in range(start + 1, m - (n - p - 1) + 1):
                here = tips_lines(join(sentences[start:end]))
                sub, cuts = solve(p + 1, end)
                cand = (max(here, sub), (end,) + cuts)
                if res is None or cand[0] < res[0]:
                    res = cand
        best[(p, start)] = res
        return res

    _, cuts = solve(0, 0)
    bounds = (0,) + cuts + (m,)
    return [join(sentences[bounds[i]:bounds[i + 1]]) for i in range(n)]


def table_for(name, en_string):
    if name in ("_MAIL", "_ATCH"):
        return PHONE
    if name in MONO:
        return FIXED
    if name in MIXED:
        return PROP if any(isinstance(x, int) and 128 <= x <= 189 for x in en_string) else FIXED
    return PROP


# ---------------------------------------------------------------- SC3 strings
def expr_end(b, i):
    while True:
        c = b[i]
        if c == 0:
            return i + 1
        i += ((c & 0xE0) - 0x80) // 0x20 + 2 if c >= 0x80 else 2


def expr_val(e):
    c = e[0]
    n = ((c & 0xE0) - 0x80) // 0x20 + 1
    return (c & 0x1F) if n == 1 else int.from_bytes(e[1:n], "little")


def parse(b, i, vita):
    """Return tokens: int = character code, (op, payload) = control code. Colour payload is one Vita byte."""
    toks = []
    while b[i] != 0xFF:
        c = b[i]
        if c >= 0x80:
            toks.append((c << 8 | b[i + 1]) & 0x7FFF)
            i += 2
            continue
        i += 1
        if c == 4:
            if vita:
                toks.append((4, bytes((b[i],))))
                i += 1
            else:
                e = expr_end(b, i)
                toks.append((4, bytes((expr_val(b[i:e]) & 0xFF,))))
                i = e
        elif c == 0x15:
            e = expr_end(b, i)
            toks.append((c, bytes(b[i:e])))
            i = e
        elif c in (0xC, 0x11, 0x12, 0x13):
            toks.append((c, bytes(b[i:i + 2])))
            i += 2
        else:
            toks.append((c, b""))
    return toks, i


def strings(d, vita):
    st, rt = struct.unpack_from("<LL", d, 4)
    return [parse(d, struct.unpack_from("<L", d, st + 4 * k)[0], vita)[0] for k in range((rt - st) // 4)]


def opseq(t):
    return [x[0] for x in t if not isinstance(x, int)]


def reconcile(fr, en):
    """Make the French control codes follow the Vita string. Returns tokens and whether they now match."""
    if opseq(fr) != opseq(en):
        if not {0x11, 0x12} & set(opseq(en)):  # Steam-only positioning has no meaning on the Vita layout
            fr = [x for x in fr if isinstance(x, int) or x[0] not in (0x11, 0x12)]
        en_named = opseq(en)[:2] == [1, 2]
        fr_named = opseq(fr)[:2] == [1, 2]
        if en_named and not fr_named:  # Vita shows a name box here, including empty names
            prefix = en[:en.index((2, b"")) + 1]
            fr = prefix + fr
        elif fr_named and not en_named:
            fr = fr[fr.index((2, b"")) + 1:]
        en_ops, fr_ops = opseq(en), opseq(fr)
        if en_ops[-1:] == [3] and fr_ops[-1:] != [3]:  # "wait for button" at the end of the line
            fr = fr + [(3, b"")]
        elif fr_ops[-1:] == [3] and en_ops[-1:] != [3]:
            fr = fr[:-1]
    if opseq(fr) == opseq(en):  # same structure: positions and margins must be the Vita's
        payloads = iter([x for x in en if not isinstance(x, int)])
        fr = [x if isinstance(x, int) else next(payloads) for x in fr]
        return fr, True
    return fr, False


def split_tokens(fr, en_a, en_b):
    """Divide one French string over two Vita strings, at the word break nearest the English ratio."""
    text = [i for i, x in enumerate(fr) if isinstance(x, int)]
    spaces = [i for i in text if fr[i] in (0, 63)]
    la = sum(isinstance(x, int) for x in en_a)
    lb = sum(isinstance(x, int) for x in en_b)
    want = text[int(len(text) * la / (la + lb))]
    cut = min(spaces, key=lambda i: abs(i - want))
    return fr[:cut], fr[cut + 1:]


def encode(toks, table, missing):
    out = bytearray()
    for x in toks:
        if isinstance(x, int):
            v = table.get(x)
            if v is None:
                missing[x] += 1
                v = 63
            out += struct.pack(">H", 0x8000 | v)
        else:
            out.append(x[0])
            out += x[1]
    out.append(0xFF)
    return bytes(out)


def convert_scene(name, vita, steam, report):
    st, rt = struct.unpack_from("<LL", vita, 4)
    n = (rt - st) // 4
    off = [struct.unpack_from("<L", vita, st + 4 * k)[0] for k in range(n)]
    if off[0] != rt:
        raise ValueError(f"{name}: string data does not start at {rt:#x}")
    en = strings(vita, True)
    fr = strings(steam, False)
    if name in SPLITS:
        k = SPLITS[name]
        a, b = split_tokens(fr[k], en[k], en[k + 1])
        fr = fr[:k] + [a, b] + fr[k + 1:]
    fr = aligned_french(name, en, fr)
    if len(fr) != n:
        raise ValueError(f"{name}: {n} Vita vs {len(fr)} Steam strings")
    for k, text in UI_TEXT.get(name, {}).items():
        fr[k] = ui_tokens(text)
    table = table_for(name, en[0])
    missing = collections.Counter()
    body = bytearray()
    new_off = []
    final = []
    for k in range(n):
        new_off.append(rt + len(body))
        if fr[k] is None:  # kept as the Vita string
            final.append(en[k])
            raw = vita[off[k]:parse(vita, off[k], True)[1]]
            for c in RULE_EXTRA.get(name, {}).get(k, []):
                raw += struct.pack(">H", 0x8000 | c)
            body += raw + b"\xff"
            continue
        toks, same = reconcile(fr[k], en[k])
        if not same:
            report["structure"].append((name, k, opseq(en[k]), opseq(toks)))
        final.append(toks)
        body += encode(toks, table_for(name, en[k]), missing)
    tail = vita[parse(vita, off[-1], True)[1] + 1:]
    out = bytearray(vita[:rt]) + body + tail
    for k, o in enumerate(new_off):
        struct.pack_into("<L", out, st + 4 * k, o)
    if missing:
        report["missing"][name] = missing
    return bytes(out), final, en, table


# ---------------------------------------------------------------- script.cpk
def toc_layout(raw):
    head_n = struct.unpack_from("<I", raw, 8)[0]
    _, r = parse_utf(raw[16:16 + head_n])
    toc = r[0]["TocOffset"]
    nn = struct.unpack_from("<I", raw, toc + 8)[0]
    utf_at = toc + 16
    b = raw[utf_at:utf_at + nn]
    if b[:4] != b"@UTF":
        raise ValueError("script.cpk TOC expected unmasked")
    rows_off, str_off, _, _, ncol, rowlen, _ = struct.unpack_from(">IIIIHHI", b, 8)
    sizes = {0: 1, 1: 1, 2: 2, 3: 2, 4: 4, 5: 4, 6: 8, 7: 8, 8: 4, 9: 8, 0xA: 4, 0xB: 8}
    p, q, field = 32, 0, {}
    for _ in range(ncol):
        fl = b[p]
        ns = 8 + str_off + struct.unpack_from(">I", b, p + 1)[0]
        nm = b[ns:b.index(b"\0", ns)].decode()
        p += 5
        if fl & 0xF0 == 0x30:
            p += sizes[fl & 0x0F]
        elif fl & 0xF0 == 0x50:
            field[nm] = (q, fl & 0x0F)
            q += sizes[fl & 0x0F]
    _, rows = parse_utf(b)
    return toc, utf_at + 8 + rows_off, rowlen, field, rows


def entry(raw, toc, row):
    o = row["FileOffset"] + toc
    d = raw[o:o + row["FileSize"]]
    return layla(d) if d[:8] == b"CRILAYLA" else d


# ---------------------------------------------------------------- overflow estimate
def wrap_lines(toks, W, limit):
    """Simulate word wrap on the body of a string. Returns (lines, width of longest word run)."""
    i = 0
    ops = opseq(toks)
    if 2 in ops:
        i = toks.index((2, b"")) + 1
    lines, x, word = 1, 0, 0
    for t in toks[i:]:
        if isinstance(t, int):
            w = W[t] if t < len(W) else 32
            if t == 63:
                if x + word > limit:
                    lines += 1
                    x = word + w
                else:
                    x += word + w
                word = 0
            else:
                word += w
        elif t[0] in (0, 0x1F):
            if x + word > limit:
                lines += 1
            lines += 1
            x = word = 0
    if x + word > limit:
        lines += 1
    return lines


# ---------------------------------------------------------------- run
mpk = open(f"{ROOT}/sources/sg-fr-patch/script.mpk", "rb").read()
steam = {}
for i in range(struct.unpack_from("<Q", mpk, 8)[0]):
    b = 0x40 + i * 0x100
    _, _, off, _, usize = struct.unpack_from("<LLQQQ", mpk, b)
    steam[mpk[b + 0x20:b + 0x100].split(b"\0")[0].decode().rsplit(".", 1)[0].upper()] = mpk[off:off + usize]
steam["_STARTUP"] = steam.pop("_STARTUP_WIN")

script_raw = open(f"{GAME}/script.cpk", "rb").read()
system_raw = open(f"{GAME}/system.cpk", "rb").read()
W = open(f"{ROOT}/game/PCSE00644/mai_moe/eboot_origin.bin", "rb").read()[0x1061E0:0x1061E0 + 836]
toc, rows_at, rowlen, field, rows = toc_layout(script_raw)
fmt = {2: ">H", 4: ">I", 6: ">Q"}
out = bytearray(script_raw)
report = {"structure": [], "missing": {}}
done, growth, pairs = [], [], {}
for idx, row in enumerate(rows):
    name = row["FileName"].rsplit(".", 1)[0].upper()
    if name in SKIP or (ONLY and name not in ONLY) or name not in steam:
        continue
    vita = entry(script_raw, toc, row)
    if vita[:4] != b"SC3\0" or steam[name][:4] != b"SC3\0":
        continue
    st, rt = struct.unpack_from("<LL", vita, 4)
    if rt == st:  # no strings to translate
        continue
    new, final, en, table = convert_scene(name, vita, steam[name], report)
    if len(out) % ALIGN:
        out += bytes(ALIGN - len(out) % ALIGN)
    pos = len(out)
    out += new
    for col, val in (("FileOffset", pos - toc), ("FileSize", len(new)), ("ExtractSize", len(new))):
        o, ty = field[col]
        struct.pack_into(fmt[ty], out, rows_at + idx * rowlen + o, val)
    done.append(name)
    growth.append((len(new) - len(vita), len(new), name))
    pairs[name] = (final, en, table)
new_script = bytes(out)
print(f"converted {len(done)} scripts; script.cpk {len(script_raw)} -> {len(new_script)} bytes")
print("largest converted:", sorted(((n, k) for _, n, k in growth), reverse=True)[:5])
print("biggest growth:", sorted(growth, reverse=True)[:5])
if report["missing"]:
    print("UNMAPPED CODES:", {k: dict(v) for k, v in report["missing"].items()})
print("strings with remaining control-code differences:", len(report["structure"]))
print("  by scene:", collections.Counter(x[0] for x in report["structure"]).most_common(12))
os.makedirs(f"{ROOT}/build/report", exist_ok=True)
with open(f"{ROOT}/build/report/structure.tsv", "w", encoding="utf-8") as f:
    f.write("scene\tstring\tvita_ops\tfrench_ops\n")
    for s in report["structure"]:
        f.write("\t".join(map(str, s)) + "\n")

# Box width from real hardware: SG00_01 string 1 wrapped after 938 units, and the next word would reach 1111.
story = [k for k in pairs if k.startswith("SG")]
en_all = [t for k in story for t in pairs[k][1]]
for limit in (950, 1000, 1050, 1100):
    c = collections.Counter(wrap_lines(t, W, limit) for t in en_all)
    print(f"  English at width {limit}:", sorted(c.items()))
LIMIT = 1100
en_lines = collections.Counter(wrap_lines(t, W, LIMIT) for t in en_all)
# Longest page the English really uses, ignoring the handful of scripted multi-line layouts.
MAXL = max(l for l, n in en_lines.items() if n >= 5)
print(f"box width {LIMIT}; longest common English page: {MAXL} lines")


def fr_width_tokens(t, table):
    return [table.get(x, 63) if isinstance(x, int) else x for x in t]


over = []
dist = collections.Counter()
for k in story:
    final, en, table = pairs[k]
    for i, t in enumerate(final):
        n = wrap_lines(fr_width_tokens(t, table), W, LIMIT)
        dist[n] += 1
        if n > MAXL:
            over.append((k, i, n, wrap_lines(en[i], W, LIMIT)))
print("French story strings by lines:", sorted(dist.items()))
print(f"French over {MAXL} lines at width {LIMIT}: {len(over)}; of those, already over in English too: {sum(1 for s in over if s[3] > MAXL)}")
with open(f"{ROOT}/build/report/overflow.tsv", "w", encoding="utf-8") as f:
    f.write("scene\tstring\tfrench_lines\tenglish_lines\n")
    for s in over:
        f.write("\t".join(map(str, s)) + "\n")

# Font: identical to the build whose story text and phone menus were checked on hardware.
TESTED_SYSTEM = "aeb69d778522243ee0a19ed33bb23fa5496e4f90126e9334f621a74c6db2addc"
same = hashlib.sha256(new_system := build_font(system_raw)[0]).hexdigest() == TESTED_SYSTEM
print("system.cpk identical to the hardware-tested build:", same)
if not same:
    raise SystemExit("font build changed; refusing to package")

d = f"{ROOT}/build/patch/rePatch/PCSE00644/gamedata"
os.makedirs(d, exist_ok=True)
open(f"{d}/script.cpk", "wb").write(new_script)
open(f"{d}/system.cpk", "wb").write(new_system)

# Independent read-back from the written archive.
back = open(f"{d}/script.cpk", "rb").read()
_, _, _, _, rows2 = toc_layout(back)
ok = bad = untouched = 0
for row, row2 in zip(rows, rows2):
    name = row["FileName"].rsplit(".", 1)[0].upper()
    a, b = entry(script_raw, toc, row), entry(back, toc, row2)
    if name in done:
        ok_here = b[:4] == b"SC3\0" and len(strings(b, True)) == len(strings(a, True))
        # Everything before the strings (labels, bytecode, table position) must be untouched.
        st, rt = struct.unpack_from("<LL", a, 4)
        ok_here = ok_here and a[:st] == b[:st]
        ok += ok_here
        bad += not ok_here
    else:
        untouched += a == b
print(f"read-back: {ok} converted OK, {bad} bad, {untouched} others byte-identical of {len(rows) - len(done)}")
print("script.cpk header unchanged:", script_raw[:2048] == back[:2048])
