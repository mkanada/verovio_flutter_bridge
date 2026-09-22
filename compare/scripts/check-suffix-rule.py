#!/usr/bin/env python3
"""check-suffix-rule.py -- valida a regra do sufixo de D-EXPMAP (E02a).

Para cada peça do corpus e cada partitura mínima de E01a, gera `-t
expansionmap` e o `.vsb` (timemap com `measureOn`), com o mesmo
`--xml-id-seed` nos dois, e confere que a regra do sufixo
(`^(.*)-rend([0-9]+)$`, com a base existindo na cena) concorda, para todo id
de `on`/`off`/`measureOn` do timemap, com o que `-t expansionmap` diz ser a
base notada daquele id. Sai com 1 e mostra a primeira divergência se achar
alguma; senão imprime o total de ids checados por peça e no total.
"""
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
VEROVIO_BIN = REPO_ROOT / "verovio" / "tools" / "verovio"
RESOURCE_PATH = REPO_ROOT / "verovio" / "data"
OUT_DIR = REPO_ROOT / "compare" / "out" / "e02a"

RENDN_RE = re.compile(r"^(.*)-rend([0-9]+)$")

PIECES = [
    (REPO_ROOT / "corpus/musicxml/Erik_Satie_-_Gymnopedie_No.1.mxl", True, []),
    (REPO_ROOT / "corpus/musicxml/Maple_Leaf_Rag_Scott_Joplin.mxl", True, []),
    (REPO_ROOT / "corpus/musicxml/Chopin_-_Nocturne_Op._9_No._1.mxl", True, []),
    (REPO_ROOT / "corpus/musicxml/Clair_de_Lune__Debussy.mxl", True, []),
    (
        REPO_ROOT
        / "corpus/musicxml/Prelude_I_in_C_major_BWV_846_-_Well_Tempered_Clavier_First_Book.mxl",
        True,
        [],
    ),
    (REPO_ROOT / "corpus/mei/Chopin_Etude_Op10_No9.mei", True, []),
    (REPO_ROOT / "corpus/mei/Chopin_Mazurka_Op6_No1.mei", True, []),
    (REPO_ROOT / "corpus/mei/Grieg_Butterfly_Op43_No1.mei", True, []),
    (REPO_ROOT / "corpus/mei/Grieg_Little_bird_Op43_No4.mei", True, []),
    (REPO_ROOT / "corpus/mei/Scarlatti_Sonata_in_C-major.mei", True, []),
]

REPETICOES_DIR = REPO_ROOT / "corpus" / "repeticoes"
BREAKS_ENCODED = {"r06-salto-de-pagina.musicxml", "r07-salto-de-pagina.mei"}
for f in sorted(REPETICOES_DIR.glob("*.musicxml")) + sorted(
    REPETICOES_DIR.glob("*.mei")
):
    extra = ["--breaks", "encoded"] if f.name in BREAKS_ENCODED else []
    PIECES.append((f, True, extra))


def sceneIds(vsb_path):
    with zipfile.ZipFile(vsb_path) as z:
        scene = json.loads(z.read("scene.json"))
    ids = set()

    def walk(node):
        node_id = node.get("id")
        if node_id:
            ids.add(node_id)
        for child in node.get("children", []):
            walk(child)

    for page in scene["pages"]:
        walk(page["root"])
    return ids


def suffix_rule_base(timemap_id, scene_ids):
    if timemap_id in scene_ids:
        return timemap_id
    m = RENDN_RE.match(timemap_id)
    if m and m.group(1) in scene_ids:
        return m.group(1)
    return None


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    total = 0
    divergences = []
    for path, needs_seed, extra in PIECES:
        name = path.stem
        seed = ["--xml-id-seed", "42"] if needs_seed else []
        vsb_out = OUT_DIR / f"{name}.vsb"
        expmap_out = OUT_DIR / f"{name}.expansionmap.json"
        subprocess.run(
            [
                str(VEROVIO_BIN),
                "--resource-path",
                str(RESOURCE_PATH),
                *seed,
                *extra,
                "-t",
                "vsb",
                str(path),
                "-o",
                str(vsb_out),
            ],
            capture_output=True,
        )
        subprocess.run(
            [
                str(VEROVIO_BIN),
                "--resource-path",
                str(RESOURCE_PATH),
                *seed,
                *extra,
                "-t",
                "expansionmap",
                str(path),
                "-o",
                str(expmap_out),
            ],
            capture_output=True,
        )
        if not vsb_out.exists():
            print(f"{name}: falha ao gerar .vsb", file=sys.stderr)
            return 2
        scene_ids = sceneIds(vsb_out)
        expmap = {}
        if expmap_out.exists():
            with open(expmap_out) as f:
                text = f.read().strip()
            if text and text != "{}":
                expmap = json.loads(text)

        with zipfile.ZipFile(vsb_out) as z:
            timemap = (
                json.loads(z.read("timemap.json")) if "timemap.json" in z.namelist() else []
            )

        piece_ids = set()
        for entry in timemap:
            piece_ids.update(entry.get("on", []))
            piece_ids.update(entry.get("off", []))
            if entry.get("measureOn"):
                piece_ids.add(entry["measureOn"])

        piece_divergences = []
        for tid in piece_ids:
            mine = suffix_rule_base(tid, scene_ids)
            if tid in expmap:
                truth = expmap[tid][0]
            else:
                # não está no mapa de expansão: não é um clone, é o próprio
                # id notado (existe na cena) ou não pertence a nada.
                truth = tid if tid in scene_ids else None
            if mine != truth:
                piece_divergences.append((tid, mine, truth))
        total += len(piece_ids)
        if piece_divergences:
            divergences.append((name, piece_divergences))
            print(f"{name}: {len(piece_divergences)} divergências de {len(piece_ids)} ids")
        else:
            print(f"{name}: OK ({len(piece_ids)} ids)")

    print(f"\nTotal: {total} ids checados, {sum(len(d) for _, d in divergences)} divergências")
    if divergences:
        name, divs = divergences[0]
        print(f"\nPrimeira divergência ({name}): {divs[0]}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
