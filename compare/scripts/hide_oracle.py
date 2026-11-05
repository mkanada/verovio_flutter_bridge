#!/usr/bin/env python3
"""Oráculo da pausa substituta (G08c, regras 4-6 da §11).

Prova 1 (sem rodar o Verovio de novo): para toda pausa de verdade em pauta de uma camada só, o
`glifo`, o `y`, a escala e os pontos da cena batem com as regras 5 e 6 (pausas em pauta de duas
camadas, em barra, cue ou com posição explícita são contadas à parte).

Prova 2 (rodando o Verovio): sorteia colunas (pauta de desenho × instante) de todo o corpus + hinos,
troca a coluna inteira, numa CÓPIA MEI, por uma pausa de mesma figura (uma camada só; barra
desfeita), renderiza a cópia com `-t vsb` e confere que o Verovio desenha o mesmo glifo, no `y` e
com os pontos que a regra diz. O `x` não se compara (trocar nota por pausa muda o espaçamento).

Uso: hide_oracle.py [--columns N] [--seed S] [--out compare/out/g08c/oraculo] [--jobs J] [--skip-swap]
"""
import argparse, collections, csv, glob, json, os, random, re, subprocess, sys, time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import hide_ref as hr

VEROVIO = os.path.join(ROOT, "verovio/tools/verovio")
RES = os.path.join(ROOT, "verovio/data")
MEI_NS = "http://www.music-encoding.org/ns/mei"
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"
ET.register_namespace("", MEI_NS)
ET.register_namespace("xml", "http://www.w3.org/XML/1998/namespace")
TOL = 0.5


def q(tag):
    return "{%s}%s" % (MEI_NS, tag)


def run_v(args):
    return subprocess.run([VEROVIO, "--resource-path", RES] + args, check=True, capture_output=True)


def sources():
    out = []
    for pat in ("corpus/mei/*.mei", "corpus/musicxml/*.mxl", "corpus/fantasma/*.mei", "corpus/repeticoes/*.mei",
                "corpus/repeticoes/*.musicxml", "corpus/sumico/*.musicxml", "corpus/sumico/*.mei"):
        out += sorted(glob.glob(os.path.join(ROOT, pat)))
    return out


# ------------------------------------------------------------------ expected (prova 1 e 2)
def expected_rest(doc, staff, dur, dots, x):
    """Regras 5 e 6 para uma pausa de figura (dur, dots) em `staff`, com o x dado."""
    top, unit, n = staff["lines"]
    loc = hr.rest_loc(dur, n)
    gid = "%s:%s" % (doc.font, hr.REST_CP[dur])
    return dict(g=gid, y=top + (2 * (n - 1) - loc) * unit, sx=staff["gs"][0], sy=staff["gs"][1],
                dots=hr.rest_dots(doc, gid, x, dur, dots, loc, top, unit, n, staff["gs"][0]))


def scene_dots(node):
    out = []

    def rec(n):
        for c in n.get("children", []):
            if c.get("t") == "e":
                out.append(c)
            elif c.get("t") == "g":
                rec(c)
    for c in node.get("children", []):
        if c.get("t") == "g" and "dots" in hr.classes(c):
            rec(c)
    return out


def check_rest(doc, node, staff, dur, dots):
    """Confere uma pausa desenhada contra as regras; devolve lista de divergências."""
    us = [c for c in node.get("children", []) if c.get("t") == "u"]
    if len(us) != 1:
        return ["glifos=%d" % len(us)]
    u = us[0]
    e = expected_rest(doc, staff, dur, dots, u["x"])
    bad = []
    if u["g"] != e["g"]:
        bad.append("glifo %s != %s" % (u["g"], e["g"]))
    if abs(u["y"] - e["y"]) > TOL:
        bad.append("y %.1f != %.1f" % (u["y"], e["y"]))
    if abs(u["sx"] - e["sx"]) > 1e-3 or abs(u["sy"] - e["sy"]) > 1e-3:
        bad.append("escala %s,%s != %s,%s" % (u["sx"], u["sy"], e["sx"], e["sy"]))
    got = scene_dots(node)
    if len(got) != len(e["dots"]):
        bad.append("pontos %d != %d" % (len(got), len(e["dots"])))
    else:
        for i, (g, w) in enumerate(zip(got, e["dots"])):
            for k in ("cx", "cy", "rx", "ry"):
                if abs(g[k] - w[k]) > TOL:
                    bad.append("ponto %d %s %.1f != %.1f" % (i, k, g[k], w[k]))
    return bad


# ------------------------------------------------------------------ prova 1
def explicit_rests(mei):
    """Pausas com posição explícita na fonte (ploc/oloc ou loc): o Verovio não aplica a regra."""
    return {e.get(XML_ID) for e in ET.parse(mei).getroot().iter(q("rest"))
            if e.get("ploc") or e.get("oloc") or e.get("loc")}


def prova1(docs, meis, out):
    c = collections.Counter()
    rows = []
    for name, doc in docs.items():
        expl = explicit_rests(meis[name])
        for pref, root in doc.all_page_roots():
            ix = hr.PageIx(root)
            xs = {n["staff"] for n, _ in list(ix.notes.values()) + list(ix.rests.values()) if "staff" in n}
            xs |= {n["staff"] for n in ix.chords.values() if "staff" in n}
            for rid, (node, st) in ix.rests.items():
                if rid in expl:
                    c["posicao_explicita(fora)"] += 1
                    continue
                ev = doc.pitchpos.get(rid)
                if not ev or ev.get("dur") not in hr.REST_CP:
                    c["sem_figura(mRest/multiRest/outra)"] += 1
                    continue
                if st is None or st["lines"][2] != 5:
                    c["pauta_nao_5_linhas"] += 1
                    continue
                if st["id"] in xs:
                    c["recebe_cross_staff(fora)"] += 1
                    continue
                nl = sum(1 for x in st.get("children", []) if x.get("t") == "g" and hr.classes(x)[:1] == ["layer"])
                us = [x for x in node.get("children", []) if x.get("t") == "u"]
                if nl != 1:
                    c["pauta_de_%d_camadas(fora)" % nl if nl > 1 else "pauta_sem_camada(fora)"] += 1
                    continue
                if us and abs(us[0]["sx"] - st["gs"][0]) > 1e-3:
                    c["cue(fora)"] += 1
                    continue
                if _in_beam(root, rid):
                    c["em_barra(fora)"] += 1
                    continue
                c["conferidas"] += 1
                bad = check_rest(doc, node, st, ev["dur"], ev.get("dots", 0))
                if bad:
                    c["excecoes"] += 1
                    rows.append([name, pref, rid, ev["dur"], ev.get("dots", 0), "; ".join(bad)])
                if ev.get("dots"):
                    c["conferidas_com_pontos"] += 1
    with open(os.path.join(out, "prova1.csv"), "w", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["peca", "pagina", "id", "dur", "dots", "divergencias"])
        w.writerows(rows)
    print("prova 1:", dict(c))
    for r in rows[:15]:
        print("  ", r)
    return c["excecoes"]


def _in_beam(root, rid):
    def rec(n, in_beam):
        if n.get("id") == rid:
            return in_beam
        for ch in n.get("children", []):
            if ch.get("t") == "g":
                r = rec(ch, in_beam or hr.classes(n)[:1] == ["beam"])
                if r is not None:
                    return r
        return None
    return bool(rec(root, False))


# ------------------------------------------------------------------ colunas
def instants(doc):
    m = {}
    for e in doc.timemap:
        for i in e.get("on", []):
            m.setdefault(re.sub(r"-rend\d+$", "", i), e["qstamp"])
    return m


def columns(doc):
    """Colunas da pauta de desenho (páginas normais): lista de dict(page, staff, ids, qstamp)."""
    inst = instants(doc)
    out = []
    for pi, p in enumerate(doc.pages):
        ix = hr.PageIx(p["root"])
        cols = {}
        for nid, (node, st) in ix.notes.items():
            if st is None:
                continue
            first = nid
            if nid in ix.chord_of:
                first = next(iter(hr.note_descendants(ix.chords[ix.chord_of[nid]])))["id"]
            t = inst.get(first)
            if t is None:
                continue      # continuação de nota ligada: não começa a coluna
            cols.setdefault((st["id"], t), []).append(nid)
        for (sid, t), ids in cols.items():
            out.append(dict(page=pi, staff=sid, qstamp=t, ids=sorted(ids)))
    return out


# ------------------------------------------------------------------ prova 2
def load_mei(path):
    tree = ET.parse(path)
    return tree, {c: p for p in tree.getroot().iter() for c in p}


def mei_substitute(tree, parent, column, new_id, dur, dots):
    """Troca a coluna por uma pausa numa só camada. Devolve False se não for possível."""
    root = tree.getroot()
    byid = {e.get(XML_ID): e for e in root.iter() if e.get(XML_ID)}
    els = [byid.get(i) for i in column]
    if any(e is None or e.tag != q("note") for e in els):
        return False
    if any(e.get("grace") or e.get("staff") for e in els):
        return False
    meas = staff = None
    anc = els[0]
    while anc is not None:
        if anc.tag == q("staff"):
            staff = anc
        if anc.tag == q("measure"):
            meas = anc
        anc = parent.get(anc)
    if staff is None or meas is None:
        return False
    # o mesmo staff para toda a coluna
    for e in els:
        a = e
        while a is not None and a.tag != q("staff"):
            a = parent.get(a)
        if a is not staff:
            return False
    layers = [l for l in staff if l.tag == q("layer")]
    def layer_of(e):
        a = e
        while a is not None and a.tag != q("layer"):
            a = parent.get(a)
        return a
    keep = layer_of(els[0])
    removed_ids = set()
    for l in layers:
        if l is not keep:
            removed_ids |= {e.get(XML_ID) for e in l.iter() if e.get(XML_ID)}
            staff.remove(l)
    # unidades a trocar (acorde inteiro ou nota) na camada mantida
    units = []
    for e in els:
        if layer_of(e) is not keep:
            continue
        u = e
        if parent.get(e) is not None and parent[e].tag == q("chord"):
            u = parent[e]
        if u not in units:
            units.append(u)
    if not units:
        return False
    rest = ET.Element(q("rest"))
    rest.set(XML_ID, new_id)
    rest.set("dur", str(dur))
    if dots:
        rest.set("dots", str(dots))
    first = units[0]
    # desfaz toda barra que contém a unidade (a pausa de barra reposiciona-se pelos vizinhos)
    while True:
        beam = parent[first]
        while beam is not None and beam.tag not in (q("beam"), q("layer")):
            beam = parent.get(beam)
        if beam is None or beam.tag != q("beam"):
            break
        gp = parent[beam]
        idx = list(gp).index(beam)
        kids = list(beam)
        gp.remove(beam)
        for k_, ch in enumerate(kids):
            gp.insert(idx + k_, ch)
            parent[ch] = gp
    par = parent[first]
    idx = list(par).index(first)
    for u in units:
        removed_ids |= {x.get(XML_ID) for x in u.iter() if x.get(XML_ID)}
    par.insert(idx, rest)
    parent[rest] = par
    for u in units:
        pu = parent[u]
        pu.remove(u)
    # controles (ligaduras, dinâmicas, pedais…) que apontam para ids removidos, em qualquer compasso
    gone = {i for i in removed_ids if i}
    for el in list(root.iter()):
        if el.tag in (q("note"), q("rest"), q("chord"), q("layer"), q("staff"), q("measure")):
            continue
        refs = [t.lstrip("#") for a in ("startid", "endid", "plist", "copyof", "sameas") for t in el.get(a, "").split()]
        if any(r in gone for r in refs):
            pr = parent.get(el)
            if pr is not None and el in list(pr):
                pr.remove(el)
    return True


def render_copy(job):
    idx, mei, subs, work = job
    tree, parent = load_mei(mei)
    for column, new_id, dur, dots in subs:
        assert mei_substitute(tree, parent, column, new_id, dur, dots), (mei, column)
    path = os.path.join(work, "copy%04d.mei" % idx)
    tree.write(path, encoding="utf-8", xml_declaration=True)
    vsb = os.path.join(work, "copy%04d.vsb" % idx)
    run_v(["-t", "vsb", "--xml-id-seed", "7", "-o", vsb, path])
    return vsb


def mei_key(tree_parent, column):
    tree, parent = tree_parent
    byid = {e.get(XML_ID): e for e in tree.getroot().iter() if e.get(XML_ID)}
    e = byid[column[0]]
    meas = staff = None
    a = e
    while a is not None:
        if a.tag == q("staff"):
            staff = a
        if a.tag == q("measure"):
            meas = a
        a = parent.get(a)
    return (id(meas), id(staff))


def prova2(docs, meis, a, out, work):
    rnd = random.Random(a.seed)
    # reservatório de colunas viáveis, por figura
    pool = collections.defaultdict(list)
    for name, doc in docs.items():
        for col in columns(doc):
            ixp = None
            fig = []
            ok = True
            for i in col["ids"]:
                ev = doc.pitchpos.get(i)
                if not ev or ev.get("dur") not in hr.REST_CP:
                    ok = False
                    break
                fig.append((ev["dur"], ev.get("dots", 0)))
            if not ok:
                continue
            dur = max(d for d, _ in fig)
            dots = min(p for d, p in fig if d == dur)
            pool[(dur, dots > 0)].append((name, col, dur, dots))
    chosen = []
    per = a.columns
    for key in sorted(pool):
        items = pool[key]
        rnd.shuffle(items)
        chosen += items[:per]
    # agrupa em cópias: no máximo uma coluna por (compasso, pauta MEI) por cópia
    trees = {name: load_mei(meis[name]) for name in docs}
    copies = {}
    skipped = 0
    for name, col, dur, dots in chosen:
        tp = trees[name]
        try:
            key = mei_key(tp, col["ids"])
        except KeyError:
            skipped += 1
            continue
        # a viabilidade (grace, cross-staff…) é conferida em mei_substitute; testa numa cópia descartável
        t2 = ET.ElementTree(ET.fromstring(ET.tostring(tp[0].getroot())))
        p2 = {c: p for p in t2.getroot().iter() for c in p}
        if not mei_substitute(t2, p2, col["ids"], "x", dur, dots):
            skipped += 1
            continue
        cl = copies.setdefault(name, [])
        for c in cl:
            if key not in c["used"]:
                break
        else:
            c = dict(used=set(), subs=[], checks=[])
            cl.append(c)
        c["used"].add(key)
        new_id = "sub-" + col["ids"][0]
        c["subs"].append((col["ids"], new_id, dur, dots))
        c["checks"].append((name, col, new_id, dur, dots))
    jobs, meta = [], []
    for name, cl in copies.items():
        for c in cl:
            jobs.append((len(jobs), meis[name], c["subs"], work))
            meta.append(c)
    print("prova 2: %d colunas sorteadas, %d inviáveis (grace/cross-staff), %d cópias a renderizar" % (
        len(chosen), skipped, len(jobs)))
    with ThreadPoolExecutor(a.jobs) as ex:
        vsbs = list(ex.map(render_copy, jobs))
    total = bad = 0
    stat = collections.Counter()
    rows = []
    for vsbp, c in zip(vsbs, meta):
        d2 = hr.Doc(vsbp)
        for name, col, new_id, dur, dots in c["checks"]:
            total += 1
            found = None
            recv = False
            for pref, root in d2.all_page_roots():
                ix = hr.PageIx(root)
                if new_id in ix.rests:
                    found = ix.rests[new_id]
                    recv = found[1]["id"] in ({n["staff"] for n, _ in ix.notes.values() if "staff" in n}
                                              | {n["staff"] for n in ix.chords.values() if "staff" in n}
                                              | {n["staff"] for n, _ in ix.rests.values() if "staff" in n})
                    break
            stat[(dur, dots > 0)] += 1
            if not found:
                bad += 1
                rows.append([name, new_id, dur, dots, "pausa não encontrada"])
                continue
            node, st = found
            bd = check_rest(d2, node, st, dur, dots)
            if bd and recv:
                stat["recebe_cross_staff(fora)"] += 1
                rows.append([name, new_id, dur, dots, "fora: pauta recebe cross-staff: " + "; ".join(bd)])
                continue
            if bd:
                bad += 1
            rows.append([name, new_id, dur, dots, "ok" if not bd else "; ".join(bd)])
    with open(os.path.join(out, "prova2.csv"), "w", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["peca", "pausa", "dur", "dots", "resultado"])
        w.writerows(rows)
    print("prova 2: %d colunas conferidas, %d divergências, por figura (dur, pontuada):" % (total, bad),
          {(("%d%s" % (k[0], "." if k[1] else "")) if isinstance(k, tuple) else k): v for k, v in sorted(stat.items(), key=str)})
    for r in rows:
        if r[4] != "ok" and not r[4].startswith("fora"):
            print("  ", r)
            break
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--columns", type=int, default=100, help="colunas sorteadas por (figura, pontuada)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default=os.path.join(ROOT, "compare/out/g08c/oraculo"))
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--skip-swap", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    work = os.path.join(a.out, "work")
    os.makedirs(work, exist_ok=True)
    docs, meis = {}, {}
    for s in sources():
        name = os.path.basename(s)
        mei = os.path.join(work, name + ".mei")
        run_v(["-t", "mei", "--xml-id-seed", "42", "-o", mei, s])
        vsb = os.path.join(work, name + ".vsb")
        run_v(["-t", "vsb", "--xml-id-seed", "7", "-o", vsb, mei])   # semente != 42 (a do -t mei): senão ids gerados colidem
        docs[name] = hr.Doc(vsb)
        meis[name] = mei
    bad = prova1(docs, meis, a.out)
    if not a.skip_swap:
        bad += prova2(docs, meis, a, a.out, work)
    print("%.1f s" % (time.time() - t0))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
