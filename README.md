# Magie du Chaos

Site statique de [magieduchaos.org](https://magieduchaos.org), généré avec [Hugo](https://gohugo.io) (version extended ≥ 0.169) et publié sur GitHub Pages.
Il remplace l'ancien WordPress `burgundi.thanateros.live`, dont les URL sont conservées.

## Travailler en local

```sh
hugo server                      # http://localhost:1313
hugo server --theme kawaii       # un seul skin, sans sélecteur
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
| `themes/<skin>/` | habillages interchangeables : `chaos-dark` (par défaut), `kawaii`, `cthulhu`, `baphomet` |
| `tools/wp2hugo/` | conversion ponctuelle depuis le dump WordPress |
| `tools/skins/<skin>/` | scripts qui génèrent les tracés SVG d'un skin (filigrane, ornements) |

## Thèmes (skins)

Les skins chargés sont listés par `theme` dans `hugo.toml` (chacun charge le socle `base` via son propre `hugo.toml`). Le build produit un CSS complet par skin, et le visiteur choisit l'apparence dans le pied de page (« Apparence du site »). Son choix est mémorisé dans son navigateur (`localStorage`, clé `magieduchaos-apparence`) : aucun cookie, rien n'est envoyé au serveur.

- `params.defaultSkin` fixe le skin affiché à la première visite et pour les visiteurs sans JavaScript (le sélecteur reste alors caché).
- Le skin est choisi par un petit script en ligne dans `<head>` (`themes/base/assets/js/skin.js`) avant le premier affichage : pas de flash de l'autre skin en changeant de page. Le choix se propage aux autres onglets ouverts.
- `params.randomSkin` active le mode « au hasard » : un skin différent est tiré au sort à chaque changement de page (jamais deux fois de suite le même). `"off"` le désactive, `"option"` l'ajoute au sélecteur (« Au hasard à chaque page »), `"default"` l'ajoute et l'active pour les nouveaux visiteurs, qui peuvent toujours choisir un skin fixe. Le mode est mémorisé comme un choix ordinaire (valeur `random`) ; le dernier skin affiché est retenu dans `sessionStorage` pour éviter les répétitions.
- Pour remettre tous les visiteurs sur le réglage du site (après un changement de `defaultSkin` ou `randomSkin`), changer `KEY` dans `skin.js` et ajouter l'ancienne clé à `OLD_KEYS`, qui est effacée chez les visiteurs. La clé est passée de `magieduchaos-skin` à `magieduchaos-apparence` lors de l'activation du mode au hasard par défaut.
- Avec un seul skin (`hugo --theme kawaii`), le site est construit comme avant, sans sélecteur ni mode au hasard.

Un skin contient :

| Fichier | Rôle |
| --- | --- |
| `hugo.toml` | `theme = "base"` et la déclaration `[params.skins.<nom>]` : `label` (nom dans le sélecteur), `weight` (ordre), `themeColor`, `colorScheme`, `preload` (polices à précharger) |
| `assets/css/skins/<nom>/tokens.css` | valeurs des variables (couleurs, polices, rayons…) |
| `assets/css/skins/<nom>/skin.css` | habillage optionnel, chargé après `base.css` |
| `layouts/_partials/skins/<nom>/*.html` | ornements : `header-decor`, `divider`, `footer-decor` (à défaut, ceux de `base/layouts/_partials/skins/_default/`), plus ses propres partials |
| `static/` | fichiers propres au skin (polices…) |

Tous les fichiers d'un skin sont rangés sous son nom, pour que plusieurs skins cohabitent dans un même build. Les ornements de chaque skin sont présents dans le HTML ; seul celui du skin actif est affiché.

Ajouter un skin : créer `themes/<nom>/` sur ce modèle, puis l'ajouter à la liste `theme` de `hugo.toml`.

`chaos-dark` : fond noir violacé, accents violet et or, étoile du chaos en filigrane et dans les séparateurs, polices Cinzel et EB Garamond auto-hébergées (licence OFL, aucun appel externe).

`kawaii` : fond rose pâle à pois, palette arc-en-ciel pastel, étoile du chaos multicolore derrière le logo et étincelles animées, menu en pastilles, cœur dans les séparateurs, pied de page festonné avec une étoile du chaos souriante. Polices Fredoka et Nunito, auto-hébergées elles aussi.

`cthulhu` : abysses vert-de-mer et laiton terni, étoile du chaos tentaculaire avec un œil qui cligne en filigrane, bulles dans l'en-tête, tentacules qui émergent du pied de page, polices IM Fell English et Crimson Pro auto-hébergées (licence OFL). Les tracés des tentacules sont générés par calcul : les régénérer plutôt que les retoucher à la main. Les animations sont coupées si le visiteur a demandé à réduire les animations.

`baphomet` : grimoire clair d'après le Baphomet d'Éliphas Lévi (1856). Fond de parchemin vergé avec des rousseurs aux coins, et une tête de bouc originale en traits fins en filigrane (étoile du chaos au front, flamme entre les cornes, lune blanche et lune noire), fixée au centre de la page. Encre brune, vermillon pour les liens et les rubriques, or terni pour le contour de focus. Un flambeau à la flamme vacillante au-dessus du logo, *Solve* et *Coagula* de part et d'autre du titre (à la verticale sur mobile), lettrine vermillon en début d'article, et un séparateur lune blanche, pentagramme pointe en haut, lune noire. Pied de page inversé, fond d'encre, avec un caducée planté dedans. Polices UnifrakturMaguntia (titre du site), Cormorant SC (titres, menu) et Spectral (texte), auto-hébergées (licence OFL). Le filigrane et les ornements sont générés par `tools/skins/baphomet/` (`python3 goat.py <dépôt>` et `python3 ornaments.py <dépôt>`) : les régénérer plutôt que les retoucher à la main. L'animation du flambeau est coupée si le visiteur a demandé à réduire les animations.

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

## Publication

Chaque push sur `main` déclenche `.github/workflows/hugo.yml` : GitHub installe Hugo extended 0.169.0, construit le site (`hugo --gc --minify`) et le publie sur GitHub Pages. Le dossier `public/` n'est jamais commité. Suivi dans l'onglet **Actions** du dépôt ; le bouton « Run workflow » relance une publication sans nouveau commit.

Mise en place (une seule fois) :

1. **Settings → Pages → Build and deployment → Source** : choisir « GitHub Actions ».
2. **Settings → Pages → Custom domain** : `magieduchaos.org`, puis cocher « Enforce HTTPS » dès que le certificat est prêt. Avec une publication par Actions, un fichier `CNAME` dans le dépôt est ignoré : le domaine se règle uniquement ici.
3. DNS de `magieduchaos.org` :
   - apex : enregistrements `A` vers `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153` (et `AAAA` vers `2606:50c0:8000::153` à `2606:50c0:8003::153` si souhaité) ;
   - `www` : `CNAME` vers `dkuster.github.io`.
4. Recommandé : vérifier le domaine dans les réglages du compte GitHub (Settings → Pages → Verified domains) pour empêcher qu'un autre dépôt s'en empare.

Le `baseURL` de `hugo.toml` vaut `https://magieduchaos.org/` : le site n'est correct qu'à cette adresse, pas sur `dkuster.github.io/MagieDuChaos/`.

Pour prévisualiser le build de production en local, le servir plutôt que l'ouvrir par double-clic :

```
hugo --gc --minify --cleanDestinationDir
python -m http.server 8080 -d public    # http://localhost:8080
```

## Reconversion depuis WordPress

Le dump SQL et la copie de l'ancien site restent **hors du dépôt**. Pour régénérer le contenu :

```sh
python3 tools/wp2hugo/wp2hugo.py \
  --dump  /chemin/isabelle_iot-2026-11-04_00_39.sql \
  --uploads /chemin/burgundi.thanateros.org/wp-content/uploads \
  --out .
```

Prérequis : Python 3.10+, `pandoc`, `Pillow`. Le script n'efface rien : vider `content/` et `static/files/` avant de le relancer. `tools/wp2hugo/url-map.csv` liste les anciennes URL et leur équivalent.
