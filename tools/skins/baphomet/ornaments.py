"""Ornements du skin baphomet : flambeau, séparateur (lunes et pentagramme), caducée.
Tracés calculés ici ; les partials Hugo sont régénérés par ce script, ne pas les retoucher à la main."""
import math
from geom import *
from goat import crescent, flame

def torch():
    # hampe effilée et ses ligatures, coupe, trois flammes superposées
    hampe = polyline([(-3.6, 6), (3.6, 6), (1.9, 52), (-1.9, 52)], True)
    bands = " ".join(f"M{f(-3.6 + (y-6)*1.7/46 - .4)} {f(y)} L{f(3.6 - (y-6)*1.7/46 + .4)} {f(y)}" for y in (12, 17, 40))
    coupe = "M-10 -4 L10 -4 L5 6 L-5 6Z"
    rim = "M-11 -4.5 L11 -4.5"
    return f'''<svg class="baphomet-torch" viewBox="-30 -66 60 120" aria-hidden="true" focusable="false">
  <defs><radialGradient id="baphomet-halo"><stop offset="0" class="halo-in"/><stop offset="1" class="halo-out"/></radialGradient></defs>
  <circle class="torch-halo" cx="0" cy="-22" r="30" fill="url(#baphomet-halo)"/>
  <g class="torch-flame">
    <path class="flame-outer" d="{flame(0, -3, 50, 13)}"/>
    <path class="flame-mid" d="{flame(0, -3, 34, 8.5)}"/>
    <path class="flame-core" d="{flame(0, -3, 18, 4.5)}"/>
  </g>
  <path class="torch-shaft" d="{hampe} {coupe}"/>
  <path class="torch-bands" d="{bands} {rim}"/>
</svg>'''

def divider():
    pent = star_points(0, 0, 9.5, 9.5, n=5)  # sommets 0,2,4,… du polygone : r_in = r_out
    verts = [pent[i] for i in range(0, 10, 2)]
    star = "M" + " L".join(pt(verts[i]) for i in (0, 2, 4, 1, 3)) + "Z"
    def rule(x0, x1):
        return f"M{f(x0)} -1.6 L{f(x1)} -1.6 M{f(x0)} 1.6 L{f(x1)} 1.6"
    dots = " ".join(f"M{f(x)} -2.6 L{f(x+2.6)} 0 L{f(x)} 2.6 L{f(x-2.6)} 0Z" for x in (-58, 58))
    return f'''<div class="baphomet-divider" role="separator">
  <svg viewBox="-130 -18 260 36" aria-hidden="true" focusable="false">
    <path class="rule" d="{rule(-128, -61)} {rule(-55, -40)} {rule(40, 55)} {rule(61, 128)}"/>
    <path class="dot" d="{dots}"/>
    <path class="moon-white" d="{crescent(-25, -5, 8, 3.4, 180)}"/>
    <circle class="pentacle-ring" r="12.5"/>
    <path class="pentacle" d="{star}"/>
    <path class="moon-black" d="{crescent(25, 5, 8, 3.4, 0)}"/>
  </svg>
</div>'''

def caduceus():
    staff = polyline([(-1.9, 4), (1.9, 4), (1.6, -108), (-1.6, -108)], True)
    snakes = []
    for s in (1, -1):
        pts = []
        for i in range(0, 72):
            y = -4 - i
            a = 13 - 4 * i / 71
            pts.append((s * a * math.sin(2 * math.pi * (i + 6) / 44 * 1.0), y))
        snakes.append(polyline(pts))
    # têtes : petites amandes en bout de corps, tournées l'une vers l'autre
    heads = []
    for s in (1, -1):
        x, y = (s * 9 * math.sin(2 * math.pi * 77 / 44), -75)   # bout du corps, au plus loin de la hampe
        d = 1 if x < 0 else -1                                   # la tête regarde vers la hampe
        heads.append(f"M{f(x - d*1.5)} {f(y-3.2)} C{f(x + d*2.5)} {f(y-5.6)} {f(x + d*6)} {f(y-3)} {f(x + d*6.6)} {f(y-.6)} "
                     f"C{f(x + d*4.5)} {f(y+1.8)} {f(x + d*1)} {f(y+3)} {f(x - d*1.5)} {f(y+3.2)}Z")
    feathers = []
    for s in (1, -1):
        for k in range(5):
            r0 = (s * 2, -95 + k * 2.4)
            ang = math.radians(62 - k * 12)          # rémiges relevées, de la plus haute à la plus basse
            L = 32 - k * 3.5
            tip = (s * (2 + L * math.cos(ang)), r0[1] - L * math.sin(ang))
            ctrl = (r0, (r0[0] + s * L * .45, r0[1] - 2), (tip[0] - s * L * .15, tip[1] + L * .25), tip)
            Lp, Rp = tapered(ctrl, 0, 0, n=16, wfun=lambda t: 6.5 * (1 - t) ** .6 + .4)
            feathers.append(polyline(Lp + Rp[::-1], True))
    return f'''<svg class="baphomet-caduceus" viewBox="-44 -128 88 132" aria-hidden="true" focusable="false">
  <path class="wings" d="{" ".join(feathers)}"/>
  <path class="staff" d="{staff}"/>
  <path class="snake" d="{snakes[0]}"/>
  <path class="snake" d="{snakes[1]}"/>
  <path class="snake-head" d="{" ".join(heads)}"/>
  <circle class="orb" cy="-113" r="5"/>
</svg>'''

HEAD = "{{- /* %s Tracé généré par tools/skins/baphomet/ornaments.py : ne pas retoucher à la main. */ -}}\n"

if __name__ == "__main__":
    # usage : python3 ornaments.py <racine du dépôt>
    import sys, os
    d = os.path.join(sys.argv[1], "themes/baphomet/layouts/_partials/skins/baphomet")
    os.makedirs(d, exist_ok=True)
    files = {
        "baphomet-torch.html": (HEAD % "Flambeau entre les cornes : hampe, coupe, trois flammes qui vacillent (voir skin.css).", torch()),
        "divider.html": (HEAD % "Séparateur : lune blanche en haut, pentagramme pointe en haut, lune noire en bas.", divider()),
        "baphomet-caduceus.html": (HEAD % "Caducée planté dans le pied de page : hampe, deux serpents, ailes, globe.", caduceus()),
    }
    for name, (head, body) in files.items():
        open(os.path.join(d, name), "w", encoding="utf-8").write(head + body + "\n")
