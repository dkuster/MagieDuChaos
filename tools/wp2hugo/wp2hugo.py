#!/usr/bin/env python3
"""Conversion ponctuelle du WordPress « Magie du Chaos » vers Hugo.

Lit directement le dump SQL (pas besoin de WordPress ni de MySQL) et le dossier
wp-content/uploads de la copie de l'ancien site, puis écrit :
  content/            articles (page bundles), pages, termes de taxonomies
  static/files/       PDF référencés
  tools/wp2hugo/url-map.csv   correspondance ancienne URL -> nouvelle URL

Ne reprend volontairement : ni comptes, ni commentaires, ni données de
formulaires (Flamingo), ni pages protégées par mot de passe, ni brouillons.
Aucun fichier autre que jpg/jpeg/png/pdf n'est copié ; les images sont
ré-encodées (métadonnées supprimées).

Usage :
  python3 wp2hugo.py --dump chemin/dump.sql --uploads chemin/wp-content/uploads --out racine-du-depot
"""
import argparse, csv, html, json, os, re, shutil, subprocess, sys
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wpdump

# --------------------------------------------------------------------------
# Paramètres propres au site
# --------------------------------------------------------------------------
OLD_HOSTS = ['https://burgundi.thanateros.live', 'http://burgundi.thanateros.live',
             'https://burgundi.thanateros.org', 'http://burgundi.thanateros.org']
TZ = ZoneInfo('Europe/Zurich')
HOME_PAGE_ID = '28'
SKIP_PAGE_IDS = {'29'}  # page « Blog » vide : remplacée par la liste Hugo /blog/
# Contact Form 7 -> clé de formulaire Tally (les ID Tally sont dans hugo.toml)
FORMS = {'30': 'renseignements', '80f4e41': 'adhesion', '689': 'adhesion'}
# [download id="…"] -> PDF du Livre du Pacte, édition 2024 (décision du 11.11.2026)
DOWNLOADS = {'121': ('/files/IOT-Le-Livre-2024.pdf',
                     'Télécharger le Livre du Pacte (PDF, édition 2024)')}
# Catégories parentes -> taxonomies Hugo
TAXO_PARENTS = {"Type d'écrit": 'types', 'Source': 'sources'}
IMG_EXT = {'.jpg', '.jpeg', '.png'}
FILE_EXT = {'.pdf'}
MAX_SIDE = 2560

warnings = []
def warn(msg):
    warnings.append(msg); print('ATTENTION :', msg, file=sys.stderr)

# --------------------------------------------------------------------------
def q(s):
    """Chaîne YAML sûre (JSON est un sous-ensemble de YAML)."""
    return json.dumps(s, ensure_ascii=False)

def to_iso(wp_date):
    return datetime.strptime(wp_date, '%Y-%m-%d %H:%M:%S').replace(tzinfo=TZ).isoformat()

def strip_size(path):
    return re.sub(r'-\d+x\d+(\.\w+)$', r'\1', path)

class Media:
    def __init__(self, uploads, out, attachments):
        self.uploads, self.out, self.att = uploads, out, attachments
        self.copied = {}

    def resolve(self, url_or_path, att_id=None):
        """Retourne le chemin relatif dans uploads du fichier original, ou None."""
        if att_id and att_id in self.att:
            rel = self.att[att_id]
            if os.path.isfile(os.path.join(self.uploads, rel)):
                return rel
        m = re.search(r'/wp-content/uploads/(.+)$', url_or_path)
        rel = m.group(1) if m else url_or_path
        rel = rel.split('?')[0]
        for cand in (rel, strip_size(rel)):
            if os.path.isfile(os.path.join(self.uploads, cand)):
                return cand if cand == rel and not re.search(r'-\d+x\d+\.\w+$', rel) else cand
        return None

    def copy(self, rel, dest_dir):
        """Copie (ré-encode) un média dans dest_dir. Retourne le nom de fichier."""
        ext = os.path.splitext(rel)[1].lower()
        name = os.path.basename(rel)
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, name)
        src = os.path.join(self.uploads, rel)
        if ext in IMG_EXT:
            from PIL import Image, ImageOps
            im = Image.open(src)
            im = ImageOps.exif_transpose(im)
            if max(im.size) > MAX_SIDE:
                im.thumbnail((MAX_SIDE, MAX_SIDE))
            if ext in ('.jpg', '.jpeg'):
                im.convert('RGB').save(dest, 'JPEG', quality=86, optimize=True, progressive=True)
            else:
                im.save(dest, 'PNG', optimize=True)
        elif ext in FILE_EXT:
            with open(src, 'rb') as f:
                if f.read(5) != b'%PDF-':
                    warn(f'{rel} ne commence pas comme un PDF, ignoré'); return None
            shutil.copyfile(src, dest)
        else:
            warn(f'extension refusée : {rel}'); return None
        self.copied[dest] = rel
        return name

# --------------------------------------------------------------------------
class Converter:
    def __init__(self, media, footnotes_meta):
        self.media = media
        self.fn_meta = footnotes_meta

    def convert(self, html_in, bundle_dir, label):
        ph = []  # placeholders : (token, markdown)
        def keep(md):
            tok = f'ZZPH{len(ph)}ZZ'; ph.append((tok, md)); return f'<p>{tok}</p>'
        def keep_inline(md):
            tok = f'ZZPH{len(ph)}ZZ'; ph.append((tok, md)); return tok

        c = html_in
        # « Lire la suite »
        c = re.sub(r'<!--\s*wp:more\s*-->.*?<!--\s*/wp:more\s*-->', lambda m: keep('<!--more-->'), c, flags=re.S)
        c = re.sub(r'<!--more-->', lambda m: keep('<!--more-->'), c)
        c = re.sub(r'<!--\s*/?wp:[^>]*-->', '', c)

        # Notes de bas de page Gutenberg
        fn_order = []
        def fn_sub(m):
            fid = m.group(1)
            if fid not in fn_order: fn_order.append(fid)
            return keep_inline(f'[^{fn_order.index(fid) + 1}]')
        c = re.sub(r'<sup data-fn="([^"]+)"[^>]*>.*?</sup>', fn_sub, c, flags=re.S)

        # Intégrations YouTube
        def yt_id(url):
            m = re.search(r'(?:v=|youtu\.be/)([\w-]{6,})', url)
            return m.group(1) if m else None
        c = re.sub(r'<figure class="wp-block-embed[^"]*youtube[^"]*">.*?(https?://\S+?)\s*</div>.*?</figure>',
                   lambda m: keep(f'{{{{< youtube {yt_id(m.group(1))} >}}}}'), c, flags=re.S)
        c = re.sub(r'\[su_youtube[^\]]*url="([^"]+)"[^\]]*\]',
                   lambda m: keep(f'{{{{< youtube {yt_id(m.group(1))} >}}}}'), c)

        # Formulaires
        def cf7(m):
            fid = m.group(1)
            if fid not in FORMS: warn(f'{label} : formulaire CF7 inconnu {fid}'); return ''
            return keep(f'{{{{< tally "{FORMS[fid]}" >}}}}')
        c = re.sub(r'<div class="wp-block-contact-form-7-contact-form-selector">\s*\[contact-form-7 id="([^"]+)"[^\]]*\]\s*</div>', cf7, c)
        c = re.sub(r'\[contact-form-7 id="([^"]+)"[^\]]*\]', cf7, c)

        # Téléchargements
        def dl(m):
            href, text = DOWNLOADS[m.group(1)]
            return keep(f'[{text}]({href})')
        c = re.sub(r'\[download id="(\d+)"\]', dl, c)

        # Images (figure WordPress) -> shortcode figure
        def fig(m):
            block = m.group(0)
            img = re.search(r'<img [^>]*>', block).group(0)
            src = re.search(r'src="([^"]+)"', img).group(1)
            alt = html.unescape((re.search(r'alt="([^"]*)"', img) or [None, ''])[1])
            att = (re.search(r'wp-image-(\d+)', img) or [None, None])[1]
            cap = re.search(r'<figcaption[^>]*>(.*?)</figcaption>', block, re.S)
            cap = html.unescape(re.sub(r'<[^>]+>', '', cap.group(1))).strip() if cap else ''
            width = re.search(r'width:\s*(\d+)px', img)
            align = 'aligncenter' if 'aligncenter' in block else ''
            rel = self.media.resolve(src, att)
            if not rel: warn(f'{label} : image introuvable {src}'); return ''
            name = self.media.copy(rel, bundle_dir)
            args = [f'src={q(name)}', f'alt={q(alt)}']
            if cap: args.append(f'caption={q(cap)}')
            if width: args.append(f'width="{width.group(1)}"')
            if align: args.append(f'class="{align}"')
            return keep('{{< figure ' + ' '.join(args) + ' >}}')
        c = re.sub(r'(?:<div class="wp-block-image">\s*)?<figure class="wp-block-image.*?</figure>(?:\s*</div>)?', fig, c, flags=re.S)

        # Images isolées (hors bloc figure)
        def lone_img(m):
            img = m.group(0)
            src = re.search(r'src="([^"]+)"', img).group(1)
            alt = html.unescape((re.search(r'alt="([^"]*)"', img) or [None, ''])[1])
            att = (re.search(r'wp-image-(\d+)', img) or [None, None])[1]
            rel = self.media.resolve(src, att)
            if not rel: warn(f'{label} : image introuvable {src}'); return ''
            name = self.media.copy(rel, bundle_dir)
            return keep('{{< figure ' + f'src={q(name)} alt={q(alt)}' + ' >}}')
        c = re.sub(r'(?:<a [^>]*>\s*)?<img [^>]*>(?:\s*</a>)?', lone_img, c)

        # Liens vers des fichiers de uploads (PDF) -> /files/
        def file_link(m):
            url = m.group(1)
            rel = self.media.resolve(url)
            if rel and os.path.splitext(rel)[1].lower() in FILE_EXT:
                name = self.media.copy(rel, os.path.join(self.media.out, 'static', 'files'))
                return f'href="/files/{name}"'
            if rel is None: warn(f'{label} : fichier lié introuvable {url}')
            return m.group(0)
        hosts = '|'.join(re.escape(h) for h in OLD_HOSTS)
        c = re.sub(rf'href="((?:{hosts})/wp-content/uploads/[^"]+)"', file_link, c)
        # Liens internes absolus -> chemins relatifs à la racine
        c = re.sub(rf'(href=")(?:{hosts})(/[^"]*)?"', lambda m: f'{m.group(1)}{m.group(2) or "/"}"', c)

        # Nettoyage : soulignés, divs, attributs inutiles
        c = re.sub(r'<span style="text-decoration: underline;">(.*?)</span>', r'<u>\1</u>', c, flags=re.S)
        c = re.sub(r'</?div[^>]*>', '', c)

        md = subprocess.run(['pandoc', '-f', 'html', '-t', 'gfm', '--wrap=none'],
                            input=c, capture_output=True, text=True, check=True).stdout
        md = re.sub(r'\n<!-- end list -->\n', '', md)
        md = re.sub(r'<span class="underline">(.*?)</span>', r'<u>\1</u>', md)
        for tok, val in ph:
            md = md.replace(tok, val)
        if 'ZZPH' in md: warn(f'{label} : marqueur non remplacé')

        if fn_order:
            notes = {n['id']: n['content'] for n in self.fn_meta}
            defs = []
            for i, fid in enumerate(fn_order, 1):
                body = subprocess.run(['pandoc', '-f', 'html', '-t', 'gfm', '--wrap=none'],
                                      input=notes.get(fid, ''), capture_output=True, text=True, check=True).stdout.strip()
                if fid not in notes: warn(f'{label} : note {fid} sans texte')
                defs.append(f'[^{i}]: {body}')
            md = md.rstrip() + '\n\n' + '\n'.join(defs) + '\n'
        return md.strip() + '\n'

# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dump', required=True)
    ap.add_argument('--uploads', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()

    T = wpdump.load(a.dump, ['wp_posts', 'wp_postmeta', 'wp_users', 'wp_terms',
                             'wp_term_taxonomy', 'wp_term_relationships', 'wp_options'])
    posts = T['wp_posts']
    meta = {}
    for m in T['wp_postmeta']:
        meta.setdefault(m['post_id'], {})[m['meta_key']] = m['meta_value']
    users = {u['ID']: u['display_name'] for u in T['wp_users']}
    terms = {t['term_id']: html.unescape(t['name']) for t in T['wp_terms']}
    tt = {t['term_taxonomy_id']: t for t in T['wp_term_taxonomy']}
    cats = {}
    for r in T['wp_term_relationships']:
        t = tt.get(r['term_taxonomy_id'])
        if not t or t['taxonomy'] != 'category' or t['parent'] == '0': continue
        parent = terms.get(t['parent'])
        if parent in TAXO_PARENTS:
            lst = cats.setdefault(r['object_id'], {}).setdefault(TAXO_PARENTS[parent], [])
            if terms[t['term_id']] not in lst: lst.append(terms[t['term_id']])
    attachments = {p['ID']: meta.get(p['ID'], {}).get('_wp_attached_file') for p in posts if p['post_type'] == 'attachment'}

    out = a.out
    media = Media(a.uploads, out, attachments)
    url_map = []

    def common_fm(p):
        return [f'title: {q(html.unescape(p["post_title"]))}',
                f'date: {to_iso(p["post_date"])}',
                f'lastmod: {to_iso(p["post_modified"])}']

    def featured(p, bundle):
        tid = meta.get(p['ID'], {}).get('_thumbnail_id')
        if not tid: return []
        rel = media.resolve('', tid)
        if not rel: warn(f'image à la une introuvable pour {p["post_name"]}'); return []
        name = media.copy(rel, bundle)
        return [f'image: {q(name)}'] if name else []

    published = [p for p in posts if p['post_status'] == 'publish' and not p['post_password']]

    # Articles
    n_posts = 0
    for p in sorted([p for p in published if p['post_type'] == 'post'], key=lambda p: p['post_date']):
        slug = p['post_name']
        bundle = os.path.join(out, 'content', 'posts', slug)
        conv = Converter(media, json.loads(meta.get(p['ID'], {}).get('footnotes') or '[]'))
        body = conv.convert(p['post_content'], bundle, slug)
        fm = common_fm(p) + [f'slug: {q(slug)}', f'author: {q(users.get(p["post_author"], ""))}']
        for tax in ('types', 'sources'):
            vals = cats.get(p['ID'], {}).get(tax, [])
            if vals: fm.append(f'{tax}: [{", ".join(q(v) for v in vals)}]')
        if p['post_excerpt'].strip():
            fm.append(f'summary: {q(html.unescape(p["post_excerpt"].strip()))}')
        fm += featured(p, bundle)
        if not body.strip(): warn(f'article vide : {slug}')
        os.makedirs(bundle, exist_ok=True)
        with open(os.path.join(bundle, 'index.md'), 'w') as f:
            f.write('---\n' + '\n'.join(fm) + '\n---\n\n' + body)
        d = datetime.strptime(p['post_date'], '%Y-%m-%d %H:%M:%S')
        url_map.append((f'/{d:%Y/%m/%d}/{slug}/', f'/{d:%Y/%m/%d}/{slug}/', 'article'))
        n_posts += 1

    # Pages
    n_pages = 0
    for p in [p for p in published if p['post_type'] == 'page']:
        if p['ID'] in SKIP_PAGE_IDS: continue
        if p['ID'] == HOME_PAGE_ID:
            bundle = os.path.join(out, 'content'); fname = '_index.md'; url = '/'
        else:
            bundle = os.path.join(out, 'content', p['post_name']); fname = 'index.md'; url = f'/{p["post_name"]}/'
        conv = Converter(media, json.loads(meta.get(p['ID'], {}).get('footnotes') or '[]'))
        body = conv.convert(p['post_content'], bundle, p['post_name'] or 'accueil')
        fm = common_fm(p) + featured(p, bundle)
        os.makedirs(bundle, exist_ok=True)
        with open(os.path.join(bundle, fname), 'w') as f:
            f.write('---\n' + '\n'.join(fm) + '\n---\n\n' + body)
        url_map.append((url, url, 'page'))
        n_pages += 1

    # Termes de taxonomies (titres + anciennes URL /category/…)
    from collections import Counter
    seen = Counter()
    for c in cats.values():
        for tax, vals in c.items():
            for v in vals: seen[(tax, v)] += 1
    for (tax, name), n in sorted(seen.items()):
        slug = subprocess.run(['python3', '-c', 'import sys,unicodedata,re;s=unicodedata.normalize("NFKD",sys.argv[1]).encode("ascii","ignore").decode().lower();print(re.sub(r"[^a-z0-9]+","-",s).strip("-"))', name],
                              capture_output=True, text=True).stdout.strip()
        d = os.path.join(out, 'content', tax, slug)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, '_index.md'), 'w') as f:
            f.write(f'---\ntitle: {q(name)}\naliases: [{q("/category/" + slug + "/")}]\n---\n')
        url_map.append((f'/category/{slug}/', f'/{tax}/{slug}/', f'catégorie ({n})'))
    for tax, title in (('types', "Type d'écrit"), ('sources', 'Source')):
        os.makedirs(os.path.join(out, 'content', tax), exist_ok=True)
        with open(os.path.join(out, 'content', tax, '_index.md'), 'w') as f:
            f.write(f'---\ntitle: {q(title)}\n---\n')
    with open(os.path.join(out, 'content', 'posts', '_index.md'), 'w') as f:
        f.write('---\ntitle: "Blog"\n---\n')
    url_map.append(('/blog/', '/blog/', 'liste des articles'))

    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'url-map.csv'), 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['ancienne_url', 'nouvelle_url', 'type']); w.writerows(url_map)

    print(f'{n_posts} articles, {n_pages} pages, {len(seen)} termes, {len(media.copied)} médias copiés')
    print(f'{len(warnings)} avertissement(s)')

if __name__ == '__main__':
    main()
