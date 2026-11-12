# Magie du Chaos

Site statique de [magieduchaos.org](https://magieduchaos.org), généré avec [Hugo](https://gohugo.io) (version extended ≥ 0.169) et publié sur GitHub Pages.
Il remplace l'ancien WordPress `burgundi.thanateros.live`, dont les URL sont conservées.

## Travailler en local

```sh
hugo server                      # http://localhost:1313
hugo server --theme kawaii       # prévisualiser un autre skin
hugo --gc --minify               # build de production dans public/
```

## Organisation

| Dossier | Contenu |
| --- | --- |
| `content/posts/<slug>/` | un article = `index.md` + ses images |
| `content/<page>/` | pages (temple, livres, liens, adhésion, carte de visite, confidentialité) |
| `content/types/`, `content/sources/` | les deux axes de catégories (type d'écrit, source) |
| `static/files/` | PDF téléchargeables |
| `themes/base/` | socle : gabarits HTML et CSS de structure, qui n'utilise que des variables |
| `themes/<skin>/` | habillages interchangeables : `chaos-dark` (par défaut), `kawaii` |
| `tools/wp2hugo/` | conversion ponctuelle depuis le dump WordPress |

## Thèmes (skins)

Le skin actif est fixé par `theme` dans `hugo.toml` (ou `--theme <skin>` au build ; chaque skin charge le socle `base` via son propre `hugo.toml`). Un skin ne contient que :

| Fichier | Rôle |
| --- | --- |
| `hugo.toml` | une ligne, `theme = "base"`, pour charger le socle |
| `assets/css/tokens.css` | valeurs des variables (couleurs, polices, rayons…) |
| `assets/css/skin.css` | habillage optionnel, chargé après `base.css` |
| `layouts/_partials/skin/*.html` | points d'accroche : `head`, `header-decor`, `divider`, `footer-decor` |
| `static/` | fichiers propres au skin (polices…) |

`chaos-dark` : fond noir violacé, accents violet et or, étoile du chaos en filigrane et dans les séparateurs, polices Cinzel et EB Garamond auto-hébergées (licence OFL, aucun appel externe).

`kawaii` : fond rose pâle à pois, palette arc-en-ciel pastel, étoile du chaos multicolore derrière le logo et étincelles animées, menu en pastilles, cœur dans les séparateurs, pied de page festonné avec une étoile du chaos souriante. Polices Fredoka et Nunito, auto-hébergées elles aussi.

## Écrire un article

Créer `content/posts/mon-article/index.md` :

```yaml
---
title: "Titre"
date: 2026-11-11T20:00:00+01:00
author: "Pseudo"
types: ["Pratique"]        # Pratique, Point de vue, Autobiographique, Lecture
sources: ["Fait maison"]   # Fait maison, Traduction, Copains
image: "illustration.jpg"  # optionnel, fichier placé dans le même dossier
---
```

Shortcodes disponibles : `{{</* figure src="img.jpg" alt="…" caption="…" */>}}`, `{{</* youtube ID */>}}`, `{{</* tally "renseignements" */>}}`.

## Formulaires

Les formulaires sont hébergés chez Tally. Leurs identifiants se renseignent dans `hugo.toml`, section `[params.tally]`. Tant qu'un identifiant est vide, la page affiche un message avec l'adresse de contact et le build émet un avertissement.

## Reconversion depuis WordPress

Le dump SQL et la copie de l'ancien site restent **hors du dépôt**. Pour régénérer le contenu :

```sh
python3 tools/wp2hugo/wp2hugo.py \
  --dump  /chemin/isabelle_iot-2026-11-04_00_39.sql \
  --uploads /chemin/burgundi.thanateros.org/wp-content/uploads \
  --out .
```

Prérequis : Python 3.10+, `pandoc`, `Pillow`. Le script n'efface rien : vider `content/` et `static/files/` avant de le relancer. `tools/wp2hugo/url-map.csv` liste les anciennes URL et leur équivalent.
