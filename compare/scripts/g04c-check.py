#!/usr/bin/env python3
"""G04c (descartável): critérios de aceite de pitchpos.json e do timemap com pausas.

Uso: g04c-check.py <dir-base(G04b)> <dir-novo(G04c)>
  1. .mid byte-idêntico; `-t timemap` standalone byte-idêntico.
  2. timemap embutido: mesmas entradas e campos antigos; só restsOn/restsOff novos.
  3. Nota/pausa desenhada (class note/rest/mRest/multiRest, não hidden, páginas normais) <-> entrada.
  4. loc == CalcLoc(pn, o, co); midi.p == altura(pn, o, alt) + sh (fora ornamentos).
  5. Cena/glifos idênticos a G04b; tamanho de pitchpos.json e tempo.
"""
import glob, json, os, re, sys, zipfile

SEM = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}
REND = re.compile(r"^(.*)-rend([0-9]+)$")


def walk(n):
    yield n
    for c in n.get("children", []):
        if c.get("t") == "g":
            yield from walk(c)


def main(base, new):
    bad = 0
    tot = dict(notes=0, rests=0, locBad=0, pBad=0, pChecked=0, missing=0, extra=0, restsOn=0)
    print("peca;pitchpos_bytes;eventos;vsb_antes;vsb_depois;t_antes;t_depois")
    times = {}
    for fn in ("base", "new"):
        d = base if fn == "base" else new
        try:
            for line in open(os.path.join(d, "tempos.csv")):
                n, t = line.strip().split(";")
                times[(fn, n)] = float(t)
        except FileNotFoundError:
            pass
    for fn in sorted(glob.glob(os.path.join(new, "*.vsb"))):
        name = os.path.basename(fn)[:-4]
        zn = zipfile.ZipFile(fn)
        if not os.path.exists(os.path.join(base, name + ".vsb")):
            continue  # peça nova (corpus/fantasma), sem baseline
        zb = zipfile.ZipFile(os.path.join(base, name + ".vsb"))
        # 1
        for ext in (".mid", ".timemap.json"):
            if open(os.path.join(base, name + ext), "rb").read() != open(os.path.join(new, name + ext), "rb").read():
                print("DIFERE", name, ext); bad += 1
        # 5
        for n in ("scene.json", "glyphs.json", "alternates.json", "midi.json", "meta.json"):
            if (n in zb.namelist()) != (n in zn.namelist()) or (n in zb.namelist() and zb.read(n) != zn.read(n)):
                print("DIFERE", name, n); bad += 1
        # 2
        if "timemap.json" in zb.namelist():
            tb, tn = json.loads(zb.read("timemap.json")), json.loads(zn.read("timemap.json"))
            if len(tb) != len(tn):
                print("TIMEMAP: nº de entradas", name, len(tb), len(tn)); bad += 1
            else:
                for a, b in zip(tb, tn):
                    tot["restsOn"] += len(b.get("restsOn", []))
                    b2 = {k: v for k, v in b.items() if k not in ("restsOn", "restsOff")}
                    if a != b2:
                        print("TIMEMAP: campo antigo mudou", name, a, b); bad += 1; break
        if "pitchpos.json" not in zn.namelist():
            print("SEM pitchpos", name); bad += 1; continue
        pp = json.loads(zn.read("pitchpos.json"))["events"]
        scene = json.loads(zn.read("scene.json"))
        # 3
        drawn = {}
        hiddenIds = set()
        for page in scene["pages"]:
            for n in walk(page["root"]):
                cls = n.get("class", "").split()
                if cls and cls[0] in ("note", "rest", "mRest", "multiRest") and "id" in n:
                    if n.get("hidden"):
                        hiddenIds.add(n["id"])
                    else:
                        drawn[n["id"]] = cls[0]
        for i, c in drawn.items():
            if i not in pp:
                tot["missing"] += 1
                if tot["missing"] <= 10: print("SEM ENTRADA", name, i, c)
            else:
                want = "n" if c == "note" else "r"
                if pp[i]["t"] != want:
                    print("TIPO", name, i); bad += 1
        for i in pp:
            if i not in drawn and i not in hiddenIds:
                tot["extra"] += 1
                if tot["extra"] <= 10: print("ENTRADA SEM CENA", name, i, pp[i])
        # 4
        for i, e in pp.items():
            if e["t"] == "n":
                tot["notes"] += 1
                calc = (e["o"] - 4) * 7 + "cdefgab".index(e["pn"]) + e["co"]
                if calc != e["loc"]:
                    tot["locBad"] += 1
                    if tot["locBad"] <= 10: print("LOC", name, i, e, calc)
            else:
                tot["rests"] += 1
        if "midi.json" in zn.namelist():
            for m in json.loads(zn.read("midi.json"))["notes"]:
                if m.get("orn"): continue
                i = m["id"]
                if i not in pp:
                    mo = REND.match(i)
                    i = mo.group(1) if mo else i
                e = pp.get(i)
                if not e or e["t"] != "n":
                    tot["pBad"] += 1
                    if tot["pBad"] <= 10: print("MIDI SEM PITCHPOS", name, m["id"])
                    continue
                pitch = 12 * (e["o"] + 1) + SEM[e["pn"]] + e["alt"] + e.get("sh", 0)
                tot["pChecked"] += 1
                if pitch != m["p"]:
                    tot["pBad"] += 1
                    if tot["pBad"] <= 10: print("P", name, m["id"], m["p"], pitch, e)
        size = len(zn.read("pitchpos.json"))
        print("%s;%d;%d;%d;%d;%s;%s" % (name, size, len(pp), os.path.getsize(os.path.join(base, name + ".vsb")),
              os.path.getsize(fn), times.get(("base", name), ""), times.get(("new", name), "")))
    print(tot, "outros erros:", bad)
    return 1 if (bad or tot["locBad"] or tot["pBad"] or tot["missing"] or tot["extra"]) else 0


sys.exit(main(sys.argv[1], sys.argv[2]))
