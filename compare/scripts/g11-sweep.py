#!/usr/bin/env python3
"""G11, item 4 do plano: o que vaza quando um compasso inteiro é escondido, e a prova da regra de dono.

Para cada página (normal ou alternativa) dos `.vsb` de `compare/out/g11/oraculo/work/*.vsb` (os
originais, sem troca por mRest; rode `hide_oracle.py --measures` antes):

 1. esconde TODOS os compassos da página (`hide_ref.hidden_measures`) e conta o que sobra desenhado,
    por classe do nó mais próximo: o que deve sobrar (pauta, clave, barra de compasso, letra,
    dinâmica…) e o que NÃO deve (nota, haste, barra, tercina, ligadura…). O segundo grupo tem de dar 0;
 2. esconde UM compasso por vez e conta, por classe de controle ancorado (ligadura, ligadura de
    prolongamento, frase, arpejo, beamSpan), quantos somem e quantos ficam (cruzam para um compasso
    visível), pelo número de compassos que o controle toca;
 3. classifica as pautas de cada compasso: só notas, notas e pausas, só pausas, só pausa de compasso.

Uso: g11-sweep.py [--work compare/out/g11/oraculo/work] [--out compare/out/g11/sweep]
"""
import argparse, collections, glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import hide_ref as hr

# o que pode sobrar à vista num compasso escondido (não vaza altura nem ritmo)
FICA = {"grpSym", "voltaBracket", "staff", "clef", "keySig", "keyAccid", "meterSig", "barLine", "mNum", "tempo", "dir", "dynam", "hairpin", "harm",
        "pedal", "fermata", "trill", "octave", "fing", "verse", "syl", "rend", "text", "ledgerLines", "space", "mSpace",
        "mRest", "multiRest", "rest", "layer", "measure", "system", "page", "mdiv", "score", "section", "ending"}
# o que NÃO pode sobrar
VAZA = {"note", "notehead", "stem", "flag", "accid", "dots", "artic", "chord", "beam", "tuplet", "tupletNum",
        "tupletBracket", "tie", "slur", "phrase", "arpeg", "beamSpan"}


def survivors(doc, root, res, count):
    """Conta as formas que continuam pintadas, por classe do nó nomeado mais próximo."""
    notes, chords = set(res["hidden"]["notes"]), set(res["hidden"]["chords"])
    beams = {b["id"] for b in res["hidden"]["beams"]}
    rests, tuplets, controls = set(res["hidden"]["rests"]), set(res["hidden"]["tuplets"]), set(res["hidden"]["controls"])
    ledgers = {tuple(l[:3]) + (l[3], l[4]) for l in res["hidden"]["ledgers"]}

    def verses(n):
        for c in n.get("children", []):
            if c.get("t") == "g":
                if "verse" in hr.classes(c):
                    rec(c, None, "verse")
                else:
                    verses(c)

    def rec(n, staff, cls):
        c0 = hr.classes(n)[:1]
        if cls not in ("rest", "mRest"):          # as formas de dentro de uma pausa contam como pausa
            cls = c0[0] if c0 else cls
        if cls == "staff":
            staff = n
        nid = n.get("id")
        if cls == "note" and nid in notes or cls == "chord" and nid in chords:
            verses(n); return
        if cls == "rest" and nid in rests or (cls in hr.CONTROL_CLASSES and "bbox" in n and hr.control_key(n) in controls):
            return
        if cls == "tuplet" and nid in tuplets:
            verses(n); return
        direct = cls == "beam" and nid in beams
        for ch in n.get("children", []):
            t = ch.get("t")
            if t == "g":
                rec(ch, staff, cls)
            elif direct:
                continue
            elif cls == "ledgerLines" and t == "p":
                side, k, x1, x2, y = hr.dash_of(staff, ch, False)
                if (staff["id"], side, k, round(x1, 1), round(x2, 1)) in ledgers:
                    continue
                count[cls] += 1
            else:
                count[cls] += 1
    rec(root, None, "?")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", default=os.path.join(ROOT, "compare/out/g11/oraculo/work"))
    ap.add_argument("--out", default=os.path.join(ROOT, "compare/out/g11/sweep"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    left = collections.Counter()               # sobras por classe
    ctl = collections.defaultdict(collections.Counter)   # classe -> {(tocados, 'some'|'fica'): n}
    staffk = collections.Counter()
    present = collections.Counter()            # classes presentes dentro de compassos (denominador)
    npages = nmeas = 0
    for f in sorted(glob.glob(a.work + "/*.vsb")):
        if ".all." in f or ".k3" in f:
            continue
        doc = hr.Doc(f)
        for ref, root in doc.all_page_roots():
            ix = hr.PageIx(root)
            if not ix.measures:
                continue
            npages += 1
            nmeas += len(ix.measures)
            res = dict(hidden=hr.hidden_measures(doc, root, set(ix.measures), ix))
            survivors(doc, root, res, left)
            for n, system in ix.controls:
                present[hr.classes(n)[0]] += 1
            for tp in ix.tuplets:
                present["tuplet"] += 1
            for mid in ix.measures:
                nb, rb = hr.measure_columns(ix, mid)
                for sid in hr.measure_staffs(ix, mid):
                    n_n, n_r = len(nb.get(sid, [])), len(rb.get(sid, []))
                    real_rests = [r for r in rb.get(sid, []) if "mRest" not in hr.classes(ix.rests[r][0])]
                    if n_n and real_rests:
                        staffk["notas e pausas (pausas somem)"] += 1
                    elif n_n:
                        staffk["só notas"] += 1
                    elif real_rests:
                        staffk["só pausas (fica como está)"] += 1
                    elif n_r:
                        staffk["só pausa de compasso (fica)"] += 1
                    else:
                        staffk["vazia"] += 1
                # um compasso por vez: o que acontece com os controles ancorados
                one = hr.hidden_measures(doc, root, {mid}, ix)
                gone = set(one["controls"])
                ext = {m: hr.measure_extent(ix.measures[m][0]) for m in ix.measures}
                for n, system in ix.controls:
                    if "bbox" not in n or not n.get("children"):
                        continue
                    x0, _, x1, _ = n["bbox"]
                    touched = [m for m, (_, sy) in ix.measures.items()
                               if sy is system and ext[m] and min(x1, ext[m][1]) - max(x0, ext[m][0]) > hr.HEAD_SLACK]
                    if mid in touched:
                        ctl[hr.classes(n)[0]][(min(len(touched), 3), "some" if hr.control_key(n) in gone else "fica")] += 1
    print("páginas %d, compassos %d" % (npages, nmeas))
    print("\nPautas por compasso:", dict(staffk))
    print("\n1. O que sobra desenhado depois de esconder TODOS os compassos da página:")
    bad = 0
    for k, v in sorted(left.items(), key=lambda kv: -kv[1]):
        flag = "VAZA" if k in VAZA else ("fica" if k in FICA else "?")
        if flag != "fica":
            bad += v
        print("   %-14s %7d formas  %s" % (k, v, flag))
    print("   vazamentos (classes que não deveriam sobrar): %d" % bad)
    print("\n2. Controles ancorados, um compasso por vez (classe: tocados -> some/fica):")
    for k in sorted(ctl):
        print("   %-9s total %5d  " % (k, present[k]), dict(sorted(ctl[k].items())))
    json.dump(dict(left=left, staffs=staffk, present=present), open(os.path.join(a.out, "sweep.json"), "w"), indent=1)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
