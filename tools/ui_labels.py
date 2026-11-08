"""The French labels baked into system.cpk textures, sheet by sheet.

Each op is (kind, ...): "L" replace a measured word, "T" draw at a fixed spot, "W" wipe a faint word, "B" blank.
Search boxes need clear background on both sides of the word; the painter measures the word itself.
Texts here were written for this patch, following the vocabulary of the Steam French translation.
"""
SANS, BOLD, ITALIC_BOLD, SERIF_BOLD, MONO_BOLD, BLACK = "arial.ttf", "arialbd.ttf", "arialbi.ttf", "timesbd.ttf", "courbd.ttf", "ariblk.ttf"
LEG = dict(cap=12, t=70)  # button legends: white on a dark pill


def leg(x0, x1, y, string, limit=None, **kw):
    return ("L", (x0, y, x1, y + 23), string, dict(LEG, limit=limit or x1 - x0, **kw))


def page_title(ghost_box, ghost_x, ghost_y, ghost_cap, ghost_color, string, x, y, font=SERIF_BOLD, cap=21, align="l", color=(255, 255, 255), wipe_t=9, ghost_opacity=0.8, limit=None, ghost_limit=None):
    """A page title and the large faint copy behind it."""
    return [
        ("W", ghost_box, dict(t=wipe_t)),
        ("T", ghost_x, ghost_y, string, dict(font=BOLD, cap=ghost_cap, align="l", color=ghost_color, opacity=ghost_opacity, limit=ghost_limit)),
        ("T", x, y, string, dict(font=font, cap=cap, align=align, color=color, shadow=((30, 30, 30), 1), limit=limit)),
    ]


def save_screen(title, ghost_box, ghost_color, title_color, stamp_box, stamp, stamp_limit=None):
    return page_title(ghost_box, 100, 66, 52, ghost_color, title, 64, 55, font=BOLD, cap=20, align="l", color=title_color, ghost_limit=700) + [
        leg(790, 880, 667, "Sélection", 80),
        leg(919, 990, 667, "Valider", 64),
        leg(1030, 1104, 667, "Verrouiller", 70),
        leg(1146, 1192, 667, "Retour", 42),
        ("G", stamp_box, stamp_box[2] - 4, stamp_box[1] + 32, stamp, dict(cap=24, t=8, align="r", limit=stamp_limit or 190, opacity=0.9)),
        ("L", (573, 760, 644, 773), "VIDE", dict(font=BOLD, t=35, align="c")),
    ]


CG_LEGENDS = [
    leg(722, 830, 666, "Sélectionner", 104),
    leg(901, 1020, 666, "Changer de page", 115),
    leg(1063, 1126, 666, "Valider", 60),
    leg(1170, 1210, 666, "Retour", 44),
    leg(532, 577, 736, "Défiler", 40), leg(610, 724, 736, "Guide ON/OFF", 108), leg(759, 940, 736, "Taille réelle", 176),
    leg(972, 1023, 736, "Agrandir", 48), leg(1056, 1110, 736, "Réduire", 48), leg(1171, 1211, 736, "Retour", 40),
    leg(387, 432, 776, "Défiler", 38), leg(457, 572, 776, "Guide ON/OFF", 108), leg(614, 795, 776, "Taille réelle", 176),
    leg(829, 880, 776, "Agrandir", 48), leg(907, 960, 776, "Réduire", 48), leg(984, 1146, 776, "Variante suivante", 158), leg(1171, 1211, 776, "Retour", 40),
]

MENU_L, MENU_D, MENU_X = (727, 891), (919, 1083), (1111, 1275)
MENU_ROWS = [("CHARG. RAPIDE", 754, True), ("CHARGER", 780, True), ("FINS", 806, False), ("GALERIE CG", 832, False), ("MUSIQUES", 858, False),
             ("VIDÉOS", 884, False), ("TIPS", 910, False), ("TROPHÉES", 936, True), ("OPTIONS", 962, True), ("SAUV. SYSTÈME", 988, True)]
MENU_FONT = "times.ttf"


# Where each old word starts inside its column, so the search box leaves the empty part of the row alone.
MENU_START = {"CHARG. RAPIDE": 20, "CHARGER": 94, "FINS": 18, "GALERIE CG": 20, "MUSIQUES": 2, "VIDÉOS": 2, "TROPHÉES": 50, "OPTIONS": 62, "SAUV. SYSTÈME": 6}


def title_menu():
    ops = []
    for word, y0, y1 in (("JOUER", 754, 784), ("CHARGER", 787, 817), ("BONUS", 820, 850), ("SYSTÈME", 853, 883)):
        ops.append(("L", (446, y0 + 1, 567, y1 - 1), word, dict(font=SERIF_BOLD, t=45, align="c", halo=2, limit=112, cap=20, color=(255, 255, 255), dy=1)))
        ops.append(("L", (581, y0 + 1, 700, y1 - 1), word, dict(font=SERIF_BOLD, t=45, align="c", halo=2, limit=110, cap=20, color=(14, 14, 24), dy=1)))
    for word, y, disabled in MENU_ROWS:
        if word == "TIPS":
            continue
        for (x0, x1), on in ((MENU_L, True), (MENU_D, True), (MENU_X, disabled)):
            if on:
                ops.append(("L", (x0 + MENU_START[word], y + 2, x1 - 2, y + 22), word, dict(font=MENU_FONT, t=30, align="r", cap=15, limit=x1 - x0 - 8)))
    return ops


# The same text as the poem in video_cues.py.
POEM = [
    (611, "L’univers a un début, mais il n’a pas de fin. — Infini."),
    (623, "Les étoiles aussi ont un début, mais leur propre force les détruit. — Fini."),
    (635, "L’histoire enseigne que ceux qui détiennent la sagesse sont souvent les plus insensés."),
    (647, "Les poissons de la mer ne connaissent pas la terre. S’ils avaient la sagesse, eux aussi seraient détruits."),
    (659, "Il est plus ridicule pour l’homme de dépasser la vitesse de la lumière que pour un poisson de vivre à terre."),
    (671, "Ceci peut aussi être appelé l’ultime avertissement de Dieu à ceux qui se rebellent."),
]


def title_plate():
    ops = [("L", (60, 722, 355, 752), "Appuyez sur START", dict(font="times.ttf", t=40, cap=20, limit=290, align="l", color=(226, 190, 122)))]
    for y, line in POEM:
        ops.append(("W", (540, y - 7, 1220, y + 5), dict(t=120, halo=1)))
    ops.append(("T", 130, 648, "Adaptation par xtasySyrup", dict(font="bahnschrift.ttf", cap=11, color=(172, 172, 172))))
    for y, line in POEM:
        ops.append(("T", 880, y + 3, line, dict(font=MONO_BOLD, cap=7, align="c", limit=676, color=(255, 255, 255))))
    return ops


SHEETS = {
    # Load, quick load, save
    12: save_screen("CHARGER", (93, 0, 310, 70), (90, 88, 70), (255, 255, 255), (414, 728, 524, 766), "CHARGER"),
    58: save_screen("CHARGEMENT RAPIDE", (36, 0, 596, 70), (90, 88, 70), (255, 255, 255), (312, 728, 524, 766), "CHARG. RAPIDE", 205),
    60: save_screen("SAUVEGARDER", (95, 0, 290, 70), (150, 150, 185), (30, 30, 40), (414, 728, 524, 766), "SAUVEGARDER"),
    # CG gallery
    0: page_title((26, 22, 342, 72), 32, 66, 40, (28, 56, 110), "GALERIE CG", 60, 56, ghost_limit=700, cap=19) + CG_LEGENDS + [
        ("L", (1345, 428, 1465, 448), "PAS D’IMAGE", dict(font="times.ttf", t=40, align="c", limit=115)),
    ],
    # Endings
    6: page_title((26, 22, 356, 72), 32, 66, 40, (20, 44, 100), "FINS", 60, 56, ghost_limit=700, cap=19) + [leg(1172, 1216, 674, "Retour", 44)],
    # Backlog
    5: [("L", (1030, 40, 1192, 72), "JOURNAL", dict(font=BLACK, t=60, align="r", cap=22, limit=155)), leg(968, 1076, 672, "Écouter la voix", 104), leg(1111, 1156, 672, "Retour", 44)],
    # TIPS
    9: page_title((26, 18, 326, 72), 32, 66, 40, (75, 72, 66), "LISTE DES TIPS", 60, 56, ghost_limit=700, cap=19) + [
        leg(678, 780, 667, "Changer", 92), leg(811, 856, 667, "Retour", 44), leg(888, 996, 667, "Changer page", 100), leg(1028, 1192, 667, "Afficher la sélection", 158),
    ],
    # Trophies
    64: page_title((26, 22, 220, 72), 32, 66, 38, (24, 50, 110), "TROPHÉES", 56, 56, ghost_limit=700, cap=19) + [leg(1163, 1208, 659, "Retour", 44)],
    # Sound library
    14: page_title((26, 22, 460, 74), 32, 68, 40, (70, 74, 84), "MUSIQUES", 60, 58, ghost_limit=700, cap=19) + [
        leg(718, 806, 670, "Sélection", 80), leg(833, 878, 670, "Retour", 38), leg(902, 945, 670, "Stop", 40), leg(970, 1118, 670, "Mode de lecture", 140), leg(1145, 1185, 670, "Lire", 36),
        ("L", (886, 104, 974, 120), "musiques", dict(t=40, limit=80, cap=10)), ("L", (986, 104, 1070, 120), "vidéos", dict(t=30, limit=80, cap=10)), ("L", (1128, 104, 1192, 120), "tout répéter", dict(t=30, limit=62, cap=10)),
        ("L", (118, 754, 182, 770), "tout répéter", dict(t=30, limit=62, cap=10)),
    ],
    # Movie library
    13: page_title((26, 22, 456, 74), 32, 68, 40, (70, 74, 84), "VIDÉOS", 60, 58, ghost_limit=700, cap=19) + [
        leg(920, 1010, 670, "Sélection", 84), leg(1050, 1096, 670, "Retour", 44), leg(1137, 1180, 670, "Lire", 36),
        ("L", (886, 104, 974, 120), "musiques", dict(t=30, limit=80, cap=10)), ("L", (986, 104, 1070, 120), "vidéos", dict(t=40, limit=80, cap=10)), ("L", (1128, 104, 1192, 120), "tout répéter", dict(t=30, limit=62, cap=10)),
    ],
    # Config, page 1
    15: [
        ("L", (104, 174, 480, 198), "Stopper saut/auto aux déclencheurs téléphone", dict(ax=110, cap=13, t=38, limit=370)),
        ("L", (104, 212, 480, 234), "Afficher les nouveaux TIPS", dict(ax=110, cap=13, t=38)),
        ("L", (104, 250, 480, 273), "Sauvegarde rapide automatique", dict(ax=110, cap=13, t=38)),
        ("L", (104, 288, 480, 311), "Type de commandes", dict(ax=110, cap=13, t=38)),
        ("L", (104, 324, 480, 348), "Utiliser l’écran tactile", dict(ax=110, cap=13, t=38)),
        ("L", (104, 381, 300, 404), "Vitesse du texte", dict(ax=110, cap=13, t=38, limit=195)),
        ("L", (104, 429, 305, 452), "Attente du mode auto", dict(ax=110, cap=13, t=38, limit=198)),
        ("L", (104, 475, 480, 498), "Mode saut", dict(ax=110, cap=13, t=38)),
        ("L", (312, 384, 352, 402), "lent", dict(t=45, cap=9)), ("L", (602, 382, 642, 400), "rapide", dict(t=45, cap=9, limit=38)),
        ("L", (312, 432, 352, 450), "lent", dict(t=45, cap=9)), ("L", (602, 430, 642, 448), "rapide", dict(t=45, cap=9, limit=38)),
    ] + [
        ("L", (771, y, 970, y + 22), s, dict(cap=13, t=45, limit=196, ax=775)) for y, s in (
            (141, "Déplacer le curseur"), (173, "Déplacer le curseur"), (205, "Déplacer le curseur"), (238, "Mode saut"), (269, "Mode auto"),
            (300, "Annuler / Masquer le texte"), (331, "Valider / Passer le texte"), (365, "Menu système"), (395, "Déclencheurs téléphone"), (428, "Afficher les TIPS"), (459, "Saut forcé"))
    ] + [
        ("L", (982, y, 1190, y + 22), s, dict(cap=13, t=45, limit=205, ax=986)) for y, s in (
            (141, "Déplacer le curseur"), (173, "Déplacer le curseur"), (205, "Déplacer le curseur"), (235, "Menu système"), (268, "Journal"),
            (300, "Annuler / Masquer le texte"), (331, "Valider / Passer le texte"), (365, "Déclencheurs téléphone"), (395, "Afficher les TIPS"), (428, "Mode auto"), (459, "Mode saut"))
    ] + [
        leg(264, 340, 661, "Sélection", 72), leg(368, 458, 661, "Changer page", 86), leg(486, 586, 661, "Par défaut", 92), leg(617, 660, 661, "Retour", 42),
        ("G", (490, 120, 648, 170), 502, 160, "base", dict(font=BLACK, cap=30, t=14, halo=2, opacity=0.9, rough=0.12)),
        ("G", (110, 518, 272, 578), 122, 566, "texte", dict(font=BLACK, cap=34, t=14, halo=2, opacity=0.9, rough=0.12)),
        ("L", (0, 722, 60, 742), "OUI", dict(cap=13, t=38)), ("L", (0, 746, 60, 767), "NON", dict(cap=13, t=38)),
        ("L", (0, 819, 170, 839), "Déjà lu seulement", dict(cap=13, t=38)), ("L", (0, 844, 170, 862), "Tout", dict(cap=13, t=38)),
        ("L", (0, 867, 170, 887), "Chaque déclencheur", dict(cap=13, t=38)), ("L", (0, 890, 170, 909), "Chaque scène", dict(cap=13, t=38)),
        ("L", (0, 914, 200, 934), "Déclencheur + scène", dict(cap=13, t=38)),
    ],
    # Config, pages 2 and 3
    16: [
        ("L", (104, 177, 300, 200), "Volume des voix", dict(ax=110, cap=14, t=38, limit=195)),
        ("L", (104, 217, 300, 240), "Volume de la musique", dict(ax=110, cap=14, t=38, limit=198)),
        ("L", (104, 255, 300, 278), "Volume des effets", dict(ax=110, cap=14, t=38, limit=195)),
        ("L", (104, 294, 300, 317), "Volume des vidéos", dict(ax=110, cap=14, t=38, limit=195)),
        ("L", (104, 335, 480, 358), "Synchronisation des voix", dict(ax=110, cap=13, t=38)),
        ("L", (104, 375, 480, 398), "Passer les dialogues vocaux", dict(ax=110, cap=13, t=38)),
        ("G", (468, 396, 656, 440), 490, 432, "son", dict(font=BLACK, cap=30, t=14, halo=2, opacity=0.9, rough=0.12)),
        ("G", (1752, 110, 1928, 158), 1772, 150, "voix", dict(font=BLACK, cap=32, t=14, halo=2, opacity=0.9, rough=0.12)),
        ("L", (1424, 516, 1600, 540), "Autres", dict(cap=15, t=60)),
        leg(264, 340, 661, "Sélection", 72), leg(368, 458, 661, "Changer page", 86), leg(486, 586, 661, "Par défaut", 92), leg(617, 660, 661, "Retour", 42),
        leg(1545, 1621, 661, "Sélection", 72), leg(1649, 1739, 661, "Changer page", 86), leg(1767, 1867, 661, "Par défaut", 92), leg(1898, 1941, 661, "Retour", 42),
    ],
    # System menu; the strip at y 480-612 holds Japanese legends with Xbox buttons, which the Vita never shows.
    7: [("B", (0, 480, 552, 612))] + [
        ("L", (660, y, 830, y + 32), s, dict(font=ITALIC_BOLD, t=60, cap=20, limit=139, shadow=((20, 20, 20), 2), halo=3)) for y, s in (
            (5, "JOURNAL"), (49, "SAUV. RAPIDE"), (93, "CHARG. RAPIDE"), (137, "SAUVEGARDER"), (181, "CHARGER"), (225, "OPTIONS"), (313, "MESSAGES"), (357, "TROPHÉES"), (401, "ÉCRAN TITRE"))
    ] + [
        ("L", (54, y, 166, y + 26), "SAUVEGARDÉ", dict(font=BOLD, t=50, cap=14, align="c", limit=100, halo=3, dy=3)) for y in (111, 169, 227, 285)
    ] + [
        ("L", (292, 124, 346, 149), "SAUT", dict(font=BOLD, t=70, cap=15, limit=46, align="r")),
    ],
    # Title screen
    61: title_plate() + title_menu(),
}

# The five phone skins share one layout.
_PHONE = [
    ("G", (1308, 704, 1560, 756), 1310, 750, "RÉGLAGES", dict(cap=38, t=8, limit=245)),
    ("L", (330, 858, 530, 896), "Voix seule", dict(font="consola.ttf", t=60, cap=22, limit=190)),
    ("L", (582, 858, 790, 892), "Lecteur", dict(font="consola.ttf", t=60, cap=20, limit=200)),
    ("L", (1054, 678, 1077, 696), "De", dict(font=BOLD, t=45, cap=11, align="c", limit=20, color=(255, 255, 255))),
    ("L", (1080, 678, 1101, 696), "À", dict(font=BOLD, t=45, cap=10, align="c", limit=18, dy=1, color=(255, 255, 255))),
    ("L", (1105, 678, 1129, 696), "Obj", dict(font=BOLD, t=45, cap=11, align="c", limit=22, color=(255, 255, 255))),
] + [
    ("L", box, s, dict(font="consola.ttf", t=60, cap=11, limit=34, align="c")) for box, s in (
        ((334, 826, 376, 843), "DIM"), ((385, 826, 427, 843), "LUN"), ((437, 826, 477, 843), "MAR"), ((282, 844, 324, 862), "MER"),
        ((334, 844, 376, 862), "JEU"), ((385, 844, 427, 862), "VEN"), ((437, 844, 477, 862), "SAM"))
]
for _id in (33, 34, 35, 36, 37):
    SHEETS[_id] = _PHONE
