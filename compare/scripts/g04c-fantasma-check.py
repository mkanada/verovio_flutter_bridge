#!/usr/bin/env python3
"""G04c: confere corpus/fantasma/*.mei contra corpus/fantasma/esperado.json (valores escritos
à mão). Uso: g04c-fantasma-check.py [verovio] — sai com código != 0 se algo divergir."""
import glob, json, os, subprocess, sys, tempfile, zipfile

root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
verovio = sys.argv[1] if len(sys.argv) > 1 else os.path.join(root, "verovio/tools/verovio")
esperado = {k: v for k, v in json.load(open(os.path.join(root, "corpus/fantasma/esperado.json"))).items() if not k.startswith("_")}
found, bad = {}, 0
with tempfile.TemporaryDirectory() as tmp:
    for mei in sorted(glob.glob(os.path.join(root, "corpus/fantasma/*.mei"))):
        out = os.path.join(tmp, os.path.basename(mei) + ".vsb")
        subprocess.run([verovio, "-t", "vsb", "--xml-id-seed", "1", "--resource-path", os.path.join(root, "verovio/data"), "-o", out, mei],
                       check=True, capture_output=True)
        found.update(json.loads(zipfile.ZipFile(out).read("pitchpos.json"))["events"])
for i, want in esperado.items():
    got = found.get(i)
    if got is None:
        print("SEM ENTRADA", i); bad += 1; continue
    defaults = {"t": "n", "sh": 0, "key": {}, "acc": {}}
    for k, v in want.items():
        if got.get(k, defaults.get(k)) != v:
            print("DIVERGE", i, k, "esperado", v, "obtido", got.get(k, defaults.get(k))); bad += 1
print("%d ids conferidos, %d divergências" % (len(esperado), bad))
sys.exit(1 if bad else 0)
