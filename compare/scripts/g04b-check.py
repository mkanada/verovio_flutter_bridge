#!/usr/bin/env python3
"""G04b (descartável): confere os critérios de aceite da geometria da pauta.

Uso: g04b-check.py <dir-base> <dir-novo>
  1. Cena/alternates idênticos ao baseline, exceto os campos aditivos
     (lines/ledger/ledgerCue/gs/staff); manifest/timemap/meta/midi idênticos.
  2. Todo nó staff tem `lines` e topY + k*2*unit bate com os n primeiros filhos `p`.
  3. Toda cabeça (u dentro de nó `notehead`) cai em loc inteiro na pauta de desenho.
  4. Os 8 glifos reservados estão em todo glyphs.json; só eles foram acrescentados.
  5. Tamanhos de scene.json/glyphs.json antes/depois.
"""
import glob, json, os, sys, zipfile

ADD = {"lines", "ledger", "ledgerCue", "gs", "staff"}
RESERVED = {"E0A4", "E260", "E261", "E262", "E511", "E512", "E515", "E516"}


def strip(n):
    if isinstance(n, dict):
        return {k: strip(v) for k, v in n.items() if k not in ADD}
    if isinstance(n, list):
        return [strip(x) for x in n]
    return n


def pages_of(files):
    out = [("p%d" % p["index"], p) for p in json.loads(files["scene.json"])["pages"]]
    if "alternates.json" in files:
        for si, seq in enumerate(json.loads(files["alternates.json"])["sequences"]):
            for pi, p in enumerate(seq["pages"]):
                out.append(("alt%d-p%d" % (si, pi), p))
    return out


def walk(n, anc=()):
    yield n, anc
    for c in n.get("children", []):
        if c.get("t") == "g":
            yield from walk(c, anc + (n,))


def main(base, new):
    tot = dict(stavesBad=0, staves=0, heads=0, headsBad=0, diffs=0)
    print("peca;scene_antes;scene_depois;glyphs_antes;glyphs_depois")
    for fn in sorted(glob.glob(os.path.join(new, "*.vsb"))):
        name = os.path.basename(fn)
        zn = zipfile.ZipFile(fn)
        if not os.path.exists(os.path.join(base, name)):
            continue  # peça nova (corpus/fantasma), sem baseline
        zb = zipfile.ZipFile(os.path.join(base, name))
        fn_ = {n: zn.read(n) for n in zn.namelist()}
        fb = {n: zb.read(n) for n in zb.namelist()}
        if set(fn_) != set(fb):
            print("ARQUIVOS DIFEREM", name, set(fn_) ^ set(fb)); tot["diffs"] += 1
        for n in fb:
            if n in ("scene.json", "alternates.json", "glyphs.json"):
                continue
            if fb[n] != fn_.get(n):
                print("DIFERE", name, n); tot["diffs"] += 1
        for n in ("scene.json", "alternates.json"):
            if n in fb and strip(json.loads(fb[n])) != strip(json.loads(fn_[n])):
                print("DIFERE (após strip)", name, n); tot["diffs"] += 1
        gb, gn = json.loads(fb["glyphs.json"]), json.loads(fn_["glyphs.json"])
        for k in gb:
            if gb[k] != gn.get(k):
                print("GLIFO DIFERE", name, k); tot["diffs"] += 1
        added = set(gn) - set(gb)
        if any(k.split(":")[1] not in RESERVED for k in added):
            print("GLIFO NÃO RESERVADO ACRESCENTADO", name, added); tot["diffs"] += 1
        have = {k.split(":")[1] for k in gn}
        if not RESERVED <= have:
            print("FALTA RESERVADO", name, RESERVED - have); tot["diffs"] += 1
        # critérios 2 e 3
        for pname, page in pages_of(fn_):
            ids = {}
            for n, _ in walk(page["root"]):
                if "id" in n:
                    ids[n["id"]] = n
            for n, anc in walk(page["root"]):
                cls = n.get("class", "").split()
                if "staff" in cls and "lines" in n:
                    pass
                if cls[:1] == ["staff"]:
                    tot["staves"] += 1
                    if "lines" not in n:
                        tot["stavesBad"] += 1; print("STAFF SEM lines", name, pname, n.get("id")); continue
                    top, unit, k = n["lines"]
                    ps = [c for c in n["children"] if c.get("t") == "p"][:k]
                    ys = [c["paths"][0]["v"][1] for c in ps]
                    want = [top + 2 * i * unit for i in range(k)]
                    if len(ys) != k or any(abs(a - b) > 0.5 for a, b in zip(ys, want)):
                        tot["stavesBad"] += 1; print("LINHAS NÃO BATEM", name, pname, n.get("id"), ys, want)
                if "notehead" in cls:
                    staffn = None
                    for a in reversed(anc):
                        if a.get("class", "").split()[:1] == ["staff"]:
                            staffn = a; break
                    for a in reversed(anc + (n,)):
                        if "staff" in a and a["staff"] in ids:
                            staffn = ids[a["staff"]]; break
                    for c in n["children"]:
                        if c.get("t") != "u": continue
                        tot["heads"] += 1
                        if not staffn or "lines" not in staffn:
                            tot["headsBad"] += 1; print("CABEÇA SEM PAUTA", name, pname, n.get("id")); continue
                        top, unit, k = staffn["lines"]
                        loc = (2 * (k - 1) - (c["y"] - top) / unit)
                        if abs(loc - round(loc)) * unit > 0.51:
                            tot["headsBad"] += 1; print("LOC NÃO INTEIRO", name, pname, n.get("id"), loc)
        print("%s;%d;%d;%d;%d" % (name, len(fb["scene.json"]), len(fn_["scene.json"]), len(fb["glyphs.json"]), len(fn_["glyphs.json"])))
    print(tot)
    return 1 if (tot["diffs"] or tot["stavesBad"] or tot["headsBad"]) else 0


sys.exit(main(sys.argv[1], sys.argv[2]))
