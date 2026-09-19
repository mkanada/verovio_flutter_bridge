#!/usr/bin/env bash
# Varredura do corpus (R06a): chama o compare-page.sh de R05b por página e
# agrega a linha estável em <dir-do-corpus>/resultado.csv.
#
# Uso: compare/scripts/compare-corpus.sh [tolerância]
#
# Saídas em $CORPUS_DIR (padrão: compare/corpus/, VERSIONADO — é assim que as
# páginas ficam visíveis após commit+push; desvio do passo registrado nas
# notas de R06a): por página, <peça>-p<N>.svg, <peça>-p<N>.vsb, os três PNGs
# (-svg, -scene, -diff) e o log da página (<peça>-p<N>.log), mais o
# consolidado:
#   resultado.csv: peca;pagina;largura;altura;divergentes;total;pct;bytes_vsb
# O .gitignore dentro do diretório versiona só PNGs, CSV e logs; .svg/.vsb
# são intermediários regeneráveis (o próprio script os recria em ~3 min).
# Para voltar ao comportamento do passo (tudo git-ignorado):
#   CORPUS_DIR=compare/out/corpus ./compare/scripts/compare-corpus.sh
#
# O número de páginas de cada peça é sondado com `verovio -t svg -a` — nunca
# hardcode (muda com versão/flags do Verovio). A varredura aborta se o total
# não for 34 páginas (o tamanho do corpus em S08/R06a) ou se qualquer página
# falhar. Backend via COMPARE_BACKEND (padrão: impeller, o oficial de R05a),
# repassado ao compare-page.sh.
set -euo pipefail

TOLERANCE=${1:-128}
COMPARE_BACKEND="${COMPARE_BACKEND:-impeller}"
export COMPARE_BACKEND

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

PAGE_SCRIPT="$SCRIPT_DIR/compare-page.sh"
VEROVIO_BIN="$REPO_ROOT/verovio/tools/verovio"
RESOURCE_PATH="$REPO_ROOT/verovio/data"
OUT_DIR="$REPO_ROOT/compare/out"
CORPUS_DIR="${CORPUS_DIR:-$REPO_ROOT/compare/corpus}"

if [[ ! -x "$VEROVIO_BIN" ]]; then
    echo "Binário do Verovio não encontrado em $VEROVIO_BIN." >&2
    echo "Compile com: cd $REPO_ROOT/verovio/tools && cmake ../cmake && make -j4" >&2
    exit 1
fi

if [[ ! -x "$PAGE_SCRIPT" ]]; then
    echo "Script compare-page.sh não encontrado em $PAGE_SCRIPT." >&2
    exit 1
fi

mkdir -p "$CORPUS_DIR"

CSV="$CORPUS_DIR/resultado.csv"
echo "peca;pagina;largura;altura;divergentes;total;pct;bytes_vsb" > "$CSV"

shopt -s nullglob
INPUT_FILES=("$REPO_ROOT"/corpus/mei/*.mei "$REPO_ROOT"/corpus/musicxml/*.mxl)
shopt -u nullglob
if [[ ${#INPUT_FILES[@]} -eq 0 ]]; then
    echo "Nenhum arquivo em corpus/mei nem corpus/musicxml." >&2
    exit 1
fi

TOTAL_PAGES=0
START=$(date +%s)

for INPUT_FILE in "${INPUT_FILES[@]}"; do
    BASENAME="$(basename "$INPUT_FILE")"
    NAME="${BASENAME%.*}"

    # Sonda o número de páginas: `-a` gera um SVG por página num prefixo sem
    # pontos (RemoveExtension do verovio truncaria nomes com ponto). Só conta;
    # a comparação em si é toda dentro do compare-page.sh.
    TMP_PROBE="$CORPUS_DIR/_probe-tmp"
    rm -f "$TMP_PROBE".svg "$TMP_PROBE"_*.svg
    "$VEROVIO_BIN" -t svg -a -o "$TMP_PROBE" --resource-path "$RESOURCE_PATH" \
        "$INPUT_FILE" >/dev/null
    shopt -s nullglob
    PROBE_SVGS=("$TMP_PROBE"_*.svg)
    shopt -u nullglob
    if [[ ${#PROBE_SVGS[@]} -eq 0 ]]; then
        PROBE_SVGS=("$TMP_PROBE.svg")
    fi
    PAGE_COUNT=${#PROBE_SVGS[@]}
    rm -f "${PROBE_SVGS[@]}"

    echo "=== $NAME ($PAGE_COUNT páginas) ==="

    for ((P = 1; P <= PAGE_COUNT; P++)); do
        PAGE_PREFIX="${NAME}-p${P}"
        LOG="$CORPUS_DIR/${PAGE_PREFIX}.log"
        if ! "$PAGE_SCRIPT" "$INPUT_FILE" "$P" "$TOLERANCE" \
            >"$LOG" 2>"$LOG.stderr"; then
            echo "FALHA em $PAGE_PREFIX (ver $LOG e $LOG.stderr)." >&2
            exit 1
        fi
        STABLE="$(tail -n 1 "$LOG")"
        # Formato exato: peça;página;largura;altura;divergentes;total;pct
        # (7 campos, os 6 últimos numéricos).
        if ! [[ "$STABLE" =~ ^[^[:space:]]+\;[0-9]+\;[0-9]+\;[0-9]+\;[0-9]+\;[0-9]+\;[0-9.]+$ ]]; then
            echo "FALHA em $PAGE_PREFIX: linha estável fora do formato:" >&2
            echo "$STABLE" >&2
            exit 1
        fi
        # Traz as 5 saídas do compare-page.sh (compare/out/) para o corpus/.
        for f in "$OUT_DIR/${PAGE_PREFIX}.svg" "$OUT_DIR/${PAGE_PREFIX}.vsb" \
            "$OUT_DIR/${PAGE_PREFIX}-svg.png" \
            "$OUT_DIR/${PAGE_PREFIX}-scene.png" \
            "$OUT_DIR/${PAGE_PREFIX}-diff.png"; do
            if [[ ! -f "$f" ]]; then
                echo "FALHA em $PAGE_PREFIX: esperado $f não gerado." >&2
                exit 1
            fi
            mv "$f" "$CORPUS_DIR/"
        done
        VSB_BYTES="$(stat -c%s "$CORPUS_DIR/${PAGE_PREFIX}.vsb")"
        echo "${STABLE};${VSB_BYTES}" >> "$CSV"
        echo "${STABLE};${VSB_BYTES}"
        TOTAL_PAGES=$((TOTAL_PAGES + 1))
    done
done

END=$(date +%s)
echo
echo "Total: $TOTAL_PAGES páginas em $((END - START))s → $CSV"
if [[ "$TOTAL_PAGES" != "34" ]]; then
    echo "FALHA: esperado 34 páginas (tamanho do corpus em S08/R06a)." >&2
    exit 1
fi
