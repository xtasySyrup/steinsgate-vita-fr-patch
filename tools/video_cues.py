"""French subtitles burned into the game's videos. These texts were written for this patch: the Steam French
translation has no video subtitles.

A cue is (first frame, rows); it lasts until the next cue. A row is (top, bottom, French) plus optional settings:
align: c frame centre (default), l or r anchored to the English line's left or right end, m centred on it
xlim: columns the English can be in; slide: the English also erases from the left as it goes
win: (first, last + 1) frames, when a line outlives or overlaps its cue
top and bottom bracket one English line.
"""
ARIAL = dict(font="arial.ttf", cap=17, hscale=0.88, shadow=1.6, shadow_gain=1.5, shadow_dark=0.75)
TITLES = dict(font="trebucbd.ttf", cap=14, hscale=0.94, shadow=2.0, shadow_gain=1.6, shadow_dark=0.7)
DIALOGUE = dict(font="trebuc.ttf", cap=20, hscale=0.96, shadow=2.5, shadow_gain=1.5, shadow_dark=0.3, glow=95)

PROLOGUE01 = [
    (30, [(293, 322, "Tout n’est que coïncidence.")]),
    (125, [(293, 322, "Mais même la coïncidence s’inscrit dans le dessein du destin.")]),
    (306, [(293, 320, "Je ne perds pas la tête. Je suis parfaitement sain d’esprit.")]),
    (425, [(297, 325, "Ce que je dis est la vérité absolue, pas un fantasme puéril.")]),
    (604, [(290, 316, "......Aussi insignifiante qu’une chose puisse paraître,")]),
    (728, [(294, 323, "elle peut façonner l’avenir.")]),
    (886, [(292, 316, "As-tu déjà entendu parler de l’Effet Papillon ?")]),
    (960, [(308, 332, "Sinon, renseigne-toi."), (337, 361, "Alors tu comprendras à quel point tu dois être prudent.")]),
    (1144, [(290, 314, "Malheureusement, je n’ai pas compris.")]),
    (1272, [(288, 317, "Si seulement j’avais compris à quel point mes actes étaient dangereux, je ne l’aurais pas perdue.")]),
    (1436, [(290, 315, "L’avenir n’aurait pas pris cette tournure.")]),
    (1547, [(291, 315, "Mais comment aurais-je pu le savoir ?")]),
    (1678, [(305, 334, "Comment aurais-je pu savoir qu’en appuyant sur ce bouton,"), (336, 360, "je déciderais du sort de l’humanité tout entière ?")]),
    (1983, [(289, 312, "Réfléchis-y un peu.")]),
    (2034, [(303, 332, "L’être humain moyen ne perçoit qu’un pour cent de son environnement."), (332, 356, "Nous sommes loin d’être aussi malins que nous aimons le croire.")]),
    (2286, [(303, 332, "Nous vivons sans prêter attention aux millions de choses qui se passent autour de nous chaque jour."), (332, 361, "Même quand quelque chose attire notre regard, notre cerveau l’oublie l’instant d’après.")]),
    (2600, [(291, 314, "Je voudrais dire au moi de cette époque :")]),
    (2655, [(290, 319, "Ne fais rien d’imprudent !")]),
    (2741, [(290, 314, "Ne fais rien d’irréfléchi !")]),
    (2820, [(290, 319, "Ne fais pas semblant de n’avoir rien vu !")]),
    (2915, [(290, 313, "Fais plus attention !")]),
    (3029, [(306, 335, "La main de la conspiration a toujours été plus proche que tu ne le pensais,"), (336, 365, "attendant simplement le bon moment pour frapper !")]),
]

# The poem. POEM in ui_labels.py is the same text on the title screen.
PROLOGUE02 = [
    (30, [(414, 438, "L’univers a un début, mais il n’a pas de fin.", dict(align="l")), (438, 458, "— Infini", dict(align="l", win=(150, 213), xlim=(90, 420)))]),
    (213, [(411, 436, "Les étoiles aussi ont un début, mais leur propre force les détruit.", dict(align="l")), (436, 456, "— Fini", dict(align="r", win=(385, 433), xlim=(770, 880)))]),
    (433, [(431, 455, "L’histoire enseigne que ceux qui détiennent la sagesse sont souvent les plus insensés.", dict(align="l", slide=True))]),
    (612, [(432, 455, "Les poissons de la mer ne connaissent pas la terre.", dict(align="r"))]),
    (754, [(417, 443, "S’ils avaient la sagesse, eux aussi seraient détruits.", dict(align="l", slide=True))]),
    (870, [(432, 458, "Il est plus ridicule pour l’homme de dépasser la vitesse de la lumière", dict(align="r"))]),
    (964, [(433, 456, "que pour un poisson de vivre à terre.", dict(align="l", win=(964, 1098))),
           (253, 275, "Ceci peut aussi être appelé", dict(align="m", win=(1082, 1183)))]),
    (1200, [(209, 239, "l’ultime avertissement de Dieu à ceux qui se rebellent.", dict(align="m", xlim=(220, 740)))]),
]

def L(x0, x1):
    """Columns of the English line. Credits scroll through these rows, so each line is held to its own width."""
    return dict(align="l", xlim=(x0, x1))


IMV041 = [
    (3365, [(376, 403, "Allô ?", L(40, 260))]),
    (3440, [(375, 403, "Hein, qui ça ?", L(40, 270))]),
    (3500, [(377, 405, "Papa ? Tu cherches", L(40, 476)), (420, 452, "ton papa ?", L(300, 476))]),
    (3565, [(376, 409, "Je suis ton papa ?", L(40, 330))]),
    (3612, [(377, 405, "Là, tu m’as perdu.", L(40, 320))]),
    (3687, [(375, 403, "Hein ?", L(40, 200))]),
    (3720, [(376, 405, "Te passer Okabe Rintaro ?", L(40, 462))]),
    (3826, [(375, 408, "Hé, Okarin, y a une", L(40, 385)), (417, 451, "drôle de fille qui", L(40, 385)), (459, 487, "veut te parler.", L(150, 385))]),
    (3983, [(375, 403, "...Qui est à l’appareil ?", L(40, 340))]),
    (4015, [(374, 402, "S’il te plaît ! Viens sur le toit", L(40, 490)), (416, 444, "du Radi-Kan tout de suite !", L(40, 490))]),
    (4120, [(375, 404, "Mais qui est à l’appareil ?", L(40, 310))]),
    (4185, [(375, 403, "Je viens de", L(40, 310)), (417, 451, "l’an 2036.", L(40, 366))]),
    (4282, [(376, 404, "Je suis la fille", L(40, 398)), (419, 446, "de Hashida Itaru.", L(235, 398))]),
    (4415, [(376, 409, "Je m’appelle", L(40, 260)), (417, 444, "Amane Suzuha.", L(160, 438))]),
    (4532, [(376, 405, "Attends...", L(40, 230)), (410, 438, "Suzuha ?", L(150, 285)), (444, 478, "Qu’est-ce que tu fais là ?!", L(175, 480))]),
]

VIDEOS = {
    "prologue01.USM": dict(cues=PROLOGUE01, end=3440, style=ARIAL),
    "prologue02.USM": dict(cues=PROLOGUE02, end=1300, style=TITLES, grow=6),
    "imv041.USM": dict(cues=IMV041, end=4745, style=DIALOGUE, grow=8, threshold=45, streak=9),
}
