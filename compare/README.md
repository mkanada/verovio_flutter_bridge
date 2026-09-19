# compare — comparação visual `.vsb` × SVG

Dois binários, em toolchains diferentes:

- `compare` (Flutter/Linux, modo batch): `cd compare && flutter build linux --release`
  → `compare/build/linux/x64/release/bundle/compare`, com os comandos `diff`
  e `scene-to-png` (`compare/lib/main.dart`). Precisa de display mesmo em
  batch: sem `DISPLAY`, rode sob `xvfb-run -a` (os scripts em `scripts/` já
  fazem isso).
- `svg_render` (Rust, `resvg` 0.48 + `tiny-skia`, software puro, sem xvfb):
  `cd compare/svg_render && cargo build --release`
  → `compare/svg_render/target/release/svg_render`.

## Backend gráfico oficial: Impeller (decisão R05a, 2026-09-19)

O lado de referência (`resvg` + `tiny-skia`) é fixo; o que muda com o backend
é só o lado da cena. Medição R05a (tolerância 32 na época — hoje o padrão é
128; 6 237 000 px, Flutter
3.47.4; tempos incluem startup sob xvfb):

| Página (perfil) | Impeller | Skia | Tempo Imp / Skia |
| --- | --- | --- | --- |
| Maple Leaf Rag p1 (muita nota) | 0,3603% (22 475) | 0,6824% (42 561) | 0,92s / 0,89s |
| Clair de Lune p1 (muito texto) | 0,8590% (53 578) | 0,7765% (48 430) | 0,99s / 1,02s |
| Chopin Étude p1 (tracejado octave) | 0,4978% (31 046) | 0,6048% (37 722) | 0,94s / 0,91s |
| Nocturne p1 (arpejo −90°) | 0,6794% (42 373) | 0,8800% (54 883) | 0,95s / 0,95s |
| Satie Gymnopédie p2 (pouco conteúdo) | 0,0552% (3 445) | 0,0394% (2 456) | 0,82s / 0,77s |
| **Média** | **0,4903%** | **0,5966%** | — |

Impeller vence na média e em 3/5 páginas; ambos são determinísticos
(PNG byte-idêntico entre execuções, `cmp`). Impeller é ainda o padrão do
Flutter 3.47 no Linux e o opt-out Skia será removido em versão futura —
por isso ele é o oficial.

Como o backend é decidido em tempo de compilação nesta versão do Flutter
(não existe `flutter build linux --no-enable-impeller`, e
`FLUTTER_ENABLE_IMPELLER=0` em execução **não** troca — sondado em R05a),
o build padrão (sem linha extra no runner) já é Impeller. Para medir com
Skia: adicione `fl_dart_project_set_enable_impeller(project, FALSE);` após
`fl_dart_project_new()` em `compare/linux/runner/my_application.cc`
([doc oficial](https://docs.flutter.dev/perf/impeller)), recompile, e rode
os scripts com `COMPARE_BACKEND=skia`. Como saber qual está ativo: o log do
embedder no stderr diz `Using the Impeller rendering backend (OpenGLESSDF)`
quando é Impeller, e nada quando é Skia.

## Fluxo ponta a ponta (R05b)

```
compare-page.sh <arquivo> <página> [tolerância]
  → compare/out/<peça>-p<N>-svg.png      (referência)
  → compare/out/<peça>-p<N>-scene.png    (cena)
  → compare/out/<peça>-p<N>-diff.png     (diferença)
  → estatística no stdout; ÚLTIMA linha do stdout é estável para R06a:
    peça;página;largura;altura;divergentes;total;pct
```

O `.vsb` é sempre gerado com todas as páginas (`-t vsb` ignora `-p`) e a
página é selecionada no `scene-to-png` (`--page` 1-based, como o `-p` do
Verovio). `COMPARE_BACKEND` (padrão `impeller`) aborta o script se o binário
estiver rodando outro backend. Detalhes que o script preserva: nomes com
ponto (renderiza em prefixo temporário), lista de 8 fontes +
`--pin-serif-family "Liberation Serif"` (não mexa sem revalidar os números).

## Varredura do corpus (R06a)

`compare-corpus.sh [tolerância]` chama o `compare-page.sh` por página (34
no total) e agrega em `compare/corpus/resultado.csv`
(`peca;pagina;largura;altura;divergentes;total;pct;bytes_vsb`). Ao contrário
de `compare/out/`, `compare/corpus/` é **versionado** (só PNGs, CSV e logs;
`.svg`/`.vsb` são regeneráveis) — dá para ver cada página e sua história no
próprio git.
