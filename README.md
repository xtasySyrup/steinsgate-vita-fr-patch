# Steins;Gate PS Vita : traduction française

Patch de traduction française non officiel pour **Steins;Gate** sur **PS Vita** (`PCSE00644`), installé avec le plugin **rePatch**.

> **Le patch traduit le texte, les images de l'interface et les sous-titres des vidéos.** Quelques images restent en anglais. Le détail est [ici](#ce-que-traduit-le-patch).

> **La release v0.1.0 ne contient que le texte.** Ce README décrit le contenu du dépôt : les images et les vidéos arriveront avec la prochaine release.

> **État : version de test.** Le patch a été testé sur une vraie console, mais seulement pendant le prologue et sur une partie des menus. Le reste du jeu n'a pas encore été parcouru. [Voir ce qui a été vérifié](#ce-qui-a-été-testé).

Ce projet adapte à la Vita la [traduction française de la version Steam](https://github.com/AlpaGit/sg-fr-patch), réalisée par les contributeurs de la VF Steins;Gate. La traduction de l'histoire est leur travail. Ce dépôt contient l'adaptation technique à la Vita, quelques textes refaits pour le petit écran, et les textes des images et des vidéos, que la version Steam ne traduit pas.

## Sommaire

- [Ce que traduit le patch](#ce-que-traduit-le-patch)
- [Installation](#installation)
- [Ce qui a été testé](#ce-qui-a-été-testé)
- [Limites connues](#limites-connues)
- [Comment fonctionne le patch](#comment-fonctionne-le-patch)
- [Différences avec la traduction Steam](#différences-avec-la-traduction-steam)
- [Compiler le patch](#compiler-le-patch)
- [Organisation du dépôt](#organisation-du-dépôt)
- [Crédits](#crédits)
- [Licences et mentions légales](#licences-et-mentions-légales)

## Ce que traduit le patch

| Élément | État | Détail |
|---|---|---|
| Histoire, du prologue au chapitre 11 | Français | 182 scripts de scènes et de téléphone |
| Mails et menus du téléphone | Français | Chaînes du téléphone raccourcies pour tenir à l'écran |
| Pièces jointes des mails | Français | |
| TIPS | Français | Liste, définitions et notification d'ajout |
| Écrans de sauvegarde, chapitres, fins, galerie | Français | Les textes, pas les images de fond |
| Messages système | Français | Sauvegarde, chargement, trophées, erreurs |
| Accents français | Ajoutés | 23 caractères ajoutés aux deux polices du jeu |
| Titres des musiques | Anglais | Laissés tels quels volontairement |
| « Opening A » et « Opening B » | Anglais | Noms de la galerie |
| Images de l'interface | Français | Écran titre et son poème, menu système, sauvegarde et chargement, journal, TIPS, options, galeries, trophées, téléphone, légendes de boutons |
| Tableau de Kurisu | Français | Les neuf étapes du schéma du saut temporel, au chapitre 5 |
| Journaux télévisés | Français | Le crash du satellite et l'alerte à la bombe. *Wallet Check!*, le nom de l'émission, reste tel quel |
| Vidéos `prologue01`, `prologue02`, `imv041` | Français | Sous-titres incrustés dans l'image. Le générique reste d'origine |
| Rapports, journaux, sites et terminaux | Anglais | Images chargées de texte, lues à voix haute par les personnages pour la plupart |
| Cartes de chapitre | Anglais et japonais | Elles ne tiennent pas dans leur emplacement, même sans modification |
| Autres vidéos | Non modifiées | Générique et images stylisées sur les extraits vérifiés |
| Voix | Japonais | Non modifiées |
| Menu de débogage (`ZZZ`) | Anglais | Hors de la partie normale |

## Installation

### Ce qu'il vous faut

- Une PS Vita avec un firmware modifié (HENkaku/Ensō) et le plugin **rePatch**.
- **Votre propre copie** de Steins;Gate, `PCSE00644`, installée sur la console. Le patch ne fonctionne pas sans le jeu.

### Étapes

1. Téléchargez le zip depuis la page **Releases**, puis décompressez-le.
2. Copiez le dossier `rePatch` à la racine de `ux0:` sur la Vita. Vous devez obtenir :

   ```
   ux0:rePatch/PCSE00644/gamedata/script.cpk
   ux0:rePatch/PCSE00644/gamedata/system.cpk
   ux0:rePatch/PCSE00644/gamedata/bg.cpk
   ux0:rePatch/PCSE00644/gamedata/movie.cpk
   ```

   Il faut environ 660 Mo d'espace libre sur la carte.

3. Lancez le jeu.

Pour désinstaller, supprimez `ux0:rePatch/PCSE00644/`. Le jeu installé n'est jamais modifié.

### Version du jeu

Le patch a été créé et testé avec une seule copie du jeu. Il remplace des fichiers entiers et ne vérifie pas votre version : une autre révision du jeu pourrait ne pas fonctionner correctement. Pour comparaison, voici les empreintes SHA-256 des fichiers `gamedata` de la copie utilisée :

```
script.cpk  7e53806fd2fa7e77fc98b1a8a5ca264f883f926e150b5c0f6365693cb378bca8
system.cpk  fd5da80879d05a41244718c39292bd551a52c075e9fea6b86b5dbdd66cdc1363
bg.cpk      694bebaaff6ce3c3a730f67a337a63bb30f0d58de5c8632289ca9d12c67f9c4d
movie.cpk   0cd490cc39891a2a25f6f9275d54d48411a5aa54532837cc988307753bd123e6
```

## Ce qui a été testé

**Vérifié sur une PS Vita**, pendant le prologue :

- le démarrage, ses messages système et l'écran de chargement ;
- le texte de l'histoire, y compris des pages de cinq lignes, et le journal (*backlog*) ;
- les menus et les listes du téléphone, les accents et les notifications ;
- la liste des TIPS et plusieurs définitions ;
- les césures : plus de ligne finissant par « l’ », plus de mot coupé après un accent sur les pages contrôlées ;
- l'écran titre et son menu, et les libellés de la première page des options ;
- les vidéos `prologue01` et `prologue02`, jusqu'à la suite du jeu.

**Vérifié seulement sur PC** :

- chaque script a été relu depuis l'archive produite. Tous les caractères ont une correspondance et le code du jeu reste identique dans chaque script ;
- chaque image relue depuis son archive, et aucun octet modifié en dehors des emplacements prévus ;
- les vidéos décodées sans erreur, avec un son identique à l'original.

**Pas encore vu sur la console** :

- l'histoire après le prologue ;
- le tableau de Kurisu, les journaux télévisés et la vidéo `imv041` ;
- la plupart des autres images de l'interface : des mots pourraient y être coupés, car le jeu n'affiche que certaines zones de chaque image ;
- le corps des mails et les pièces jointes ;
- l'écran de sauvegarde et la plupart des boîtes de dialogue système ;
- les écrans de sélection des chapitres, des fins et de la galerie ;
- une partie des chaînes réécrites du téléphone ;
- la plupart des TIPS, dont la page PTSD raccourcie.

Si vous trouvez un problème, ouvrez une *issue* en indiquant l'écran ou le chapitre, si possible avec une photo.

## Limites connues

- **Coupures en plein mot sur le téléphone.** Le moteur ne garde les mots entiers que pour la police proportionnelle. Le téléphone utilise une police à chasse fixe et peut couper un mot long, comme avec le texte anglais.
- **Espace après l'apostrophe sur le téléphone.** Chaque caractère occupe une case de largeur fixe, d'où un petit écart dans « d’envoi ».
- **Pages de TIPS trop longues.** Une page contient environ 10 lignes. D'après une estimation, cinq pages en demandent environ 11 et ont été laissées telles quelles pour ne pas réécrire le texte : Alpaga, Horizon des événements, Théorie des Supercordes, Bit Particle Gun et la page 2 de Bogue de l'an 2000.
- **Tri des TIPS.** Les clés de tri contiennent maintenant des accents absents de la table de tri du jeu. La liste observée se comporte normalement, mais toutes les entrées n'ont pas été vérifiées.
- **Largeurs de caractères.** La table du jeu n'est pas modifiée. « œ », « î » et « ï » peuvent donc paraître un peu serrés ou espacés.
- **Vocabulaire.** Les termes viennent de la traduction Steam. Elle emploie par exemple à la fois « TIPS » et « Astuces ».
- **Images.** Le français doit tenir dans la place de l'anglais : certains mots sont resserrés, comme *SAUVEGARDER*. La mention *NEW* de la liste des TIPS reste en anglais, tout comme le petit poème sous le logo à la fin de `prologue02`.
- **Traces dans les vidéos.** Là où l'anglais était incrusté sur une image en mouvement, il peut rester une zone floue jusqu'à la fin de la phrase (`prologue02`), ou de légères traînées quand le générique passe au même endroit (`imv041`).
- **Alerte à la bombe.** L'anglais était posé sur un texte japonais : une bande grise diffuse reste derrière le français.

## Comment fonctionne le patch

**rePatch** remplace à la volée les fichiers du jeu par ceux de `ux0:rePatch/PCSE00644/`. Quatre fichiers sont concernés.

**`script.cpk`** contient les scripts au format SC3 du moteur MAGES. La version Vita et la version Steam partagent la même structure de scripts, ce qui permet de faire correspondre les textes par position :

- les codes de caractères Steam sont convertis vers ceux de la Vita, qui possède une rangée proportionnelle pour l'histoire et une rangée à chasse fixe pour le téléphone ;
- les codes de contrôle (nom du personnage, attente d'une touche, position, couleur) sont alignés sur ceux du script Vita ;
- le code du jeu n'est pas modifié, seule la zone de texte change ;
- les scripts convertis sont ajoutés à la fin de l'archive, non compressés, et seule leur entrée dans la table des matières change.

**`system.cpk`** contient les polices et les images de l'interface. Les accents sont dessinés dans des cases libres de chacune des deux polices :

- le fichier 10 sert à l'histoire et au journal ;
- le fichier 11 sert au téléphone, qui découpe chaque lettre selon sa largeur.

Ces fichiers utilisent la compression CRILAYLA et doivent conserver leur taille exacte. Sur la console, un fichier qui laissait trop d'octets de remplissage provoquait un écran noir au démarrage. Le compresseur du projet laisse donc entre 4 et 7 octets inutilisés, comme les fichiers d'origine.

**Les images** de `system.cpk` et `bg.cpk` utilisent une palette de 256 couleurs et suivent la même règle de taille, avec moins de 1 % de marge dans la plupart des cas. Seuls les pixels qui changent reçoivent donc une nouvelle couleur : recalculer toute l'image ferait dépasser l'emplacement. Pour le tableau de Kurisu, l'anglais est effacé à l'aide de la page vierge que le jeu contient aussi.

**`movie.cpk`** contient des vidéos CRI USM, en H.264 non chiffré. Comme le jeu n'utilise pas de piste de sous-titres, le français est incrusté dans l'image : l'anglais est repéré sur plusieurs images successives, réparé, puis le français est dessiné avec la même apparition et le même fondu. La vidéo est réencodée dans les limites des flux d'origine, et le son reste identique. Les nouvelles vidéos sont ajoutées à la fin de l'archive, comme les scripts.

**Les césures** dépendent de deux listes du script `_SYSTEM`, qui indiquent les caractères ne pouvant ni commencer ni terminer une ligne. Le patch y ajoute l'apostrophe, l'espace, le trait d'union et les lettres accentuées, sans quoi le moteur couperait des mots français.

## Différences avec la traduction Steam

La licence demande d'indiquer les modifications apportées au texte d'origine :

- **Téléphone et notifications** : une vingtaine de chaînes raccourcies ou réécrites, par exemple « Messages reçus » pour « Boîte de réception », et « Fond d’écran » pour « Changer le fond d’écran ».
- **Messages système** (`_STARTUP`) : écrits pour la Vita, car ils diffèrent de ceux de la version Steam.
- **Écrans de sauvegarde et trophées** : libellés courts ajoutés, comme « Durée : », « Date : » et « Trophée caché ».
- **Crédits des musiques** : « Musique » et « Paroles », en reprenant les noms de la version Vita.
- **Titres de chapitres de `MACROSYS`** : reformatés depuis les titres français de la version Steam.
- **TIPS** : phrases déplacées entre les pages, sans en changer un mot, pour Interprétation de Copenhague, RaiNet Kakeru et Téléportation Quantique. La page PTSD est légèrement raccourcie, sans perte d'information.

Tous ces textes se trouvent dans [`tools/build_patch.py`](tools/build_patch.py).

Les textes des images et des vidéos n'existent pas dans la version Steam. Ils ont été écrits pour ce patch, à partir de l'anglais du jeu et avec le vocabulaire de la traduction Steam. Ils se trouvent dans [`tools/ui_labels.py`](tools/ui_labels.py), [`tools/bg_labels.py`](tools/bg_labels.py) et [`tools/video_cues.py`](tools/video_cues.py).

## Compiler le patch

Cette étape ne sert qu'à modifier le patch : pour jouer, utilisez la release. Il vous faut Windows, dont les polices servent à dessiner les textes, Python 3 avec [Pillow](https://python-pillow.org/) et [NumPy](https://numpy.org/), et [FFmpeg](https://ffmpeg.org/) avec libx264 pour les vidéos.

1. Placez votre copie du jeu dans `game/PCSE00644/`. Elle doit contenir `mai_moe/eboot_origin.bin`, d'où est lue la table des largeurs.
2. Placez le texte de base dans `sources/sg-fr-patch/script.mpk` ([instructions](sources/README.md)).
3. Compilez le texte. Le résultat est écrit dans `build/patch/`, avec des rapports dans `build/report/` :

   ```bash
   python -I tools/build_patch.py .
   ```

4. Compilez les images de l'interface, les fonds et les vidéos. Le résultat est écrit dans `build/assets/`, avec des aperçus dans `build/report/` :

   ```bash
   python -I tools/build_ui.py .
   ```

   ```bash
   python -I tools/build_bg.py .
   ```

   ```bash
   python -I tools/build_video.py .
   ```

5. Pour fabriquer le zip de release :

   ```bash
   python -I tools/make_release.py . v0.2.0
   ```

Par sécurité, la compilation s'arrête si les polices diffèrent de la version testée sur console. Après une modification voulue des polices, retestez sur Vita, puis mettez à jour `TESTED_SYSTEM` dans `build_patch.py`. De même, une image dont le français ne tient pas dans son emplacement arrête la compilation.

## Organisation du dépôt

```
├── README.md, LICENSE
├── release/            Notice incluse dans le zip de release
├── sources/            Instructions et licence du texte de base
├── tools/
│   ├── build_patch.py  Compilation : conversion du texte, textes réécrits
│   ├── sglib.py        Polices et compresseur CRILAYLA
│   ├── build_ui.py     Images de l'interface (textes : ui_labels.py)
│   ├── build_bg.py     Fonds (textes : bg_labels.py)
│   ├── build_video.py  Vidéos (textes : video_cues.py)
│   ├── ui_paint.py     Dessin du texte dans les images
│   ├── usm.py          Reconstruction des vidéos USM
│   ├── cpk.py          Lecture des archives CPK
│   ├── cpk_write.py    Ajout de fichiers aux archives CPK
│   ├── make_release.py Création du zip de release
│   ├── checks/         Relecture et aperçus simulés du résultat
│   └── analysis/       Scripts d'analyse des formats
├── game/               Votre copie du jeu (ignorée par git)
├── build/              Résultats de compilation (ignorés par git)
└── dist/               Zip de release (ignoré par git)
```

## Crédits

**Le jeu**

- **MAGES. / 5pb. / Nitroplus** : créateurs de Steins;Gate.
- **PQube Ltd.** : édition PS Vita.
- **JAST USA** : localisation anglaise de la version Steam, sur laquelle repose la traduction française.

**La traduction**

- **[Contributeurs de la VF Steins;Gate](https://github.com/AlpaGit/sg-fr-patch)** : traduction française complète de la version Steam, base de ce projet (v1.0.1, CC BY-NC-SA 4.0). Ce projet leur reprend le texte et les emplacements des accents dans la police.
- **[xtasySyrup](https://github.com/xtasySyrup)** : adaptation à la PS Vita, textes des images et des vidéos.

**Les outils et le savoir technique**

- **[Committee of Zero](https://github.com/CommitteeOfZero)** : rétro-ingénierie du moteur MAGES. La table de caractères de [sc3tools](https://github.com/CommitteeOfZero/sc3tools) (MIT) a servi à l'analyse, et [sghd-patch](https://github.com/CommitteeOfZero/sghd-patch) ainsi qu'[impacto](https://github.com/CommitteeOfZero/impacto) ont été consultés. Ce projet n'est pas affilié au Committee of Zero, qui n'en assure pas le support.
- **[dots-tb](https://github.com/dots-tb)** : plugin rePatch, qui rend cette méthode d'installation possible.
- **[Pillow](https://python-pillow.org/)** et **[NumPy](https://numpy.org/)** : traitement des images.
- **[FFmpeg](https://ffmpeg.org/)** et **[x264](https://www.videolan.org/developers/x264.html)** : décodage et encodage des vidéos.
- **[Claude Code](https://claude.com/claude-code) (Anthropic)** : aide au développement des outils et à la rédaction des textes réécrits, des images et des vidéos.

**Consulté sans être repris**

- **[TacTosT/SG-Reboot-Patch-FR](https://github.com/TacTosT/SG-Reboot-Patch-FR)** : traduction de Steins;Gate RE:BOOT, étudiée comme point de départ puis écartée, car son script ne correspond pas à celui de la Vita. **Aucun de ses textes n'est utilisé ici.**

## Licences et mentions légales

- **Outils** (`tools/`) : licence MIT.
- **Textes de la traduction, des images et des vidéos** : [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.fr), comme la traduction d'origine. Toute réutilisation doit créditer ses auteurs, rester non commerciale et conserver la même licence.

Le texte complet se trouve dans [`LICENSE`](LICENSE).

Patch de fan gratuit et non officiel, sans lien avec les ayants droit. La release contient des versions modifiées de quatre archives du jeu, `script.cpk`, `system.cpk`, `bg.cpk` et `movie.cpk`. Les licences ci-dessus ne couvrent que les textes et les outils du projet, pas le reste de ces archives. Le patch ne fonctionne qu'avec le jeu, que vous devez posséder. Tous les droits sur le scénario, les personnages, les illustrations, la musique et le moteur appartiennent à leurs ayants droit.

Si un ayant droit souhaite le retrait de ce patch, il suffit d'ouvrir une *issue*.

*El. Psy. Kongroo.*
