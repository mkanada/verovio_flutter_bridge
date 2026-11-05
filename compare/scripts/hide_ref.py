#!/usr/bin/env python3
"""Implementação de referência da nota escondida (docs/formato/especificacao-v1.md §11, G08c).

Lê um `.vsb` (cena + glifos + pitchpos) e, para uma página (normal ou alternativa), calcula:

 * `hidden_shapes(doc, page, ids)` — o que a cena apaga quando as notas `ids` (o conjunto H de
   TODAS as notas escondidas) somem: as notas, os acordes inteiros escondidos (regra 1), as
   formas da barra de ligação (regra 2) e os traços de linha suplementar (regra 3);
 * `stand_in(doc, page, ids)` — a pausa que ocupa o lugar da coluna `ids` (regras 4-7): glifo, x,
   y, escala e os pontos de aumento; `None` quando não há pausa substituta.

G11 (regra 8, compasso inteiro): `hidden_measures(doc, page, measure_ids)` e `measure_stand_in(...)`
calculam o que some e a pausa de compasso substituta (uma `mRest` por pauta de desenho) quando os
compassos `measure_ids` são escondidos por inteiro.

É a régua contra a qual o host valida a porta Dart (vetores em docs/formato/sumico/vetores.json).

Uso:
  hide_ref.py --self-test                          confere todos os vetores
  hide_ref.py <arquivo.vsb> <pagina> <id[,id...]>  imprime hidden_shapes e stand_in (JSON)
  hide_ref.py --measures <arquivo.vsb> <pagina> <id[,id...]>  idem, com os COMPASSOS escondidos por inteiro (G11)
                                                   (<pagina>: 0-based, ou altN.M = sequência N, página M)
"""
import json, os, sys, zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ghost_ref as gr

REST_CP = {1: "E4E3", 2: "E4E4", 4: "E4E5", 8: "E4E6", 16: "E4E7", 32: "E4E8", 64: "E4E9"}   # regra 5
HEAD_SLACK = 1.0     # regra 3: folga de 1 unidade de viewBox
CONTROL_CLASSES = ("tie", "slur", "phrase", "arpeg", "beamSpan")   # regra 8: controles de dono = compassos que tocam
TOL = 0.5            # tolerância dos vetores (unidades de viewBox)


class Doc(gr.Vsb):
    """`ghost_ref.Vsb` + páginas alternativas + timemap."""

    def __init__(self, path):
        super().__init__(path)
        z = zipfile.ZipFile(path)
        names = z.namelist()
        self.alt = json.loads(z.read("alternates.json"))["sequences"] if "alternates.json" in names else []
        self.timemap = json.loads(z.read("timemap.json")) if "timemap.json" in names else []

    def page_root(self, ref):
        """`ref`: int (página normal, 0-based) ou 'alt<N>.<M>' (sequência N, página M)."""
        if isinstance(ref, int) or (isinstance(ref, str) and ref.isdigit()):
            return self.pages[int(ref)]["root"]
        n, m = ref[3:].split(".")
        return self.alt[int(n)]["pages"][int(m)]["root"]

    def all_page_roots(self):
        for i, p in enumerate(self.pages):
            yield i, p["root"]
        for si, s in enumerate(self.alt):
            for pi, p in enumerate(s["pages"]):
                yield "alt%d.%d" % (si, pi), p["root"]


def classes(n):
    return n.get("class", "").split()


class PageIx:
    """Índice de uma página: pautas, notas (com a pauta de desenho), acordes, barras e traços."""

    def __init__(self, root):
        self.staffs = {}          # id -> nó staff
        self.notes = {}           # id -> (nó, staff de desenho)
        self.chords = {}          # id -> nó
        self.chord_of = {}        # id da nota -> id do acorde (nota de acorde)
        self.rests = {}           # id -> (nó, staff de desenho)
        self.beams = []           # (nó, [ancestrais])
        self.ledgers = []         # (nó ledgerLines, staff, [formas p])
        self.measures = {}        # id -> (nó measure, nó system)   (G11)
        self.measure_of = {}      # id da nota/pausa -> id do compasso
        self.tuplets = []         # nós tuplet
        self.controls = []        # (nó de controle ancorado, nó system)
        self._staff_obj = []
        self._system = None
        self._measure = None
        self._walk(root, [], None)
        for d in (self.notes, self.rests):
            for nid, (n, st) in list(d.items()):
                if isinstance(st, str):
                    d[nid] = (n, self.staffs[st])

    def _walk(self, n, anc, staff):
        cl = classes(n)
        if cl[:1] == ["system"]:
            self._system = n
        if cl[:1] == ["measure"] and "id" in n:
            self.measures[n["id"]] = (n, self._system)
            self._measure = n["id"]
        if cl[:1] == ["tuplet"]:
            self.tuplets.append(n)
        if cl[:1] and cl[0] in CONTROL_CLASSES and anc and classes(anc[-1])[:1] in (["measure"], ["system"]):
            self.controls.append((n, self._system))
        if cl[:1] == ["staff"]:
            staff = n
            if "id" in n:
                self.staffs[n["id"]] = n
        if cl[:1] == ["note"] and "id" in n:
            self.notes[n["id"]] = (n, n["staff"] if "staff" in n else staff)
            self.measure_of[n["id"]] = self._measure
        if cl[:1] in (["rest"], ["mRest"], ["multiRest"]) and "id" in n:
            self.rests[n["id"]] = (n, n["staff"] if "staff" in n else staff)
            self.measure_of[n["id"]] = self._measure
        if cl[:1] == ["chord"] and "id" in n:
            self.chords[n["id"]] = n
            for x in note_descendants(n):
                self.chord_of[x["id"]] = n["id"]
        if cl[:1] == ["beam"]:
            self.beams.append((n, anc))
        if cl[:1] == ["ledgerLines"] and staff is not None:
            self.ledgers.append((n, staff, [s for s in _shapes(n) if s.get("t") == "p"]))
        for c in n.get("children", []):
            if c.get("t") == "g":
                self._walk(c, anc + [n], staff)


def _shapes(n):
    for c in n.get("children", []):
        if c.get("t") == "g":
            yield from _shapes(c)
        else:
            yield c


def note_descendants(n):
    out = []
    for c in n.get("children", []):
        if c.get("t") == "g":
            if classes(c)[:1] == ["note"] and "id" in c:
                out.append(c)
            out.extend(note_descendants(c))
    return out


def head_us(note):
    """Os `u` de dentro do nó `notehead` da nota."""
    out = []

    def rec(n, in_head):
        in_head = in_head or "notehead" in classes(n)
        for c in n.get("children", []):
            if c.get("t") == "u" and in_head:
                out.append(c)
            elif c.get("t") == "g":
                rec(c, in_head)
    rec(note, False)
    return out


def head_extent(doc, note):
    """[xl, xr]: extensão horizontal dos vértices do contorno de cada glifo da cabeça (regra 3)."""
    xl, xr = None, None
    for u in head_us(note):
        xs = doc.glyphs[u["g"]]["paths"]
        vx = [v for p in xs for v in p["v"][0::2]]
        if not vx:
            continue
        a, b = u["x"] + min(vx) * u["sx"], u["x"] + max(vx) * u["sx"]
        xl = a if xl is None else min(xl, a)
        xr = b if xr is None else max(xr, b)
    return None if xl is None else (xl, xr)


def dash_of(staff, shape, cue_group):
    """(lado, ordem k, x1, x2, y) de um traço de linha suplementar."""
    top, unit, n = staff["lines"]
    v = shape["paths"][0]["v"]
    x1, y, x2 = v[0], v[1], v[2]
    bottom = top + 2 * (n - 1) * unit
    if y < top:
        return "above", int(round((top - y) / (2 * unit))), min(x1, x2), max(x1, x2), y
    return "below", int(round((y - bottom) / (2 * unit))), min(x1, x2), max(x1, x2), y


def rest_extent(doc, node):
    xs = [(u["x"] + min(v for p in doc.glyphs[u["g"]]["paths"] for v in p["v"][0::2]) * u["sx"],
           u["x"] + max(v for p in doc.glyphs[u["g"]]["paths"] for v in p["v"][0::2]) * u["sx"])
          for u in node.get("children", []) if u.get("t") == "u"]
    return (min(a for a, _ in xs), max(b for _, b in xs)) if xs else None


def dash_owners(doc, ix, staff, side, k, a, b):
    """Donas do traço (regra 3): notas da pauta de desenho cuja cabeça ele cobre e cujo `loc` o alcança;
    mais as pausas deslocadas (id `rest:<id>`), que o host nunca esconde, então o traço delas fica."""
    top, unit, n = staff["lines"]
    owners = []
    for rid, (node, st) in ix.rests.items():
        if st is not staff:
            continue
        ext = rest_extent(doc, node)
        us = [c for c in node.get("children", []) if c.get("t") == "u"]
        if ext is None or not us:
            continue
        if not (a - HEAD_SLACK <= ext[0] and ext[1] <= b + HEAD_SLACK):
            continue
        loc = 2 * (n - 1) - (us[0]["y"] - top) / unit
        if (side == "above" and loc >= 2 * (n - 1) + 2 * k - 0.01) or (side == "below" and loc <= -2 * k + 0.01):
            owners.append("rest:" + rid)
    for nid, (node, st) in ix.notes.items():
        if st is not staff:
            continue
        ev = doc.pitchpos.get(nid)
        if not ev or ev["t"] != "n":
            continue
        ext = head_extent(doc, node)
        if ext is None:
            continue
        if not (a - HEAD_SLACK <= ext[0] and ext[1] <= b + HEAD_SLACK):
            continue
        loc = ev["loc"]
        if (side == "above" and loc >= 2 * (n - 1) + 2 * k) or (side == "below" and loc <= -2 * k):
            owners.append(nid)
    return owners


def hidden_shapes(doc, root, ids, ix=None, hidden_rests=()):
    """O que some quando as notas `ids` (H, todas as escondidas) somem. Ver §11, regras 1-3.
    `hidden_rests` (G11, regra 8): pausas de verdade que o host também esconde (compasso inteiro);
    contam como donas escondidas de um traço de linha suplementar."""
    ix = ix or PageIx(root)
    H = set(ids)
    HR = set(hidden_rests)
    out = dict(notes=sorted(i for i in H if i in ix.notes), chords=[], beams=[], ledgers=[])
    for cid, c in ix.chords.items():
        nd = note_descendants(c)
        if nd and all(x["id"] in H for x in nd):
            out["chords"].append(cid)
    out["chords"].sort()
    for b, _ in ix.beams:
        nd = note_descendants(b)
        direct = [c for c in b.get("children", []) if c.get("t") != "g"]
        if nd and direct and all(x["id"] in H for x in nd):
            out["beams"].append(dict(id=b.get("id"), shapes=len(direct)))
    out["beams"].sort(key=lambda d: d["id"] or "")
    for g, staff, shapes in ix.ledgers:
        for s in shapes:
            side, k, x1, x2, y = dash_of(staff, s, "cue" in classes(g))
            own = dash_owners(doc, ix, staff, side, k, x1, x2)
            if own and all(o in H or (o.startswith("rest:") and o[5:] in HR) for o in own):
                out["ledgers"].append([staff["id"], side, k, round(x1, 1), round(x2, 1)])
    out["ledgers"].sort()
    return out


def rest_loc(dur, n):
    """Regra 6: `loc` da pausa padrão (sem ajuste por camada)."""
    loc = n - 1
    if dur < 4 and loc % 2 != 0:
        loc -= 1
    if dur == 1 and n > 1:
        loc += 2
    return loc


def rest_dots(doc, glyph_id, x, dur, dots, loc, top, unit, n, sx):
    """Regra 6, pontos de aumento (View::DrawDots + CalcDotsFunctor::VisitRest)."""
    if dots < 1:
        return []
    loc_dot = loc
    if loc_dot % 2 == 0:
        loc_dot += 1
    if dur in (32, 64):
        loc_dot += 2
    x_rel = int(doc.glyph_width(glyph_id, sx)) if dur > 2 else int(2.5 * unit)   # o Verovio trunca (int)
    x0 = x + x_rel + unit
    y = top + (2 * (n - 1) - loc_dot) * unit
    r = max(2 * unit / 5, 2)
    return [dict(cx=x0 + j * 1.5 * unit, cy=y, rx=r, ry=r) for j in range(dots)]


def stand_in(doc, root, column, ix=None):
    """A pausa que substitui a coluna `column` (ids notados): regras 4-7. `None` = sem pausa."""
    ix = ix or PageIx(root)
    notes = [ix.notes[i] for i in column]
    staffs = {id(st) for _, st in notes}
    if len(staffs) != 1:
        raise ValueError("a coluna tem de ser de uma pauta de desenho só")
    staff = notes[0][1]
    top, unit, n = staff["lines"]
    if n != 5:
        return None
    figs = []
    for i in column:
        ev = doc.pitchpos.get(i)
        if not ev or "dur" not in ev:
            return None
        figs.append((ev["dur"], ev.get("dots", 0)))
    dur = max(d for d, _ in figs)
    dots = min(p for d, p in figs if d == dur)
    cp = REST_CP.get(dur)
    gid = "%s:%s" % (doc.font, cp) if cp else None
    if gid is None or gid not in doc.glyphs:
        return None
    xs = [u["x"] for nd, _ in notes for u in head_us(nd)]
    if not xs:
        return None
    x = min(xs)
    loc = rest_loc(dur, n)
    sx, sy = staff["gs"]
    y = top + (2 * (n - 1) - loc) * unit
    return dict(glyph=gid, dur=dur, x=x, y=y, sx=sx, sy=sy, loc=loc, dots=rest_dots(doc, gid, x, dur, dots, loc, top, unit, n, sx))


# ---------------------------------------------------------------- compasso inteiro (G11, regra 8)
MREST_CP = "E4E3"        # a semibreve centrada; E4E2 (breve) em compasso de 2 semibreves ou mais não é reservada
DOUBLE_Q = 8.0           # View::DrawMRest: `GetMaxTime() >= 2` semibreves = 8 semínimas (qstamp)


def measure_len_q(doc, measure_id):
    """Duração do compasso em semínimas (qstamp), do timemap embutido; `None` sem timemap."""
    pts = []
    for e in doc.timemap:
        if "measureOn" in e:
            pts.append((e["qstamp"], e["measureOn"]))
    end = doc.timemap[-1]["qstamp"] if doc.timemap else None
    for k, (q, mid) in enumerate(pts):
        if mid.split("-rend")[0] == measure_id.split("-rend")[0]:
            nxt = pts[k + 1][0] if k + 1 < len(pts) else end
            return None if nxt is None else nxt - q
    return None


def measure_extent(m):
    """[x0, x1] da pauta do compasso: o primeiro traço de linha de cada pauta."""
    xs = []
    for st in m.get("children", []):
        if st.get("t") == "g" and classes(st)[:1] == ["staff"]:
            for c in st.get("children", []):
                if c.get("t") == "p":
                    v = c["paths"][0]["v"]
                    xs += [v[0], v[2]]
                    break
    return (min(xs), max(xs)) if xs else None


def control_key(n):
    """Chave de um controle ancorado: o `id`, ou `classe@x0,y0,x1,y1` (bbox, 1 casa) nos que o Verovio
    desenha no nível do sistema, sem id (metades de ligadura que cruzam a quebra de sistema)."""
    if "id" in n:
        return n["id"]
    return "%s@%s" % (classes(n)[0], ",".join("%.1f" % v for v in n["bbox"]))


def leaf_ids(n, out=None):
    """ids dos nós `note` e `rest` descendentes de `n` (a nota de dentro de um `chord` conta)."""
    out = [] if out is None else out
    for c in n.get("children", []):
        if c.get("t") == "g":
            if classes(c)[:1] in (["note"], ["rest"]) and "id" in c:
                out.append(c["id"])
            leaf_ids(c, out)
    return out


def measure_staffs(ix, mid):
    """{id da pauta de desenho: nó staff} dos nós `staff` filhos do compasso."""
    m = ix.measures[mid][0]
    return {st["id"]: st for st in m.get("children", [])
            if st.get("t") == "g" and classes(st)[:1] == ["staff"] and "id" in st}


def measure_columns(ix, mid):
    """Por pauta de desenho do compasso: (ids das notas desenhadas nela, ids das pausas desenhadas nela)."""
    notes, rests = {}, {}
    for nid, (_, st) in ix.notes.items():
        if ix.measure_of.get(nid) == mid:
            notes.setdefault(st["id"], []).append(nid)
    for rid, (_, st) in ix.rests.items():
        if ix.measure_of.get(rid) == mid:
            rests.setdefault(st["id"], []).append(rid)
    return notes, rests


def hidden_measures(doc, root, measure_ids, ix=None):
    """Regra 8: o que some quando os compassos `measure_ids` são escondidos por inteiro.
    Pauta de desenho sem nenhuma nota no compasso fica como está (a pausa que existe já está lá);
    pauta com notas perde as notas e as pausas de verdade."""
    ix = ix or PageIx(root)
    M = set(measure_ids)
    notes, rests = [], []
    for mid in sorted(M):
        n_by, r_by = measure_columns(ix, mid)
        for sid, ids in n_by.items():
            notes += ids
            rests += [r for r in r_by.get(sid, []) if "mRest" not in classes(ix.rests[r][0])]
    out = hidden_shapes(doc, root, notes, ix, hidden_rests=rests)
    out["rests"] = sorted(rests)
    H, HR = set(notes), set(rests)
    out["tuplets"] = sorted(t["id"] for t in ix.tuplets if "id" in t and leaf_ids(t)
                            and all(i in H or i in HR for i in leaf_ids(t)))
    ctl = []
    ext = {mid: measure_extent(ix.measures[mid][0]) for mid in ix.measures}
    for n, system in ix.controls:
        if "bbox" not in n or not n.get("children"):
            continue
        x0, _, x1, _ = n["bbox"]
        touched = [mid for mid, (_, sy) in ix.measures.items()
                   if sy is system and ext[mid] and min(x1, ext[mid][1]) - max(x0, ext[mid][0]) > HEAD_SLACK]
        if touched and all(mid in M for mid in touched):
            ctl.append(control_key(n))
    out["controls"] = sorted(ctl)
    return out


def mrest_geometry(doc, ix, measure_id, staff):
    """Glifo, x, y e escala da pausa de compasso de `staff` (nó staff do compasso), pela regra 8.
    `None` se não houver (sem `inner`, 2 semibreves ou mais, glifo ausente, `n != 5`)."""
    m = ix.measures[measure_id][0]
    inner = m.get("inner")
    if inner is None:
        return None
    q = measure_len_q(doc, measure_id)
    if q is not None and q >= DOUBLE_Q:
        return None
    gid = "%s:%s" % (doc.font, MREST_CP)
    top, unit, n = staff["lines"]
    if gid not in doc.glyphs or n != 5:
        return None
    sx, sy = staff["gs"]
    cx = inner[0] + int(inner[1] - inner[0]) // 2          # Measure::GetInnerCenterX (divisão inteira)
    x = cx - int(doc.glyph_width(gid, sx)) // 2             # View::DrawMRest: x -= largura / 2
    loc = rest_loc(1, n)                                    # mesma conta da semibreve (regra 6)
    return dict(g=gid, x=x, y=top + (2 * (n - 1) - loc) * unit, sx=sx, sy=sy)


def measure_stand_in(doc, root, measure_id, ix=None):
    """Pausa de compasso substituta de um compasso escondido (regra 8): uma por pauta de desenho que
    tem nota no compasso (`[]` onde `mrest_geometry` não dá nada)."""
    ix = ix or PageIx(root)
    notes, _ = measure_columns(ix, measure_id)
    out = []
    for sid, st in measure_staffs(ix, measure_id).items():
        if sid in notes:
            g = mrest_geometry(doc, ix, measure_id, st)
            if g:
                out.append(dict(measure=measure_id, staff=sid, **g))
    return out


def run_measures(doc, ref, measure_ids):
    root = doc.page_root(ref)
    ix = PageIx(root)
    return dict(hidden=hidden_measures(doc, root, measure_ids, ix),
                measureStandIn=[r for mid in sorted(measure_ids) for r in measure_stand_in(doc, root, mid, ix)])



def run(doc, ref, column, hidden=None):
    """Conjunto completo para uma página: o que some e a pausa."""
    root = doc.page_root(ref)
    ix = PageIx(root)
    H = set(hidden if hidden is not None else column)
    return dict(hidden=hidden_shapes(doc, root, H, ix), standIn=stand_in(doc, root, column, ix))


# ---------------------------------------------------------------- self-test
def close(a, b, tol=TOL):
    if isinstance(a, dict):
        return isinstance(b, dict) and set(a) == set(b) and all(close(a[k], b[k], tol) for k in a)
    if isinstance(a, list):
        return isinstance(b, list) and len(a) == len(b) and all(close(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return abs(a - b) <= tol
    return a == b


def summary(res):
    """O `resumo` (o que o `resumo` à mão de cada caso diz): contagens e pausa."""
    h, s = res["hidden"], res["standIn"]
    return dict(notes=len(h["notes"]), chords=len(h["chords"]), beams=len(h["beams"]), ledgers=len(h["ledgers"]),
                rest=(s["glyph"].split(":")[1] if s else None), restLoc=(s["loc"] if s else None),
                dots=(len(s["dots"]) if s else 0))


def self_test():
    here = os.path.dirname(os.path.abspath(__file__))
    base = os.path.join(here, "..", "..", "docs", "formato", "sumico")
    vec = json.load(open(os.path.join(base, "vetores.json")))
    docs, bad = {}, 0
    for case in vec["casos"]:
        doc = docs.setdefault(case["vsb"], Doc(os.path.join(base, case["vsb"])))
        got = json.loads(json.dumps(run(doc, case["pagina"], case["coluna"], case.get("escondidas"))))
        if summary(got) != case["resumo"]:
            print("RESUMO diverge:", case["nome"], "esperado", case["resumo"], "obtido", summary(got)); bad += 1
        if not close(got, case["esperado"]):
            print("NÚMEROS divergem:", case["nome"]); bad += 1
    for case in vec.get("casosCompasso", []):     # G11, regra 8
        doc = docs.setdefault(case["vsb"], Doc(os.path.join(base, case["vsb"])))
        got = json.loads(json.dumps(run_measures(doc, case["pagina"], set(case["compassos"]))))
        h = got["hidden"]
        resumo = dict(notes=len(h["notes"]), chords=len(h["chords"]), beams=len(h["beams"]), ledgers=len(h["ledgers"]),
                      rests=len(h["rests"]), tuplets=len(h["tuplets"]), controls=len(h["controls"]),
                      standIns=len(got["measureStandIn"]))
        if resumo != case["resumo"]:
            print("RESUMO (compasso) diverge:", case["nome"], "esperado", case["resumo"], "obtido", resumo); bad += 1
        if not close(got, case["esperado"]):
            print("NÚMEROS (compasso) divergem:", case["nome"]); bad += 1
    print("%d casos + %d de compasso, %d divergências" % (len(vec["casos"]), len(vec.get("casosCompasso", [])), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
        sys.exit(self_test())
    if len(sys.argv) == 5 and sys.argv[1] == "--measures":
        d = Doc(sys.argv[2])
        print(json.dumps(run_measures(d, sys.argv[3], set(sys.argv[4].split(","))), indent=1))
        sys.exit(0)
    if len(sys.argv) == 4:
        d = Doc(sys.argv[1])
        ids = sys.argv[3].split(",")
        print(json.dumps(run(d, sys.argv[2], ids), indent=1))
        sys.exit(0)
    print(__doc__)
    sys.exit(2)
