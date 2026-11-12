"""Géométrie partagée : courbes de Bézier, décalages, mise en forme des nombres."""
import math

def f(v):
    s = f"{v:.1f}"
    return "0" if s in ("-0.0", "0.0") else s.rstrip("0").rstrip(".") if "." in s else s

def pt(p):
    return f"{f(p[0])} {f(p[1])}"

def bez(p0, p1, p2, p3, t):
    u = 1 - t
    return (u**3*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3*p3[0],
            u**3*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3*p3[1])

def bez_d(p0, p1, p2, p3, t):
    u = 1 - t
    return (3*u*u*(p1[0]-p0[0]) + 6*u*t*(p2[0]-p1[0]) + 3*t*t*(p3[0]-p2[0]),
            3*u*u*(p1[1]-p0[1]) + 6*u*t*(p2[1]-p1[1]) + 3*t*t*(p3[1]-p2[1]))

def normal(d):
    l = math.hypot(*d) or 1
    return (-d[1]/l, d[0]/l)

def polyline(pts, close=False):
    s = "M" + " L".join(pt(p) for p in pts)
    return s + ("Z" if close else "")

def tapered(ctrl, w0, w1, n=40, wfun=None):
    """Forme effilée le long d'une Bézier : largeur w0 à la base, w1 au bout."""
    left, right = [], []
    for i in range(n + 1):
        t = i / n
        c = bez(*ctrl, t); nr = normal(bez_d(*ctrl, t))
        w = (wfun(t) if wfun else w0 + (w1 - w0) * t) / 2
        left.append((c[0] + nr[0]*w, c[1] + nr[1]*w)); right.append((c[0] - nr[0]*w, c[1] - nr[1]*w))
    return left, right

def star_points(cx, cy, r_out, r_in, n=5, rot=-90):
    pts = []
    for i in range(2 * n):
        r = r_out if i % 2 == 0 else r_in
        a = math.radians(rot + i * 180 / n)
        pts.append((cx + r*math.cos(a), cy + r*math.sin(a)))
    return pts

def chaos_star(cx, cy, r, shaft=0.09, head=0.32, hub=0.2, rot=0):
    """Étoile du chaos à 8 flèches : moyeu + 8 hampes terminées en pointe (un seul tracé par flèche)."""
    arrows = []
    for k in range(8):
        a = math.radians(rot + k * 45 - 90)
        ux, uy = math.cos(a), math.sin(a); nx, ny = -uy, ux
        sw, hw = r*shaft/2, r*head/2
        base = r*hub*0.9; neck = r*0.62; tip = r
        P = lambda d, s: (cx + ux*d + nx*s, cy + uy*d + ny*s)
        arrows.append([P(base, -sw), P(neck, -sw), P(neck, -hw), P(tip, 0), P(neck, hw), P(neck, sw), P(base, sw)])
    return arrows
