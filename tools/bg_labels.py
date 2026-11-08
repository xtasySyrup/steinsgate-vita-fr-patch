"""French for the backgrounds in bg.cpk. These texts were written for this patch, in the script's vocabulary.

WHITEBOARD: Kurisu's time-leap diagram, built up over images 379-387. Each entry appears in every image that has
ink inside its box: (x0, y0, x1, y1, French, capital height, width limit, alignment, options). Only ink wholly
inside a box is lifted, so a box may cross a bubble's outline, and must contain the whole English word.
Words that touch their bubble can't be separated that way: `inner` lifts everything inside that ellipse (centre x,
centre y, radius x, radius y), which must stay just inside the bubble. `also` adds lines: (dy, French, cap, limit).
NEWS: the two TV images. "Wallet Check!" stays: it is the show's name.
"""
HAND = "Inkfree.ttf"
INK = (52.0, 52.0, 52.0)

BLANK_PAPER = 378
WHITEBOARD_IDS = range(379, 388)
WHITEBOARD = [
    (6, 126, 258, 182, "Moi, le 13 août 2010", 24, 238, "c"),
    (299, 146, 414, 192, "Hippocampe", 16, 106, "c"),
    (503, 142, 888, 195, "Scan données mémorielles (3,24 To)", 20, 372, "l"),
    (503, 190, 900, 252, "Encodage impulsions -> signal électrique", 19, 386, "l"),
    (955, 102, 1210, 143, "Machine à Saut Temporel", 18, 226, "c"),
    (1058, 280, 1178, 333, "Envoi !!", 28, 112, "c"),
    (1094, 320, 1234, 362, "(40~50 s)", 20, 128, "c"),
    (993, 432, 1260, 467, "Créer un trou noir avec le LHC", 16, 256, "l"),
    (993, 461, 1172, 497, "Utiliser le trou noir pour", 16, 236, "l"),
    (981, 504, 1086, 541, "Compresser !", 14, 96, "c", dict(inner=(1033, 523, 50, 15))),
    (1098, 498, 1264, 542, "3,24 To -> 36 o", 20, 158, "c"),
    (851, 419, 931, 461, "Récupérer !", 13, 74, "c", dict(inner=(889, 440, 35, 18))),
    (596, 304, 848, 356, "Machine à Saut Temporel", 23, 242, "c"),
    (389, 397, 592, 471, "Saut Temporel !", 32, 186, "c"),
    (392, 456, 592, 502, "(comme un D-Mail)", 19, 188, "c"),
    (6, 326, 264, 382, "Moi, le 8 août 2010", 26, 244, "c"),
    (278, 461, 355, 495, "Réception", 14, 72, "c"),
    (60, 479, 216, 538, "Données mémoire", 15, 130, "c", dict(inner=(137, 510, 80, 28), lift=-13, also=[(13, "écrasées !", 16, 118)])),
]

# box, how to find the old letters, then French drawn over it.
NEWS = {
    426: [
        dict(box=(918, 36, 1192, 128), dark=105, light=225, grow=2,
             draw=[(1048, 62, "Un satellite s’écrase !", "impact.ttf", 28, 0, (6, 6, 6), (255, 255, 255), 1.5, 260),
                   (1048, 102, "Akiba en émoi !", "impact.ttf", 28, 0, (6, 6, 6), (255, 255, 255), 1.5, 260)]),
        dict(box=(118, 610, 1262, 678), dark=60, light=205, grow=2,
             draw=[(690, 644, "Origine, autres infos : enquête en cours", "verdanab.ttf", 36, 0, (250, 250, 250), (14, 14, 14), 2.5, 1124)]),
    ],
    434: [
        dict(box=(130, 0, 1050, 222), dark=48, light=222, grow=3, band=((148, 118, 893, 30), (170, 176, 1033, 70)), band_half=38,
             draw=[(520, 72, "Alerte à la bombe : arrêt des lignes", "arialbd.ttf", 34, 7, (250, 250, 250), (10, 10, 10), 2.5, 770),
                   (600, 128, "Yamanote, Sobu et Keihin-Tohoku", "arialbd.ttf", 36, 7, (250, 250, 250), (10, 10, 10), 2.5, 880)]),
        dict(box=(92, 580, 452, 632), dark=None, light=225, red=True, grow=3,
             draw=[(270, 610, "Le perdant paie !", "trebucbd.ttf", 30, -3, (176, 38, 44), (248, 248, 248), 3, 350)]),
    ],
}

SPLASH_SLOT = 427  # A news image no script ever loads.
SPLASH_SIZE = (1280, 720)
SPLASH_BACKGROUND = (0, 0, 0, 255)
# The source image's own white text says "Traduction par :" on this line, drawn over with the project's wording.
SPLASH_LINE = dict(clear=(600, 535, 970, 587), text="Adaptation par :", font="verdana.ttf", size=44, at=(606, 572))
