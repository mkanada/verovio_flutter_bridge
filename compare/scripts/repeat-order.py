#!/usr/bin/env python3
"""repeat-order.py -- sequência de compassos que um .vsb realmente toca (E01a).

    repeat-order.py <partitura | .vsb> [--expected <arquivo>] [-- <opções do verovio>]

Com uma partitura (MEI/MusicXML), gera o `.vsb` em `compare/out/e01/` (`-t vsb`
mais as opções extras depois de `--`) e analisa o pacote gerado. Com um `.vsb`,
analisa direto.

Lê a cena para saber, para cada id, o compasso ancestral mais próximo e a
ordem de documento dos compassos (por página, na ordem dos `children`). Lê o
timemap embutido para saber a ordem de execução:

- se uma entrada do timemap tem `measureOn`, ela é a fonte (E01b);
- senão, cada nota de `on` é resolvida (`sceneIdOf`/`passOf`, regra do
  sufixo `-rend<N>` de D-EXPMAP) até o compasso ancestral, e uma ocorrência
  nova começa sempre que o par (compasso, passagem) muda.

Imprime a sequência em blocos (`1-4 1-4 5-6`), o total de ocorrências e a
distribuição por passagem, e a lista de saltos (ocorrência cujo compasso não
é o seguinte do anterior na ordem de documento), com página de origem e de
destino. Com `--expected`, compara a sequência de blocos com o arquivo (uma
linha, mesmo formato) e sai com 1 na primeira divergência.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import zipfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VEROVIO_BIN = os.path.join(REPO_ROOT, "verovio", "tools", "verovio")
RESOURCE_PATH = os.path.join(REPO_ROOT, "verovio", "data")
OUT_DIR = os.path.join(REPO_ROOT, "compare", "out", "e01")

RENDN_RE = re.compile(r"^(.*)-rend([0-9]+)$")


def load_vsb(path):
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        scene = json.loads(z.read("scene.json"))
        timemap = json.loads(z.read("timemap.json")) if "timemap.json" in names else []
    return scene, timemap


def generate_vsb(score_path, extra_args):
    os.makedirs(OUT_DIR, exist_ok=True)
    base = os.path.splitext(os.path.basename(score_path))[0]
    # o `-o` do verovio trunca no ultimo "." do caminho: usa um prefixo
    # temporário sem pontos e move depois (mesma cautela de compare-page.sh).
    tmp_prefix = os.path.join(OUT_DIR, "_repeat-order-tmp")
    out_path = os.path.join(OUT_DIR, base + ".vsb")
    cmd = [VEROVIO_BIN, "--resource-path", RESOURCE_PATH, "-t", "vsb"] + extra_args + [score_path, "-o", tmp_prefix]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    sys.stderr.write(proc.stderr)
    if proc.returncode != 0 or not os.path.exists(tmp_prefix + ".vsb"):
        print(f"Falha ao gerar .vsb de {score_path} (código {proc.returncode}).", file=sys.stderr)
        sys.exit(2)
    os.replace(tmp_prefix + ".vsb", out_path)
    return out_path


class SceneIndex:
    """id -> compasso ancestral mais próximo (ele mesmo, se for um compasso),
    ordem de documento dos compassos e página de cada um."""

    def __init__(self, scene):
        self.id_to_measure = {}
        self.measure_order = []  # ids de compasso, em ordem de documento
        self.page_of_measure = {}
        for page in scene["pages"]:
            self._walk(page["root"], page["index"], current_measure=None)

    def _walk(self, node, page_index, current_measure):
        node_id = node.get("id")
        node_class = node.get("class")
        if node_class == "measure" and node_id:
            current_measure = node_id
            if node_id not in self.page_of_measure:
                self.measure_order.append(node_id)
                self.page_of_measure[node_id] = page_index
        if node_id and current_measure is not None:
            self.id_to_measure.setdefault(node_id, current_measure)
        elif node_id and node_class == "measure":
            self.id_to_measure.setdefault(node_id, node_id)
        for child in node.get("children", []):
            self._walk(child, page_index, current_measure)

    def scene_ids(self):
        return self.id_to_measure.keys()

    def resolve(self, id_):
        """(compasso, passagem) para um id do timemap, ou (None, None)."""
        if id_ in self.id_to_measure:
            return self.id_to_measure[id_], 1
        m = RENDN_RE.match(id_)
        if m and m.group(1) in self.id_to_measure:
            return self.id_to_measure[m.group(1)], int(m.group(2))
        return None, None

    def measure_number(self, measure_id):
        # 1-based, ordem de documento
        return self.measure_order.index(measure_id) + 1


class Occurrence:
    __slots__ = ("measure_id", "measure_number", "pass_", "page", "start_ms")

    def __init__(self, measure_id, measure_number, pass_, page, start_ms):
        self.measure_id = measure_id
        self.measure_number = measure_number
        self.pass_ = pass_
        self.page = page
        self.start_ms = start_ms


def build_occurrences(scene_index, timemap):
    occurrences = []
    warnings = []
    last_key = None
    for entry in timemap:
        measure_on = entry.get("measureOn")
        if measure_on is not None:
            measure_id, pass_ = scene_index.resolve(measure_on)
            if measure_id is None:
                warnings.append(f"measureOn {measure_on!r} não resolvido na cena")
                continue
            candidates = [(measure_id, pass_)]
        else:
            on_ids = entry.get("on") or []
            candidates = []
            for note_id in on_ids:
                measure_id, pass_ = scene_index.resolve(note_id)
                if measure_id is None:
                    warnings.append(f"id de timemap {note_id!r} não resolvido na cena")
                    continue
                candidates.append((measure_id, pass_))
            if not candidates:
                continue
            distinct = set(candidates)
            if len(distinct) > 1:
                warnings.append(
                    f"tstamp {entry.get('tstamp')}: ids de 'on' resolvem a compassos/passagens "
                    f"diferentes ({sorted(distinct)}), usando o mais frequente"
                )
                candidates = [max(distinct, key=candidates.count)]
        key = candidates[0]
        if key != last_key:
            measure_id, pass_ = key
            occurrences.append(
                Occurrence(
                    measure_id,
                    scene_index.measure_number(measure_id),
                    pass_,
                    scene_index.page_of_measure[measure_id],
                    entry.get("tstamp", 0),
                )
            )
            last_key = key
    return occurrences, warnings


def format_blocks(occurrences):
    blocks = []
    i = 0
    n = len(occurrences)
    while i < n:
        j = i
        while (
            j + 1 < n
            and occurrences[j + 1].measure_number == occurrences[j].measure_number + 1
            and occurrences[j + 1].pass_ == occurrences[j].pass_
        ):
            j += 1
        start = occurrences[i].measure_number
        end = occurrences[j].measure_number
        blocks.append(str(start) if start == end else f"{start}-{end}")
        i = j + 1
    return blocks


def find_jumps(occurrences):
    jumps = []
    for i in range(1, len(occurrences)):
        prev, cur = occurrences[i - 1], occurrences[i]
        if cur.measure_number != prev.measure_number + 1:
            jumps.append((prev, cur))
    return jumps


def pass_counts(occurrences):
    counts = {}
    for o in occurrences:
        counts[o.pass_] = counts.get(o.pass_, 0) + 1
    return counts


def main():
    # Separa manualmente as opções do verovio depois de "--": com
    # argparse.REMAINDER, um "--expected" depois do "--" seria engolido pelo
    # REMAINDER em vez de reconhecido como opção deste script.
    argv = sys.argv[1:]
    if "--" in argv:
        sep = argv.index("--")
        main_argv, extra_args = argv[:sep], argv[sep + 1 :]
    else:
        main_argv, extra_args = argv, []

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", help="partitura (MEI/MusicXML/.mxl) ou pacote .vsb")
    parser.add_argument("--expected", help="arquivo com a sequência esperada (uma linha, blocos separados por espaço)")
    args = parser.parse_args(main_argv)

    if args.input.endswith(".vsb"):
        vsb_path = args.input
    else:
        vsb_path = generate_vsb(args.input, extra_args)

    scene, timemap = load_vsb(vsb_path)
    scene_index = SceneIndex(scene)
    occurrences, warnings = build_occurrences(scene_index, timemap)
    blocks = format_blocks(occurrences)
    jumps = find_jumps(occurrences)
    counts = pass_counts(occurrences)

    print(f"arquivo: {vsb_path}")
    print(f"sequência: {' '.join(blocks)}")
    print(f"ocorrências: {len(occurrences)} ({', '.join(f'passagem {p}: {c}' for p, c in sorted(counts.items()))})")
    print(f"saltos: {len(jumps)}")
    for prev, cur in jumps:
        same_page = " (mesma página)" if prev.page == cur.page else ""
        print(
            f"  {prev.measure_number} → {cur.measure_number}  "
            f"página {prev.page} → {cur.page}{same_page}"
        )
    for w in warnings:
        print(f"aviso: {w}", file=sys.stderr)

    if args.expected:
        with open(args.expected) as f:
            expected = f.read().strip()
        got = " ".join(blocks)
        if got != expected:
            print(f"DIVERGE de {args.expected}:", file=sys.stderr)
            print(f"  esperado: {expected}", file=sys.stderr)
            print(f"  obtido:   {got}", file=sys.stderr)
            exp_blocks = expected.split()
            got_blocks = blocks
            for i, (e, g) in enumerate(zip(exp_blocks, got_blocks)):
                if e != g:
                    print(f"  primeira divergência no bloco {i}: esperado {e!r}, obtido {g!r}", file=sys.stderr)
                    break
            else:
                print(f"  um dos dois tem blocos a mais (esperado {len(exp_blocks)}, obtido {len(got_blocks)})", file=sys.stderr)
            sys.exit(1)
        print(f"OK: bate com {args.expected}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
