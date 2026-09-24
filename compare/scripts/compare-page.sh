#!/usr/bin/env bash
# Compara uma página de uma partitura no fluxo `.vsb`, de ponta a ponta (R05b):
#
#   compare-page.sh <arquivo> <página> [tolerância] [--alternate <start-id>]
#     → compare/out/<peça>-p<N>-svg.png      (referência: verovio -t svg + svg_render)
#     → compare/out/<peça>-p<N>-scene.png    (cena: verovio -t vsb + compare scene-to-png)
#     → compare/out/<peça>-p<N>-diff.png     (imagem de diferença)
#     → estatística no stdout + linha final estável para R06a agregar em CSV
#
# <arquivo>: uma partitura (MEI/MusicXML/.mxl) OU um `.vsb` gerado com
# `--vsb-debug` (docs/formato/especificacao-v1.md §2.6). No segundo caso a
# comparação inteira sai só do `.vsb` — nem a partitura original nem as flags
# do Verovio usadas para gerá-lo são necessárias: o script extrai
# `debug-source.txt`/`debug-options.json` de dentro do pacote e os usa no
# lugar do arquivo de entrada e de `--header none --footer none
# --no-instrument-labels`, via `--options-file` (Toolkit::SetOptions). Um
# `.vsb` sem esses dois arquivos (gerado sem `--vsb-debug`) é rejeitado com
# uma mensagem clara.
#
# --alternate <start-id> (P02d, §2.5): compara a página <página> da sequência
# alternativa cujo compasso de chegada é esse `xml:id`, não a página normal.
# A referência SVG usa `--select-from <start-id>` (o mesmo mecanismo que
# Toolkit::RenderAlternatesToBridge usa no exportador, P02c/P02d) em vez de só
# `-p N`; os arquivos saem como <peça>-alt<K>-p<N>-*, K = índice da sequência
# em `alternates.json` (só para nomear a saída — a seleção em si é por id).
#
# Páginas: o `-p` do Verovio é 1-based e o `page.index` no `.vsb` é 0-based.
# O `.vsb` é SEMPRE gerado com todas as páginas (`-t vsb` ignora `-p`; achado
# de R02d em tools/main.cpp) e a página é selecionada no `scene-to-png`
# (`--page` 1-based, como o `-p` do Verovio). O SVG é gerado só da página
# pedida (`-t svg -p N`).
#
# Backend gráfico: Skia (decisão de 2026-09-20, revendo R05a). O Impeller no
# Linux não aplica antialiasing, o que contamina a comparação; por isso o
# runner (compare/linux/runner/my_application.cc) chama
# fl_dart_project_set_enable_impeller(project, FALSE). O backend é decidido em
# tempo de compilação. `COMPARE_BACKEND` diz qual backend este script espera
# (`skia`, padrão, ou `impeller`) e o script ABORTA se o binário `compare`
# estiver rodando outro — para ninguém medir com o backend errado por
# acidente. Para medir com Impeller: remova a linha FALSE do runner,
# `cd compare && flutter build linux --release`, e rode com
# `COMPARE_BACKEND=impeller`.
set -euo pipefail

ALTERNATE=""
POSITIONAL=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --alternate)
            ALTERNATE="$2"
            shift 2
            ;;
        --alternate=*)
            ALTERNATE="${1#--alternate=}"
            shift
            ;;
        *)
            POSITIONAL+=("$1")
            shift
            ;;
    esac
done
set -- "${POSITIONAL[@]}"

if [[ $# -lt 2 || $# -gt 3 ]]; then
    echo "Uso: $0 <arquivo> <página> [tolerância] [--alternate <start-id>]" >&2
    exit 1
fi

INPUT_FILE=$1
PAGE=$2
TOLERANCE=${3:-128}
COMPARE_BACKEND="${COMPARE_BACKEND:-skia}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

VEROVIO_BIN="$REPO_ROOT/verovio/tools/verovio"
COMPARE_BIN="$REPO_ROOT/compare/build/linux/x64/release/bundle/compare"
SVG_RENDER_BIN="$REPO_ROOT/compare/svg_render/target/release/svg_render"
RESOURCE_PATH="$REPO_ROOT/verovio/data"
OUT_DIR="$REPO_ROOT/compare/out"

if [[ ! -x "$VEROVIO_BIN" ]]; then
    echo "Binário do Verovio não encontrado em $VEROVIO_BIN." >&2
    echo "Compile com: cd $REPO_ROOT/verovio/tools && cmake ../cmake && make -j4" >&2
    exit 1
fi

if [[ ! -x "$COMPARE_BIN" ]]; then
    echo "Binário do compare não encontrado em $COMPARE_BIN." >&2
    echo "Compile com: cd $REPO_ROOT/compare && flutter build linux --release" >&2
    exit 1
fi

if [[ ! -x "$SVG_RENDER_BIN" ]]; then
    echo "Binário do svg_render não encontrado em $SVG_RENDER_BIN." >&2
    echo "Compile com: cd $REPO_ROOT/compare/svg_render && cargo build --release" >&2
    exit 1
fi

# O compare é um app Flutter/Linux: mesmo em modo batch precisa de um display
# para inicializar o motor. Sem DISPLAY, roda sob xvfb-run.
if [[ -z "${DISPLAY:-}" ]] && command -v xvfb-run >/dev/null 2>&1; then
    COMPARE_RUN=(xvfb-run -a "$COMPARE_BIN")
else
    COMPARE_RUN=("$COMPARE_BIN")
fi

if [[ ! -f "$INPUT_FILE" ]]; then
    echo "Arquivo de entrada não encontrado: $INPUT_FILE" >&2
    exit 1
fi

# Guarda de backend (R05a): o log do embedder diz qual backend está ativo.
# `diff --help` inicializa o motor e imprime a linha no stderr.
BACKEND_LOG="$("${COMPARE_RUN[@]}" diff --help 2>&1 >/dev/null || true)"
if [[ "$COMPARE_BACKEND" == "skia" ]]; then
    if grep -q "Using the Impeller rendering backend" <<<"$BACKEND_LOG"; then
        echo "Backend inesperado: COMPARE_BACKEND=skia, mas o binário está" >&2
        echo "usando Impeller. Confirme que o runner tem" >&2
        echo "  fl_dart_project_set_enable_impeller(project, FALSE);" >&2
        echo "em compare/linux/runner/my_application.cc, recompile e rode de novo:" >&2
        echo "  cd $REPO_ROOT/compare && flutter build linux --release" >&2
        exit 1
    fi
elif [[ "$COMPARE_BACKEND" == "impeller" ]]; then
    if ! grep -q "Using the Impeller rendering backend" <<<"$BACKEND_LOG"; then
        echo "Backend inesperado: COMPARE_BACKEND=impeller, mas o binário não" >&2
        echo "está usando Impeller. Remova a linha" >&2
        echo "fl_dart_project_set_enable_impeller(project, FALSE) do runner e" >&2
        echo "recompile: cd $REPO_ROOT/compare && flutter build linux --release" >&2
        exit 1
    fi
else
    echo "COMPARE_BACKEND inválido: $COMPARE_BACKEND (use skia ou impeller)" >&2
    exit 1
fi

mkdir -p "$OUT_DIR"

BASENAME="$(basename "$INPUT_FILE")"
NAME="${BASENAME%.*}"

# Modo debug (--vsb-debug, docs/formato/especificacao-v1.md §2.6): quando
# $INPUT_FILE já é um .vsb, a comparação sai só dele - debug-source.txt vira
# o arquivo que os `verovio` abaixo carregam, e debug-options.json (via
# --options-file/Toolkit::SetOptions) substitui as flags manuais de layout
# (--header none --footer none --no-instrument-labels e qualquer outra opção
# usada para gerar o pacote, ex. tamanho de página/espaçamento). Um .vsb sem
# os dois é rejeitado com uma mensagem clara antes de qualquer renderização.
SOURCE_FILE="$INPUT_FILE"
DEBUG_OPTIONS=""
if [[ "$INPUT_FILE" == *.vsb ]]; then
    DEBUG_SOURCE="$OUT_DIR/_compare-page-tmp-debug-source"
    DEBUG_OPTIONS="$OUT_DIR/_compare-page-tmp-debug-options.json"
    python3 - "$INPUT_FILE" "$DEBUG_SOURCE" "$DEBUG_OPTIONS" <<'PYEOF'
import sys
import zipfile

vsb_path, source_out, options_out = sys.argv[1:4]
with zipfile.ZipFile(vsb_path) as z:
    names = z.namelist()
    if "debug-source.txt" not in names or "debug-options.json" not in names:
        sys.exit(
            f"{vsb_path} não tem debug-source.txt/debug-options.json - "
            "gere com --vsb-debug para comparar só a partir do .vsb"
        )
    with open(source_out, "wb") as f:
        f.write(z.read("debug-source.txt"))
    with open(options_out, "wb") as f:
        f.write(z.read("debug-options.json"))
PYEOF
    SOURCE_FILE="$DEBUG_SOURCE"
fi
VSB_OPTIONS_ARGS=()
if [[ -n "$DEBUG_OPTIONS" ]]; then
    VSB_OPTIONS_ARGS=(--options-file "$DEBUG_OPTIONS")
fi

# .vsb sempre primeiro quando há --alternate: precisamos dele para achar o
# índice K da sequência (só para nomear a saída) antes de montar $PREFIX.
#
# --xml-id-seed fixo (42, a mesma semente usada em todo o resto do projeto -
# ver check-suffix-rule.py) só neste modo, e só fora do modo debug: sem ele,
# os `xml:id` sintéticos (system/score/scoreDef da seleção, e qualquer id
# ausente do arquivo de origem) sairiam diferentes a cada `verovio` chamado
# nesta função, e o `start` que o `.vsb` deste script gera nunca bateria com
# o que compare-corpus.sh descobriu num `.vsb` separado. Sem --alternate isso
# não importa (a comparação é só de pixel, nunca por id); no modo debug,
# --options-file sempre vence sobre --xml-id-seed nesta mesma chamada
# (Toolkit::SetOptions é aplicado depois de getopt_long inteiro em
# tools/main.cpp - ver o comentário lá), então passar os dois juntos seria
# enganoso: a semente usada é a que já estava gravada em debug-options.json.
ALT_XML_ID_SEED=42
ALT_SEED_ARGS=(--xml-id-seed "$ALT_XML_ID_SEED")
if [[ -n "$DEBUG_OPTIONS" ]]; then
    ALT_SEED_ARGS=()
fi
TMP_PREFIX="$OUT_DIR/_compare-page-tmp"
if [[ -n "$ALTERNATE" ]]; then
    "$VEROVIO_BIN" -t vsb "${ALT_SEED_ARGS[@]}" "${VSB_OPTIONS_ARGS[@]}" -o "$TMP_PREFIX" \
        --resource-path "$RESOURCE_PATH" "$SOURCE_FILE"
    if [[ ! -f "$TMP_PREFIX.vsb" ]]; then
        echo "Falha ao gerar o .vsb (ver mensagem do Verovio acima)." >&2
        exit 1
    fi
    SEQ_INDEX="$(python3 - "$TMP_PREFIX.vsb" "$ALTERNATE" <<'PYEOF'
import json
import sys
import zipfile

with zipfile.ZipFile(sys.argv[1]) as z:
    if "alternates.json" not in z.namelist():
        sys.exit(f"{sys.argv[1]} não tem alternates.json")
    alternates = json.loads(z.read("alternates.json"))
for k, seq in enumerate(alternates["sequences"]):
    if seq["start"] == sys.argv[2]:
        print(k)
        break
else:
    sys.exit(f"nenhuma sequência começa em '{sys.argv[2]}'")
PYEOF
)"
    PREFIX="$OUT_DIR/${NAME}-alt${SEQ_INDEX}-p${PAGE}"
    mv "$TMP_PREFIX.vsb" "$PREFIX.vsb"
else
    PREFIX="$OUT_DIR/${NAME}-p${PAGE}"
fi

# Prefixo sem pontos para as próximas renderizações: o `-o` do verovio trunca
# tudo a partir do último "." do caminho (RemoveExtension em tools/main.cpp),
# o que corromperia nomes de saída para arquivos de entrada cujo nome já tem
# pontos (ex.: alguns .mxl do corpus). Renderiza num nome temporário e move
# depois. ($TMP_PREFIX já foi usado acima para o .vsb, quando --alternate.)

# NÃO mexa nesta lista sem revalidar todos os números antigos: ela define o
# PNG de referência (4 SMuFL + 4 Liberation Serif, serif fixado).
FONTS=(
    "$REPO_ROOT/verovio/fonts/Leipzig/Leipzig.ttf"
    "$REPO_ROOT/verovio/fonts/Bravura/Bravura.otf"
    "$REPO_ROOT/verovio/fonts/Leland/Leland.otf"
    "$REPO_ROOT/verovio/fonts/Gootville/Gootville.otf"
    "$REPO_ROOT/verovio/data/text/LiberationSerif-Regular.ttf"
    "$REPO_ROOT/verovio/data/text/LiberationSerif-Italic.ttf"
    "$REPO_ROOT/verovio/data/text/LiberationSerif-Bold.ttf"
    "$REPO_ROOT/verovio/data/text/LiberationSerif-BoldItalic.ttf"
)
FONT_ARGS=()
for font in "${FONTS[@]}"; do
    FONT_ARGS+=(--font "$font")
done

echo "==> Renderizando SVG (página $PAGE${ALTERNATE:+, sequência $ALTERNATE})"
# P01c: o .vsb de referência carrega os padrões do bridge (--header none
# --footer none --no-instrument-labels, D-VSB-PADRAO) desde P01b; o SVG de
# referência precisa das mesmas três flags (ou, no modo debug, de todas as
# opções gravadas em debug-options.json - as três incluídas), senão toda
# página diverge. --alternate (P02d): --select-from troca a paginação normal
# pela da sequência antes do -p N, o mesmo mecanismo que o exportador usa
# (P02c).
if [[ -n "$DEBUG_OPTIONS" ]]; then
    if [[ -n "$ALTERNATE" ]]; then
        # --options-file sempre vence sobre qualquer outra flag desta mesma
        # chamada (mesma razão do ALT_SEED_ARGS acima), então --select-from
        # não pode ir como flag separada aqui - precisa estar dentro do JSON.
        # A semente fica a que já estava em debug-options.json (não importa
        # para o diff de pixel; ver o comentário de ALT_SEED_ARGS).
        DEBUG_OPTIONS_ALT="$OUT_DIR/_compare-page-tmp-debug-options-alt.json"
        python3 - "$DEBUG_OPTIONS" "$DEBUG_OPTIONS_ALT" "$ALTERNATE" <<'PYEOF'
import json
import sys

options_in, options_out, alternate = sys.argv[1:4]
with open(options_in) as f:
    options = json.load(f)
options["selectFrom"] = alternate
with open(options_out, "w") as f:
    json.dump(options, f)
PYEOF
        HEADER_ARGS=(--options-file "$DEBUG_OPTIONS_ALT")
    else
        HEADER_ARGS=(--options-file "$DEBUG_OPTIONS")
    fi
else
    HEADER_ARGS=(--header none --footer none --no-instrument-labels)
    if [[ -n "$ALTERNATE" ]]; then
        HEADER_ARGS+=(--select-from "$ALTERNATE" --xml-id-seed "$ALT_XML_ID_SEED")
    fi
fi
"$VEROVIO_BIN" -t svg -p "$PAGE" -o "$TMP_PREFIX" --resource-path "$RESOURCE_PATH" \
    "${HEADER_ARGS[@]}" "$SOURCE_FILE"
if [[ ! -f "$TMP_PREFIX.svg" ]]; then
    echo "Falha ao gerar o SVG da página $PAGE (ver mensagem do Verovio acima;" >&2
    echo "página inexistente na peça/sequência também falha aqui)." >&2
    exit 1
fi
mv "$TMP_PREFIX.svg" "$PREFIX.svg"

if [[ -z "$ALTERNATE" ]]; then
    echo "==> Renderizando .vsb (todas as páginas; a seleção é no scene-to-png)"
    "$VEROVIO_BIN" -t vsb "${VSB_OPTIONS_ARGS[@]}" -o "$TMP_PREFIX" --resource-path "$RESOURCE_PATH" "$SOURCE_FILE"
    if [[ ! -f "$TMP_PREFIX.vsb" ]]; then
        echo "Falha ao gerar o .vsb (ver mensagem do Verovio acima)." >&2
        exit 1
    fi
    mv "$TMP_PREFIX.vsb" "$PREFIX.vsb"
fi
# (--alternate já gerou e moveu o .vsb para $PREFIX.vsb mais acima, para achar
# o índice K da sequência antes de montar $PREFIX.)

echo "==> SVG -> PNG (referência)"
"$SVG_RENDER_BIN" "$PREFIX.svg" "$PREFIX-svg.png" "${FONT_ARGS[@]}" --pin-serif-family "Liberation Serif"

echo "==> Cena -> PNG (backend $COMPARE_BACKEND)"
SCENE_ALTERNATE_ARGS=()
if [[ -n "$ALTERNATE" ]]; then
    SCENE_ALTERNATE_ARGS=(--alternate "$ALTERNATE")
fi
"${COMPARE_RUN[@]}" scene-to-png "$PREFIX.vsb" "$PREFIX-scene.png" --page "$PAGE" "${SCENE_ALTERNATE_ARGS[@]}"

echo "==> Lendo dimensões dos PNGs"
read -r SVG_W SVG_H < <(python3 - "$PREFIX-svg.png" <<'PYEOF'
import struct
import sys

with open(sys.argv[1], "rb") as f:
    header = f.read(24)
width, height = struct.unpack(">II", header[16:24])
print(width, height)
PYEOF
)
read -r SCENE_W SCENE_H < <(python3 - "$PREFIX-scene.png" <<'PYEOF'
import struct
import sys

with open(sys.argv[1], "rb") as f:
    header = f.read(24)
width, height = struct.unpack(">II", header[16:24])
print(width, height)
PYEOF
)
if [[ "$SVG_W" != "$SCENE_W" || "$SVG_H" != "$SCENE_H" ]]; then
    echo "Dimensões diferentes: SVG ${SVG_W}x${SVG_H} vs cena ${SCENE_W}x${SCENE_H}." >&2
    echo "O PNG da cena deveria ter exatamente as dimensões do PNG do SVG." >&2
    exit 1
fi

echo "==> Diff (tolerância $TOLERANCE)"
DIFF_OUT="$("${COMPARE_RUN[@]}" diff "$PREFIX-svg.png" "$PREFIX-scene.png" "$PREFIX-diff.png" --tolerance "$TOLERANCE")"
echo "$DIFF_OUT"

# Linha final estável para R06a/P02d agregar em CSV sem reprocessar texto
# livre: peça;página;largura;altura;divergentes;total;pct. É a ÚLTIMA linha
# do stdout. "peça" ganha o sufixo "-alt<K>" com --alternate (o mesmo K do
# nome de arquivo), para não colidir com as linhas das páginas normais.
REPORT_NAME="$NAME"
if [[ -n "$ALTERNATE" ]]; then
    REPORT_NAME="${NAME}-alt${SEQ_INDEX}"
fi
STABLE="$(python3 - "$DIFF_OUT" <<'PYEOF'
import re
import sys

out = sys.argv[1]
total = re.search(r"Pixels comparados:\s+(\d+)", out)
diff = re.search(r"Pixels diferentes:\s+(\d+)\s+\(([0-9.]+)%\)", out)
if not total or not diff:
    sys.exit("não foi possível extrair as estatísticas do diff")
print(f"{diff.group(1)};{total.group(1)};{diff.group(2)}")
PYEOF
)"
echo "${REPORT_NAME};${PAGE};${SCENE_W};${SCENE_H};${STABLE}"
