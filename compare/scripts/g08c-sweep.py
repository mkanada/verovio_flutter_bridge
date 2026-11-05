#!/usr/bin/env python3
"""G08c: varreduras da regra 3 (linhas suplementares) e da regra 2 (barra) da §11, sobre o corpus.

Regra 3: para todo traço de todo `ledgerLines …` (páginas normais e alternativas), calcula as donas
pela regra e confere (i) todo traço tem ao menos uma dona; (ii) as donas de um traço são sempre da
MESMA coluna (mesma pauta de desenho, mesmo instante no timemap). Falhou -> D-SUM-NATIVO.
Regra 2: todo `beam` tem ao menos uma forma filha direta e ao menos uma `note` descendente;
registra barras aninhadas, entre pautas (cross-staff) e os nós de tremolo.

Uso: g08c-sweep.py [--out compare/out/g08c/sweep]
"""
import argparse, collections, csv, glob, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import hide_ref as hr

VEROVIO = os.path.join(ROOT, "verovio/tools/verovio")
RES = os.path.join(ROOT, "verovio/data")


def sources():
    out = []
    for pat in ("corpus/mei/*.mei", "corpus/musicxml/*.mxl", "corpus/fantasma/*.mei", "corpus/repeticoes/*.mei",
                "corpus/repeticoes/*.musicxml", "corpus/sumico/*.musicxml", "corpus/sumico/*.mei"):
        out += sorted(glob.glob(os.path.join(ROOT, pat)))
    return out


def build(srcs, work):
    os.makedirs(work, exist_ok=True)
    res = {}
    for s in srcs:
        name = os.path.basename(s)
        vsb = os.path.join(work, name + ".vsb")
        subprocess.run([VEROVIO, "-t", "vsb", "--xml-id-seed", "42", "--resource-path", RES, "-o", vsb, s],
                       check=True, capture_output=True)
        res[name] = vsb
    return res


def instants(doc):
    """id notado -> qstamp do `on` (ids expandidos viram o id da cena pelo sufixo -rend<N>)."""
    m = {}
    for e in doc.timemap:
        for i in e.get("on", []):
            m.setdefault(re.sub(r"-rend\d+$", "", i), e["qstamp"])
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "compare/out/g08c/sweep"))
    a = ap.parse_args()
    vsbs = build(sources(), os.path.join(a.out, "vsb"))
    rows3, rows2, bad3 = [], [], []
    tot = collections.Counter()
    for name, path in vsbs.items():
        doc = hr.Doc(path)
        inst = instants(doc)
        c = collections.Counter()
        for pref, root in doc.all_page_roots():
            ix = hr.PageIx(root)
            # ---- regra 3
            for g, staff, shapes in ix.ledgers:
                for s in shapes:
                    side, k, x1, x2, y = hr.dash_of(staff, s, "cue" in hr.classes(g))
                    own = hr.dash_owners(doc, ix, staff, side, k, x1, x2)
                    c["dashes"] += 1
                    if not own:
                        c["sem_dona"] += 1
                        bad3.append((name, pref, "sem dona", staff.get("id"), side, k, round(x1, 1), round(x2, 1)))
                        continue
                    if any(o.startswith("rest:") for o in own):
                        c["com_dona_pausa"] += 1
                        c["so_pausa"] += all(o.startswith("rest:") for o in own)
                        c["pausa_e_nota"] += not all(o.startswith("rest:") for o in own)
                    own = [o for o in own if not o.startswith("rest:")]
                    if not own:
                        continue
                    cols = set()
                    for o in own:
                        oo = ix.chord_of.get(o) and next(iter(hr.note_descendants(ix.chords[ix.chord_of[o]])))["id"] or o
                        cols.add((staff.get("id"), inst.get(oo, inst.get(o, ("sem-instante", round(hr.head_extent(doc, ix.notes[o][0])[0]))))))
                    if len(cols) > 1:
                        c["colunas_diferentes"] += 1
                        # ignora o caso benigno: só difere porque falta instante (continuação ligada)
                        c["colunas_diferentes_com_sem_instante"] += any(isinstance(col[1], tuple) for col in cols)
                        bad3.append((name, pref, "colunas diferentes", staff.get("id"), side, k, round(x1, 1), round(x2, 1),
                                     ";".join("%s@%s" % (o, inst.get(o, "?")) for o in own)))
                    c["donas_total"] += len(own)
            # ---- regra 2
            nbeam_ancestor = 0
            for b, anc in ix.beams:
                c["beams"] += 1
                nd = hr.note_descendants(b)
                direct = [x for x in b.get("children", []) if x.get("t") != "g"]
                if not nd:
                    c["beam_sem_nota"] += 1
                if not direct:
                    c["beam_sem_forma_filha"] += 1
                if any(hr.classes(x)[:1] == ["beam"] for x in anc[::-1]):
                    c["beam_aninhada"] += 1
                if any(hr.classes(x)[:1] == ["beam"] for x in _desc_groups(b)):
                    c["beam_com_beam_dentro"] += 1
                staffs = {id(ix.notes[x["id"]][1]) for x in nd}
                if len(staffs) > 1:
                    c["beam_cross_staff"] += 1
                if any(hr.classes(x)[:1] == ["chord"] for x in _desc_groups(b)):
                    c["beam_com_acorde"] += 1
            for n in _all_groups(root):
                cl = hr.classes(n)[:1]
                if cl and ("trem" in cl[0].lower() or cl[0] in ("beamSpan",)):
                    c["tremolo_ou_beamSpan:" + cl[0]] += 1
        rows3.append([name] + [c[k] for k in ("dashes", "sem_dona", "colunas_diferentes", "colunas_diferentes_com_sem_instante", "so_pausa", "pausa_e_nota")])
        rows2.append([name] + [c[k] for k in ("beams", "beam_sem_nota", "beam_sem_forma_filha", "beam_aninhada",
                                              "beam_com_beam_dentro", "beam_cross_staff", "beam_com_acorde")]
                     + [";".join("%s=%d" % (k.split(":")[1], v) for k, v in sorted(c.items()) if k.startswith("tremolo"))])
        tot.update(c)
    with open(os.path.join(a.out, "regra3.csv"), "w", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["peca", "tracos", "sem_dona", "donas_de_colunas_diferentes", "dessas_por_falta_de_instante", "so_de_pausa", "de_pausa_e_nota"])
        w.writerows(rows3)
    with open(os.path.join(a.out, "regra2.csv"), "w", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["peca", "beams", "sem_nota", "sem_forma_filha", "aninhadas", "com_beam_dentro", "cross_staff", "com_acorde", "tremolos"])
        w.writerows(rows2)
    with open(os.path.join(a.out, "regra3-falhas.csv"), "w", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["peca", "pagina", "caso", "pauta", "lado", "ordem", "x1", "x2", "donas"])
        w.writerows(bad3)
    print("peça; traços; sem dona; colunas diferentes (por falta de instante)")
    for r in rows3:
        print("%-72s %5d %4d %4d (%d) pausa:%d misto:%d" % tuple(r))
    print("TOTAL regra 3: traços %d, sem dona %d, colunas diferentes %d (por falta de instante: %d), donas %d; "
          "com dona pausa %d (só pausa %d, pausa e nota %d)" % (
        tot["dashes"], tot["sem_dona"], tot["colunas_diferentes"], tot["colunas_diferentes_com_sem_instante"], tot["donas_total"],
        tot["com_dona_pausa"], tot["so_pausa"], tot["pausa_e_nota"]))
    print("TOTAL regra 2: " + ", ".join("%s=%d" % kv for kv in sorted(tot.items()) if kv[0].startswith(("beam", "tremolo"))))
    return 1 if tot["sem_dona"] or tot["colunas_diferentes"] or tot["pausa_e_nota"] else 0


def _desc_groups(n):
    for c in n.get("children", []):
        if c.get("t") == "g":
            yield c
            yield from _desc_groups(c)


def _all_groups(n):
    yield n
    yield from _desc_groups(n)


if __name__ == "__main__":
    sys.exit(main())
