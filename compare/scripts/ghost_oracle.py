#!/usr/bin/env python3
"""Oráculo Verovio da nota fantasma (G04d).

Dois testes, sobre o corpus (+ corpus/fantasma):

 * swap: para um alvo (nota esperada E, tecla k), a fórmula (ghost_ref.py) diz pauta, `loc` (antes
   do deslocamento de oitava), acidente e linhas suplementares. Uma CÓPIA MEI da partitura com E
   trocada pela grafia prevista é renderizada pelo próprio Verovio; a cabeça de E na cena da cópia
   tem de cair no `loc` previsto (medido contra as linhas da PRÓPRIA cópia), com o acidente e o nº
   de linhas suplementares previstos. No máximo um alvo por (compasso, pauta) por cópia.
 * self: para toda nota E do corpus, a fantasma da tecla que E soa tem de reproduzir E: mesmo
   `loc` e a mesma decisão de desenhar (ou não) acidente que a partitura original tomou.

Também mede a folga entre o acidente e a cabeça (mediana, em `unit`).

Uso: ghost_oracle.py [--targets N] [--seed S] [--out compare/out/g04d] [--jobs J] [--skip-swap]
"""
import argparse, csv, glob, json, os, random, statistics, subprocess, sys, time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ghost_ref as gr

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
VEROVIO = os.path.join(ROOT, "verovio/tools/verovio")
RES = os.path.join(ROOT, "verovio/data")
MEI_NS = "http://www.music-encoding.org/ns/mei"
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"
ET.register_namespace("", MEI_NS)
ET.register_namespace("xml", "http://www.w3.org/XML/1998/namespace")
ACC_CODE = {"E262": "s", "E260": "f", "E261": "n"}
DELTAS = [1, -1, 2, -2, 3, -3, 12, -12]


def run(args, **kw):
    return subprocess.run([VEROVIO, "--resource-path", RES] + args, check=True, capture_output=True, **kw)


def to_mei(src, out):
    run(["-t", "mei", "--xml-id-seed", "42", "-o", out, src])


def to_vsb(mei, out):
    run(["-t", "vsb", "--xml-id-seed", "7", "-o", out, mei])  # semente != 42 (a do -t mei): senão ids gerados colidem com os do MEI


def walk(n, anc=()):
    yield n, anc
    for c in n.get("children", []):
        if c.get("t") == "g":
            yield from walk(c, anc + (n,))


def scene_info(doc):
    """id -> dict(node, staff, measure, pageIdx) para notas e pausas da cena."""
    info = {}
    for pi, page in enumerate(doc.pages):
        for n, anc in walk(page["root"]):
            cls = n.get("class", "").split()
            if "id" in n and cls[:1] and cls[0] in ("note", "rest", "mRest", "multiRest"):
                staff = next((a for a in reversed(anc) if a.get("class", "").split()[:1] == ["staff"]), None)
                if "staff" in n:
                    staff = doc.staffs.get(n["staff"], staff)
                meas = next((a for a in reversed(anc) if a.get("class", "").split()[:1] == ["measure"]), None)
                info[n["id"]] = dict(node=n, staff=staff, measure=meas.get("id") if meas else None, page=pi)
    return info


def head_u(node):
    return gr.first_u(node, True)


def accid_glyph(node):
    for n, _ in walk(node):
        if "accid" in n.get("class", "").split():
            for c in n["children"]:
                if c.get("t") == "u":
                    return c["g"].split(":")[1], c, n
    return None, None, None


def measured_ledgers(staff, hx, hw, hy):
    """Linhas suplementares na coluna da cabeça (x) entre a pauta e a cabeça (y), inclusive a da cabeça:
    as de outras notas da coluna, mais afastadas que esta, não contam."""
    top, unit, n = staff["lines"]
    bottom = top + 2 * (n - 1) * unit
    ys = set()
    for c in staff["children"]:
        if c.get("t") == "g" and "ledgerLines" in c.get("class", "").split():
            for d in walk(c):
                for s in d[0].get("children", []):
                    if s.get("t") == "p":
                        v = s["paths"][0]["v"]
                        x1, y, x2 = v[0], v[1], v[2]
                        if not (x1 <= hx + hw and x2 >= hx):
                            continue
                        if (y < top and y >= hy - 0.5) or (y > bottom and y <= hy + 0.5):
                            ys.add(round(y, 1))
    return len(ys)


def build_piece(name, src, work):
    mei = os.path.join(work, name + ".mei")
    vsb = os.path.join(work, name + ".vsb")
    to_mei(src, mei)
    to_vsb(mei, vsb)
    return mei, vsb


def note_elements(root):
    return {e.get(XML_ID): e for e in root.iter("{%s}note" % MEI_NS) if e.get(XML_ID)}


def edit_note(el, pname, octv, alt, accid_glyph_code):
    for a in ("accid", "accid.ges", "pname.ges", "oct.ges"):
        el.attrib.pop(a, None)
    for ch in list(el):
        if ch.tag == "{%s}accid" % MEI_NS:
            el.remove(ch)
    el.set("pname", gr.LETTERS[pname - 1])
    el.set("oct", str(octv))
    if accid_glyph_code:
        acc = ET.SubElement(el, "{%s}accid" % MEI_NS)
        acc.set("accid", ACC_CODE[accid_glyph_code])
    elif alt:
        el.set("accid.ges", {1: "s", -1: "f", 2: "ss", -2: "ff"}[alt])


def render_copy(job):
    idx, tree_path, edits, work = job
    tree = ET.parse(tree_path)
    notes = note_elements(tree.getroot())
    for nid, pname, octv, alt, acode in edits:
        edit_note(notes[nid], pname, octv, alt, acode)
    mei = os.path.join(work, "copy%04d.mei" % idx)
    tree.write(mei, encoding="utf-8", xml_declaration=True)
    vsb = os.path.join(work, "copy%04d.vsb" % idx)
    to_vsb(mei, vsb)
    return vsb


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", type=int, default=2400)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default=os.path.join(ROOT, "compare/out/g04d"))
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--skip-swap", action="store_true")
    a = ap.parse_args()
    t_start = time.time()
    os.makedirs(a.out, exist_ok=True)
    work = os.path.join(a.out, "work")
    os.makedirs(work, exist_ok=True)
    rnd = random.Random(a.seed)

    sources = sorted(glob.glob(os.path.join(ROOT, "corpus/mei/*.mei")) + glob.glob(os.path.join(ROOT, "corpus/musicxml/*.mxl"))
                     + glob.glob(os.path.join(ROOT, "corpus/fantasma/*.mei")))
    pieces = {}
    for src in sources:
        name = os.path.splitext(os.path.basename(src))[0]
        mei, vsb = build_piece(name, src, work)
        doc = gr.Vsb(vsb)
        pieces[name] = dict(mei=mei, vsb=vsb, doc=doc, info=scene_info(doc))

    # ---------- folga do acidente (medida nas partituras originais)
    gaps = {}
    for name, p in pieces.items():
        for nid, inf in p["info"].items():
            if not nid in p["doc"].pitchpos or p["doc"].pitchpos[nid]["t"] != "n":
                continue
            code, au, _ = accid_glyph(inf["node"])
            hu = head_u(inf["node"])
            if code and au and hu and inf["staff"] and hu["sy"] == inf["staff"]["gs"][1]:
                aw = p["doc"].glyph_width(au["g"], au["sx"])
                gaps.setdefault(inf["staff"]["lines"][1], []).append((hu["x"] - (au["x"] + aw)) / inf["staff"]["lines"][1])
    gap_report = {u: dict(n=len(v), mediana=statistics.median(v), min=min(v), max=max(v)) for u, v in gaps.items()}
    print("folga acidente->cabeça (em unit):", json.dumps(gap_report))

    # ---------- self: a notação da partitura vs. o contexto (`key`/`acc`) e o acidente da fórmula
    GLYPH_ALT = {"E262": 1, "E260": -1, "E261": 0, "E263": 2, "E264": -2}
    self_rows = []
    counts = dict(plain=0, plain_bad=0, drawn=0, drawn_bad=0, ghost_bad=0)
    for name, p in pieces.items():
        doc = p["doc"]
        for nid, inf in p["info"].items():
            ev = doc.pitchpos.get(nid)
            if not ev or ev["t"] != "n" or inf["staff"] is None:
                continue
            code, _, _ = accid_glyph(inf["node"])
            letter = ev["pn"]
            in_force = ev.get("acc", {}).get("%s%d" % (letter, ev["o"]), ev.get("key", {}).get(letter, 0))
            if code is None:
                # sem acidente desenhado: o som tem de ser o em vigor (fonte fiel à notação)
                counts["plain"] += 1
                if ev["alt"] != in_force:
                    counts["plain_bad"] += 1
                    self_rows.append([name, nid, "sem acidente", letter, ev["o"], ev["alt"], in_force, json.dumps(ev.get("key", {})), json.dumps(ev.get("acc", {}))])
            else:
                counts["drawn"] += 1
                if GLYPH_ALT[code] != ev["alt"] and not (code == "E261" and ev["alt"] == 0):
                    counts["drawn_bad"] += 1
                    self_rows.append([name, nid, "acidente " + code, letter, ev["o"], ev["alt"], GLYPH_ALT[code], json.dumps(ev.get("key", {})), json.dumps(ev.get("acc", {}))])
            # a fórmula, com a tecla que a própria nota soa: nunca desenha acidente diferente do em vigor
            k = gr.midi_natural(gr.LETTERS.index(letter) + 1, ev["o"]) + ev["alt"] + ev.get("sh", 0)
            if 0 <= k <= 127:
                g = gr.ghosts(doc, [nid], [k], acc_gap=0)[0]
                if (g["accid"] is not None) != (ev["alt"] != in_force) or (g["loc"] != ev["loc"] and g["m"] == 0):
                    counts["ghost_bad"] += 1
    print("self:", counts)
    with open(os.path.join(a.out, "self-divergencias.csv"), "w", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["peca", "id", "caso", "pn", "o", "alt_som", "esperado", "key", "acc"])
        w.writerows(self_rows)
    self_bad = self_rows

    if a.skip_swap:
        return 0

    # ---------- swap
    pool = []
    for name, p in pieces.items():
        weight = 1
        for nid, inf in p["info"].items():
            ev = p["doc"].pitchpos.get(nid)
            if not ev or ev["t"] != "n" or inf["staff"] is None or head_u(inf["node"]) is None \
                    or inf["node"].get("hidden"):
                continue   # nota oculta (visible=false): o Verovio não desenha nem as linhas suplementares
            pool.append((name, nid))
    fantasma = [x for x in pool if x[0].startswith("f0")]
    others = [x for x in pool if not x[0].startswith("f0")]
    rnd.shuffle(others)
    chosen = [(n, i, d) for (n, i) in fantasma for d in rnd.sample(DELTAS, 4)]
    for (n, i) in others:
        if len(chosen) >= a.targets:
            break
        chosen.append((n, i, rnd.choice(DELTAS + ["far"])))
    # tecla, previsão, agrupamento em cópias
    copies = {}   # name -> list of dict(used=set, edits=[], checks=[])
    skipped = 0
    for name, nid, d in chosen:
        p = pieces[name]
        doc = p["doc"]
        ev = doc.pitchpos[nid]
        inf = p["info"][nid]
        base = gr.midi_natural(gr.LETTERS.index(ev["pn"]) + 1, ev["o"]) + ev["alt"] + ev.get("sh", 0)
        if d == "far":
            k = 21 if base < 64 else 108
            if abs(k - base) < 24:
                k = 108 if k == 21 else 21
        else:
            k = base + d
        if not 0 <= k <= 127:
            skipped += 1
            continue
        g = gr.ghosts(doc, [nid], [k], acc_gap=0)[0]
        if g["target"] != nid:
            skipped += 1
            continue
        key = (inf["measure"], inf["staff"].get("id"))
        pname, octv, alt = gr.LETTERS.index(g["pname"]) + 1, g["oct"], g["alt"]
        acode = g["accid"]["g"].split(":")[1] if g["accid"] else None
        cl = copies.setdefault(name, [])
        for c in cl:
            if key not in c["used"]:
                break
        else:
            c = dict(used=set(), edits=[], checks=[])
            cl.append(c)
        c["used"].add(key)
        c["edits"].append((nid, pname, octv, alt, acode))
        c["checks"].append(dict(name=name, id=nid, key=k, d=d, g=g, acode=acode))
    jobs = []
    meta = []
    for name, cl in copies.items():
        for ci, c in enumerate(cl):
            jobs.append((len(jobs), pieces[name]["mei"], c["edits"], work))
            meta.append(c)
    print("cópias a renderizar:", len(jobs), "alvos:", sum(len(c["checks"]) for c in meta), "descartados:", skipped)
    with ThreadPoolExecutor(a.jobs) as ex:
        vsbs = list(ex.map(render_copy, jobs))

    total = bad = 0
    rows = []
    for vsbp, c in zip(vsbs, meta):
        doc = gr.Vsb(vsbp)
        info = scene_info(doc)
        for chk in c["checks"]:
            g = chk["g"]
            inf = info.get(chk["id"])
            total += 1
            if not inf or not inf["staff"]:
                bad += 1; rows.append([chk["name"], chk["id"], chk["key"], chk["d"], "nota não encontrada", "", "", "", "", "", ""]); continue
            hu = head_u(inf["node"])
            top, unit, n = inf["staff"]["lines"]
            loc = 2 * (n - 1) - (hu["y"] - top) / unit
            code, _, _ = accid_glyph(inf["node"])
            led = measured_ledgers(inf["staff"], hu["x"], doc.glyph_width(hu["g"], hu["sx"]), hu["y"])
            ok = (abs(loc - g["locRaw"]) < 0.01) and (code == chk["acode"]) and (led == g["ledgersRaw"])
            if not ok:
                bad += 1
            rows.append([chk["name"], chk["id"], chk["key"], chk["d"], "ok" if ok else "DIVERGE",
                         g["locRaw"], round(loc, 3), chk["acode"] or "", code or "", g["ledgersRaw"], led])
    with open(os.path.join(a.out, "swap.csv"), "w", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["peca", "id", "tecla", "delta", "resultado", "loc_previsto", "loc_medido", "acidente_previsto",
                    "acidente_medido", "linhas_previstas", "linhas_medidas"])
        w.writerows(rows)
    print("swap: %d alvos, %d divergências, %d cópias renderizadas, %.1f s no total" % (total, bad, len(jobs), time.time() - t_start))
    return 1 if bad or self_bad else 0


sys.exit(main())
