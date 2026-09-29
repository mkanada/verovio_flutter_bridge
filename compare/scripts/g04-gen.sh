#!/usr/bin/env bash
# G04b/G04c (descartável): gera .vsb, .mid e timemap de todo o corpus (+ repetições
# + corpus/fantasma) num diretório, para comparar antes/depois.
# Uso: compare/scripts/g04-gen.sh <dir-saida> [extra flags do verovio]
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="$1"; shift || true
V="$ROOT/verovio/tools/verovio"; R="$ROOT/verovio/data"
mkdir -p "$OUT"
shopt -s nullglob
run() {
    local f="$1" b; b="$(basename "$f")"; b="${b%.*}"
    local t0 t1
    t0=$(date +%s.%N)
    "$V" -t vsb --xml-id-seed 42 --resource-path "$R" "$@" -o "$OUT/$b.vsb" "$f" >/dev/null 2>"$OUT/$b.vsb.log" || echo "FALHA vsb $f"
    t1=$(date +%s.%N)
    echo "$b;$(echo "$t1 - $t0" | bc)" >> "$OUT/tempos.csv"
    "$V" -t midi --xml-id-seed 42 --resource-path "$R" -o "$OUT/$b.mid" "$f" >/dev/null 2>&1 || echo "FALHA midi $f"
    "$V" -t timemap --xml-id-seed 42 --resource-path "$R" -o "$OUT/$b.timemap.json" "$f" >/dev/null 2>&1 || true
}
rm -f "$OUT/tempos.csv"
for f in "$ROOT"/corpus/mei/*.mei "$ROOT"/corpus/musicxml/*.mxl "$ROOT"/corpus/repeticoes/*.mei "$ROOT"/corpus/repeticoes/*.musicxml "$ROOT"/corpus/fantasma/*.mei; do
    run "$f"
done
