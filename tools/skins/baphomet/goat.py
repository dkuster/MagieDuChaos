"""Filigrane : tête de bouc en traits fins (dessin original), symétrique.
Demi-tête droite dessinée une fois puis reflétée ; cornes annelées calculées le long d'une Bézier ;
étoile du chaos à 8 flèches au front, flamme entre les cornes, lune blanche et lune noire dans le cadre."""
import math, sys
from geom import *

INK = "#1d1712"

def horn():
    ctrl = ((18, -52), (24, -106), (64, -138), (106, -136))
    wf = lambda t: 20 * (1 - t) ** 0.85 + 0.6
    L, R = tapered(ctrl, 0, 0, n=48, wfun=wf)
    outline = polyline(L + R[::-1], close=True)
    ribs = []
    for i in range(1, 15):
        t = i / 15.5
        c = bez(*ctrl, t); d = bez_d(*ctrl, t); nr = normal(d); w = wf(t) / 2
        l = math.hypot(*d); tx, ty = d[0]/l, d[1]/l
        a = (c[0] + nr[0]*w, c[1] + nr[1]*w); b = (c[0] - nr[0]*w, c[1] - nr[1]*w)
        m = (c[0] + tx*w*0.45, c[1] + ty*w*0.45)   # anneau légèrement bombé vers la pointe
        ribs.append(f"M{pt(a)} Q{pt(m)} {pt(b)}")
    return outline, ribs

def half():
    p = []
    # contour de la tête avec l'oreille, du front au bout du museau
    p.append("M0 -58 C14 -58 25 -53 31 -42 C52 -47 80 -40 104 -22 C82 -11 57 -9 38 -14 "
             "C38 8 32 30 25 48 C20 62 18 77 14 88 C11 96 6 101 0 102")
    p.append("M44 -34 C62 -35 80 -30 94 -22")                          # pli de l'oreille
    p.append("M5 -26 C13 -31 23 -30 31 -24")                            # arcade
    p.append("M6 -12 C11 -19 22 -21 29 -15 C22 -8 12 -7 6 -12Z")        # œil en amande
    p.append("M4 0 C6 30 8 60 10 84")                                   # arête du chanfrein
    p.append("M3 94 C6 90 11 90 12 95")                                 # naseau
    # barbe en pointe et ses mèches
    p.append("M24 52 C31 86 23 130 0 172")
    p.append("M20 84 C24 104 20 126 12 148")
    p.append("M14 100 C17 122 13 142 6 160")
    p.append("M7 107 C8 124 6 138 2 150")
    ho, ribs = horn()
    return p, ho, ribs

def flame(cx, base, h, w):
    return (f"M{f(cx)} {f(base)} C{f(cx-w)} {f(base-h*.25)} {f(cx-w*.55)} {f(base-h*.6)} {f(cx-w*.1)} {f(base-h*.78)} "
            f"C{f(cx-w*.05)} {f(base-h*.9)} {f(cx+w*.2)} {f(base-h*.95)} {f(cx)} {f(base-h)} "
            f"C{f(cx+w*.5)} {f(base-h*.7)} {f(cx+w)} {f(base-h*.4)} {f(cx)} {f(base)}Z")

def crescent(cx, cy, r, off, rot):
    # croissant : grand arc extérieur et arc intérieur décalé
    a = math.radians(rot)
    r2 = r * 0.82
    # points de jonction : intersections des deux cercles
    d = off
    x = (d*d + r*r - r2*r2) / (2*d); y = math.sqrt(max(r*r - x*x, 0))
    ca, sa = math.cos(a), math.sin(a)
    T = lambda px, py: (cx + px*ca - py*sa, cy + px*sa + py*ca)
    p1, p2 = T(x, -y), T(x, y)
    return f"M{pt(p1)} A{f(r)} {f(r)} 0 1 0 {pt(p2)} A{f(r2)} {f(r2)} 0 1 1 {pt(p1)}Z"

def svg(opacity=1.0, bg=None):
    parts, ho, ribs = half()
    star = chaos_star(0, -36, 13, shaft=0.12, head=0.36, hub=0.25)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="-200 -200 400 400" width="400" height="400">']
    if bg: out.append(f'<rect x="-200" y="-200" width="400" height="400" fill="{bg}"/>')
    out.append(f'<g fill="none" stroke="{INK}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" opacity="{opacity}">')
    out.append('<defs><g id="h">' + "".join(f'<path d="{d}"/>' for d in parts)
               + f'<path d="{ho}"/>' + f'<path d="{" ".join(ribs)}" stroke-width="1.1"/>'
               + '<ellipse cx="17.5" cy="-13.3" rx="4.2" ry="1.5" fill="' + INK + '" stroke="none"/></g></defs>')
    out.append('<use xlink:href="#h"/><use xlink:href="#h" transform="scale(-1 1)"/>')
    out.append(f'<path d="{flame(0, -60, 50, 11)}"/>')
    out.append(f'<path d="{flame(0, -62, 28, 5.5)}" stroke-width="1.1"/>')
    out.append(f'<circle cx="0" cy="-36" r="3.4" fill="{INK}" stroke="none"/>')
    out.append(f'<path d="{" ".join(polyline(a, True) for a in star)}" fill="{INK}" stroke="none"/>')
    out.append('<circle r="190"/><circle r="183" stroke-width="0.8"/>')
    out.append(f'<path d="{crescent(-152, -52, 15, 6, 200)}"/>')
    out.append(f'<path d="{crescent(152, 52, 15, 6, 20)}" fill="{INK}"/>')
    out.append('</g></svg>')
    return "\n".join(out)

if __name__ == "__main__":
    # usage : python3 goat.py <racine du dépôt>            → filigrane publié (traits à 7,5 % d'opacité)
    #         python3 goat.py <fichier.svg> 1 "#efe6d2"    → aperçu opaque sur fond parchemin
    import os
    a = sys.argv[1]
    if a.endswith(".svg"):
        open(a, "w").write(svg(float(sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 else None))
    else:
        d = os.path.join(a, "themes/baphomet/static/images/skins/baphomet")
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "filigrane.svg"), "w", encoding="utf-8").write(svg(0.075) + "\n")
