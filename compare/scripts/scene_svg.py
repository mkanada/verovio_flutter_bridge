#!/usr/bin/env python3
"""Desenha uma página do `.vsb` como SVG (só para evidência visual do G08c).

Lê a cena e os glifos e aplica o que a referência (`hide_ref.py`) manda: nós `note`/`chord`
escondidos não são pintados (a letra, `verse`, fica), as formas filhas diretas das barras escondidas
e os traços de linha suplementar escondidos também não, e a pausa substituta entra numa cor à parte.
Não é o renderizador do host: não há paridade a medir aqui, só olhar.
"""
import os, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hide_ref as hr

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SVG_RENDER = os.path.join(ROOT, "compare/svg_render/target/release/svg_render")
FONTS = [os.path.join(ROOT, p) for p in (
    "verovio/fonts/Leipzig/Leipzig.ttf", "verovio/data/text/LiberationSerif-Regular.ttf",
    "verovio/data/text/LiberationSerif-Italic.ttf", "verovio/data/text/LiberationSerif-Bold.ttf")]


def path_d(doc_paths, tx=lambda x, y: (x, y)):
    d = []
    for p in doc_paths:
        v, i, o = p["v"], p["i"], p["o"]
        n = len(v) // 2
        if n == 0:
            continue
        pts = [tx(v[2 * k], v[2 * k + 1]) for k in range(n)]
        d.append("M%g %g" % pts[0])
        for k in range(n - 1):
            c1 = tx(v[2 * k] + o[2 * k], v[2 * k + 1] + o[2 * k + 1])
            c2 = tx(v[2 * k + 2] + i[2 * k + 2], v[2 * k + 3] + i[2 * k + 3])
            d.append("C%g %g %g %g %g %g" % (c1 + c2 + pts[k + 1]))
        if p.get("closed"):
            c1 = tx(v[2 * (n - 1)] + o[2 * (n - 1)], v[2 * (n - 1) + 1] + o[2 * (n - 1) + 1])
            c2 = tx(v[0] + i[0], v[1] + i[1])
            d.append("C%g %g %g %g %g %g" % (c1 + c2 + pts[0]))
            d.append("Z")
    return " ".join(d)


def style(s, cur, default_stroke=True):
    fill = s.get("fill", cur)
    stroke = s.get("stroke", cur)
    if fill == "none":
        fill = "none"
    sw = s.get("strokeWidth", 0)
    out = 'fill="%s"' % fill
    if stroke != "none" and sw:
        out += ' stroke="%s" stroke-width="%g"' % (stroke, sw)
        cap = s.get("lineCap")
        if cap in ("butt", "round", "square"):
            out += ' stroke-linecap="%s"' % cap
    else:
        out += ' stroke="none"'
    return out


class Painter:
    def __init__(self, doc, hidden, stand=None, stand_color="#d4380d", hide_color=None):
        self.doc = doc
        self.hidden = hidden
        self.stand = stand
        self.stand_color = stand_color
        self.notes = set(hidden["notes"]) if hidden else set()
        self.chords = set(hidden["chords"]) if hidden else set()
        self.beams = {b["id"] for b in hidden["beams"]} if hidden else set()
        self.ledgers = {tuple(l[:3]) + (l[3], l[4]) for l in hidden["ledgers"]} if hidden else set()
        self.out = []

    def node(self, n, cur, staff):
        cl = hr.classes(n)
        if n.get("hidden"):
            return
        cur = n.get("color", cur)
        if cl[:1] == ["staff"]:
            staff = n
        nid = n.get("id")
        if cl[:1] == ["note"] and nid in self.notes or cl[:1] == ["chord"] and nid in self.chords:
            # a nota some; a letra (verse) fica
            self.verses(n, cur)
            return
        hide_direct = cl[:1] == ["beam"] and nid in self.beams
        hide_ledger = cl[:1] == ["ledgerLines"]
        for c in n.get("children", []):
            t = c.get("t")
            if t == "g":
                self.node(c, cur, staff)
            elif hide_direct:
                continue
            elif hide_ledger and t == "p":
                side, k, x1, x2, y = hr.dash_of(staff, c, False)
                if (staff["id"], side, k, round(x1, 1), round(x2, 1)) in self.ledgers:
                    continue
                self.shape(c, cur)
            else:
                self.shape(c, cur)

    def verses(self, n, cur):
        for c in n.get("children", []):
            if c.get("t") == "g":
                cur2 = c.get("color", cur)
                if "verse" in hr.classes(c):
                    self.node(c, cur2, None)
                else:
                    self.verses(c, cur2)

    def shape(self, s, cur):
        t = s["t"]
        if t == "p":
            self.out.append('<path d="%s" %s/>' % (path_d(s["paths"]), style(s, cur)))
        elif t == "r":
            self.out.append('<rect x="%g" y="%g" width="%g" height="%g" %s/>' % (s["x"], s["y"], s["w"], s["h"], style(s, cur)))
        elif t == "e":
            self.out.append('<ellipse cx="%g" cy="%g" rx="%g" ry="%g" %s/>' % (s["cx"], s["cy"], s["rx"], s["ry"], style(s, cur)))
        elif t == "u":
            self.glyph(s, cur)
        elif t == "t":
            anchor = {"left": "start", "center": "middle", "right": "end"}.get(s.get("align"), "start")
            self.out.append('<text x="%g" y="%g" font-size="%g" text-anchor="%s" font-family="Liberation Serif"%s%s fill="%s">%s</text>' % (
                s["x"], s["y"], s["size"], anchor, ' font-weight="bold"' if s.get("bold") else "",
                ' font-style="italic"' if s.get("italic") else "", cur, s["s"].replace("&", "&amp;").replace("<", "&lt;")))

    def glyph(self, u, cur, color=None):
        g = self.doc.glyphs[u["g"]]
        d = path_d(g["paths"], lambda x, y: (u["x"] + x * u["sx"], u["y"] + y * u["sy"]))
        self.out.append('<path d="%s" fill="%s" stroke="none"/>' % (d, color or cur))

    def page(self, root, crop):
        self.out = []
        self.node(root, "#000000", None)
        if self.stand:
            s = self.stand
            self.glyph(dict(g=s["glyph"], x=s["x"], y=s["y"], sx=s["sx"], sy=s["sy"]), None, self.stand_color)
            for d in s["dots"]:
                self.out.append('<ellipse cx="%g" cy="%g" rx="%g" ry="%g" fill="%s"/>' % (d["cx"], d["cy"], d["rx"], d["ry"], self.stand_color))
        x0, y0, x1, y1 = crop
        return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="%g %g %g %g" width="%d" height="%d">'
                '<rect x="%g" y="%g" width="%g" height="%g" fill="white"/>%s</svg>') % (
            x0, y0, x1 - x0, y1 - y0, int((x1 - x0) / 10 * 2), int((y1 - y0) / 10 * 2),
            x0, y0, x1 - x0, y1 - y0, "".join(self.out))


def render_png(doc, ref, res, crop, path, ghost_color="#d4380d"):
    """Desenha a página `ref` com `res` (saída de hide_ref.run) e grava `path` (.png). `crop` no
    referencial de conteúdo (viewBox, antes do translate(origin))."""
    root = doc.page_root(ref)
    p = Painter(doc, res["hidden"], res["standIn"], ghost_color)
    svg = p.page(root, crop)
    svgp = path[:-4] + ".svg"
    open(svgp, "w").write(svg)
    cmd = [SVG_RENDER, svgp, path] + [a for f in FONTS for a in ("--font", f)] + ["--pin-serif-family", "Liberation Serif"]
    subprocess.run(cmd, check=True, capture_output=True)
