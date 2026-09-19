#!/usr/bin/env bash
# Compara uma página de uma partitura no fluxo `.vsb`, de ponta a ponta (R05b):
#
#   compare-page.sh <arquivo> <página> [tolerância]
#     → compare/out/<peça>-p<N>-svg.png      (referência: verovio -t svg + svg_render)
#     → compare/out/<peça>-p<N>-scene.png    (cena: verovio -t vsb + compare scene-to-png)
#     → compare/out/<peça>-p<N>-diff.png     (imagem de diferença)
#     → estatística no stdout + linha final estável para R06a agregar em CSV
#
# Páginas: o `-p` do Verovio é 1-based e o `page.index` no `.vsb` é 0-based.
# O `.vsb` é SEMPRE gerado com todas as páginas (`-t vsb` ignora `-p`; achado
# de R02d em tools/main.cpp) e a página é selecionada no `scene-to-png`
# (`--page` 1-based, como o `-p` do Verovio). O SVG é gerado só da página
# pedida (`-t svg -p N`).
#
# Backend gráfico (R05a): o Flutter 3.47 usa Impeller por padrão no Linux e o
# backend é decidido em tempo de compilação
# (fl_dart_project_set_enable_impeller em compare/linux/runner/my_application.cc;
# sem a linha = Impeller). `COMPARE_BACKEND` diz qual backend este script
# espera (`impeller`, padrão, ou `skia`) e o script ABORTA se o binário
# `compare` estiver rodando outro — para ninguém medir com o backend errado
# por acidente. Para medir com Skia: adicione a linha FALSE ao runner,
# `cd compare && flutter build linux --release`, e rode com
# `COMPARE_BACKEND=skia`.
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
    echo "Uso: $0 <arquivo> <página> [tolerância]" >&2
    exit 1
fi

INPUT_FILE=$1
PAGE=$2
TOLERANCE=${3:-32}
COMPARE_BACKEND="${COMPARE_BACKEND:-impeller}"

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
if [[ "$COMPARE_BACKEND" == "impeller" ]]; then
    if ! grep -q "Using the Impeller rendering backend" <<<"$BACKEND_LOG"; then
        echo "Backend inesperado: COMPARE_BACKEND=impeller, mas o binário não" >&2
        echo "está usando Impeller. Recompile sem a linha" >&2
        echo "fl_dart_project_set_enable_impeller(project, FALSE):" >&2
        echo "  cd $REPO_ROOT/compare && flutter build linux --release" >&2
        exit 1
    fi
elif [[ "$COMPARE_BACKEND" == "skia" ]]; then
    if grep -q "Using the Impeller rendering backend" <<<"$BACKEND_LOG"; then
        echo "Backend inesperado: COMPARE_BACKEND=skia, mas o binário está" >&2
        echo "usando Impeller. Adicione" >&2
        echo "  fl_dart_project_set_enable_impeller(project, FALSE);" >&2
        echo "em compare/linux/runner/my_application.cc, recompile e rode de novo." >&2
        exit 1
    fi
else
    echo "COMPARE_BACKEND inválido: $COMPARE_BACKEND (use impeller ou skia)" >&2
    exit 1
fi

mkdir -p "$OUT_DIR"

BASENAME="$(basename "$INPUT_FILE")"
NAME="${BASENAME%.*}"
PREFIX="$OUT_DIR/${NAME}-p${PAGE}"

# Renderiza com um prefixo sem pontos: o `-o` do verovio trunca tudo a partir
# do último "." do caminho (RemoveExtension em tools/main.cpp), o que
# corromperia nomes de saída para arquivos de entrada cujo nome já tem pontos
# (ex.: alguns .mxl do corpus). Renderiza num nome temporário e move depois.
TMP_PREFIX="$OUT_DIR/_compare-page-tmp"

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

echo "==> Renderizando SVG (página $PAGE)"
"$VEROVIO_BIN" -t svg -p "$PAGE" -o "$TMP_PREFIX" --resource-path "$RESOURCE_PATH" "$INPUT_FILE"
if [[ ! -f "$TMP_PREFIX.svg" ]]; then
    echo "Falha ao gerar o SVG da página $PAGE (ver mensagem do Verovio acima;" >&2
    echo "página inexistente na peça também falha aqui)." >&2
    exit 1
fi
mv "$TMP_PREFIX.svg" "$PREFIX.svg"

echo "==> Renderizando .vsb (todas as páginas; a seleção é no scene-to-png)"
"$VEROVIO_BIN" -t vsb -o "$TMP_PREFIX" --resource-path "$RESOURCE_PATH" "$INPUT_FILE"
if [[ ! -f "$TMP_PREFIX.vsb" ]]; then
    echo "Falha ao gerar o .vsb (ver mensagem do Verovio acima)." >&2
    exit 1
fi
mv "$TMP_PREFIX.vsb" "$PREFIX.vsb"

echo "==> SVG -> PNG (referência)"
"$SVG_RENDER_BIN" "$PREFIX.svg" "$PREFIX-svg.png" "${FONT_ARGS[@]}" --pin-serif-family "Liberation Serif"

echo "==> Cena -> PNG (backend $COMPARE_BACKEND)"
"${COMPARE_RUN[@]}" scene-to-png "$PREFIX.vsb" "$PREFIX-scene.png" --page "$PAGE"

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

# Linha final estável para R06a agregar em CSV sem reprocessar texto livre:
# peça;página;largura;altura;divergentes;total;pct. É a ÚLTIMA linha do stdout.
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
echo "${NAME};${PAGE};${SCENE_W};${SCENE_H};${STABLE}"
