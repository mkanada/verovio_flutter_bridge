#!/usr/bin/env bash
# Builds the Emscripten/wasm Verovio toolkit (W01), with the bridge's
# RenderToBridgeFile/RenderToBridgeJson exported (exports.txt), via the
# upstream emscripten/buildToolkit (Perl). Default flags (-w, humdrum on,
# no modularize) match how the upstream npm package is built, and match
# what compare/out/w01/index.html expects to load.
#
# Output: verovio/emscripten/build/verovio-toolkit-hum.js — SINGLE_FILE=1,
# so the wasm binary is embedded as base64 inside the .js (no separate
# .wasm to serve). verovio/emscripten/{data,build,CMakeFiles,CMakeCache.txt}
# are git-ignored (see verovio/.gitignore, upstream).
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
emscripten_dir="$root_dir/emscripten"

command -v emcc >/dev/null 2>&1 || source "$HOME/emsdk/emsdk_env.sh"
command -v emcc >/dev/null 2>&1 || {
    echo "ERROR: emcc not found. Install emsdk (see docs/plano/W01-verovio-wasm.md)." >&2
    exit 1
}

cd "$emscripten_dir"
perl buildToolkit -w -c "$@"
ls -lh build/verovio-toolkit-hum.js
