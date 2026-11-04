#!/usr/bin/env python3
"""G08b (descartável): critérios de aceite de glifos de pausa reservados e dur/dots no pitchpos.json.

Uso: g08b-check.py <dir-antes> <dir-depois>
  1. .mid e timemap standalone byte-idênticos; scene/alternates/timemap/midi/meta idênticos.
  2. 16 glifos reservados em todo glyphs.json; únicos acrescentados vs. baseline = os 8 novos.
  3. toda nota e pausa (exceto mRest/multiRest) de figura semibreve..semifusa tem dur; conta as sem.
  4. glifo da pausa desenhada na cena == glifo de Rest::GetRestGlyph(dur gravado): 0 divergências.
  5. pitchpos.json: só campos dur/dots novos (resto idêntico ao baseline); tamanhos antes/depois.
"""
import glob, json, os, sys, zipfile

NEW = {"E4E3", "E4E4", "E4E5", "E4E6", "E4E7", "E4E8", "E4E9", "E1E7"}
OLD = {"E0A4", "E260", "E261", "E262", "E511", "E512", "E515", "E516"}
REST_GLYPH = {1: "E4E3", 2: "E4E4", 4: "E4E5", 8: "E4E6", 16: "E4E7", 32: "E4E8", 64: "E4E9",
              128: "E4EA", 256: "E4EB", 512: "E4EC", 1024: "E4ED"}


def walk(n):
    yield n
    for c in n.get("children", []):
        if c.get("t") == "g":
            yield from walk(c)


def main(base, new):
    bad = 0
    tot = dict(notes=0, rests=0, semDur=0, restChecked=0, restDiv=0, comDots=0)
    print("peca;glyphs_antes;glyphs_depois;pitchpos_antes;pitchpos_depois;eventos;sem_dur")
    for fn in sorted(glob.glob(os.path.join(new, "*.vsb"))):
        name = os.path.basename(fn)[:-4]
        if not os.path.exists(os.path.join(base, name + ".vsb")):
            continue
        zn, zb = zipfile.ZipFile(fn), zipfile.ZipFile(os.path.join(base, name + ".vsb"))
        for ext in (".mid", ".timemap.json"):
            if open(os.path.join(base, name + ext), "rb").read() != open(os.path.join(new, name + ext), "rb").read():
                print("DIFERE", name, ext); bad += 1
        for n in ("scene.json", "alternates.json", "timemap.json", "midi.json", "meta.json"):
            if (n in zb.namelist()) != (n in zn.namelist()) or (n in zb.namelist() and zb.read(n) != zn.read(n)):
                print("DIFERE", name, n); bad += 1
        # 2
        gb, gn = json.loads(zb.read("glyphs.json")), json.loads(zn.read("glyphs.json"))
        cb = {k.split(":")[1] for k in gb}
        cn = {k.split(":")[1] for k in gn}
        if not (cb <= cn):
            print("GLIFO SUMIU", name, cb - cn); bad += 1
        if (cn - cb) - NEW:
            print("GLIFO ACRESCIDO FORA DO ESPERADO", name, (cn - cb) - NEW); bad += 1
        if not ((OLD | NEW) <= cn):
            print("RESERVADO FALTA", name, (OLD | NEW) - cn); bad += 1
        # 5 / 3
        pb = json.loads(zb.read("pitchpos.json"))["events"]
        pn = json.loads(zn.read("pitchpos.json"))["events"]
        if pb.keys() != pn.keys():
            print("PITCHPOS ids mudaram", name); bad += 1
        semDur = 0
        for i, e in pn.items():
            e0 = {k: v for k, v in e.items() if k not in ("dur", "dots")}
            if pb.get(i) != e0:
                print("PITCHPOS campo antigo mudou", name, i); bad += 1; break
        scene = json.loads(zn.read("scene.json"))
        cls = {}
        rests = []
        for page in scene["pages"]:
            for n in walk(page["root"]):
                c = n.get("class", "").split()
                if c and "id" in n:
                    cls[n["id"]] = c[0]
                    if c[0] == "rest" and not n.get("hidden"):
                        rests.append(n)
        for i, e in pn.items():
            tot["notes" if e["t"] == "n" else "rests"] += 1
            if "dots" in e:
                tot["comDots"] += 1
                if "dur" not in e:
                    print("DOTS SEM DUR", name, i); bad += 1
            if "dur" in e:
                if e["dur"] not in REST_GLYPH:
                    print("DUR FORA", name, i, e); bad += 1
                continue
            if cls.get(i) in ("mRest", "multiRest"):
                continue
            semDur += 1
            if semDur <= 3:
                print("  sem dur:", name, i, cls.get(i), e)
        tot["semDur"] += semDur
        # 4
        for n in rests:
            e = pn.get(n["id"])
            if e is None or "dur" not in e:
                continue
            u = [c for c in n.get("children", []) if c.get("t") == "u"]
            if not u:
                continue
            tot["restChecked"] += 1
            code = u[0]["g"].split(":")[1]
            if code != REST_GLYPH[e["dur"]]:
                tot["restDiv"] += 1
                if tot["restDiv"] <= 10: print("REST DIVERGE", name, n["id"], code, e)
        print("%s;%d;%d;%d;%d;%d;%d" % (name, len(zb.read("glyphs.json")), len(zn.read("glyphs.json")),
              len(zb.read("pitchpos.json")), len(zn.read("pitchpos.json")), len(pn), semDur))
    print(tot, "outros erros:", bad)
    return 1 if (bad or tot["restDiv"]) else 0


sys.exit(main(sys.argv[1], sys.argv[2]))
