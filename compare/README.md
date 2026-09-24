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

## Backend gráfico oficial: Skia (decisão de 2026-09-20, revendo R05a)

O lado de referência (`resvg` + `tiny-skia`) é fixo; o que muda com o backend
é só o lado da cena. Em R05a (2026-09-19) o Impeller foi escolhido por ser o
padrão do Flutter 3.47 e vencer na média (0,49% × 0,60% Skia a tolerância 32).
Em 2026-09-20 o usuário descobriu que o **Impeller no Linux não aplica
antialiasing**, e a comparação passou a rodar em **Skia**: o runner
(`compare/linux/runner/my_application.cc`) chama
`fl_dart_project_set_enable_impeller(project, FALSE)`. O backend é decidido em
tempo de compilação (não há `flutter build linux --no-enable-impeller`, e
`FLUTTER_ENABLE_IMPELLER=0` em execução **não** troca — sondado em R05a), então
basta o build padrão: `cd compare && flutter build linux --release`.

Como saber qual está ativo: o log do embedder no stderr diz
`Using the Impeller rendering backend (OpenGLESSDF)` quando é Impeller, e nada
quando é Skia. Os scripts conferem isso e abortam se o binário não bate com
`COMPARE_BACKEND` (padrão `skia`). Para medir com Impeller: remova a linha
`FALSE` do runner, recompile e rode com `COMPARE_BACKEND=impeller`.

Re-medição do corpus (34 páginas, tolerância 128, mesmo commit do exportador):

| | Impeller | Skia |
| --- | --- | --- |
| Média | 0,008456% | 0,008800% |
| Max | 0,038624% | 0,039330% |
| Páginas ≤ 0,01% | 27/34 | 27/34 |

Skia é ligeiramente pior (32/34 páginas, 1 a ~73 px de diferença por página) e
determinístico (`cmp` byte-idêntico entre execuções). Nos PNGs do
`scene-to-png` (rasterização offscreen, `Picture.toImage`) o Impeller **tinha**
antialiasing — a mesma quantidade de tons intermediários que a referência —,
então o defeito relatado provavelmente não afeta este pipeline; ver
[`docs/relatorio-paridade.md`](../docs/relatorio-paridade.md).

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
Verovio). `COMPARE_BACKEND` (padrão `skia`) aborta o script se o binário
estiver rodando outro backend. Detalhes que o script preserva: nomes com
ponto (renderiza em prefixo temporário), lista de 8 fontes +
`--pin-serif-family "Liberation Serif"` (não mexa sem revalidar os números).

**Modo debug (§2.6):** `<arquivo>` também aceita um `.vsb` gerado com
`--vsb-debug` — nesse caso a comparação sai só dele, sem a partitura original
nem as flags do Verovio usadas para gerá-lo (o script extrai
`debug-source.txt`/`debug-options.json` de dentro do pacote e os usa em vez
de `--header none --footer none --no-instrument-labels`, via a flag de CLI
`--options-file`). Útil para reportar/depurar uma divergência sem precisar
reconstruir o comando original: `verovio -t vsb --vsb-debug ... peça.mei -o
peça` e depois `compare-page.sh compare/out/peça.vsb 1`.

## Varredura do corpus (R06a)

`compare-corpus.sh [tolerância]` chama o `compare-page.sh` por página (34
no total) e agrega em `compare/corpus/resultado.csv`
(`peca;pagina;largura;altura;divergentes;total;pct;bytes_vsb`). Ao contrário
de `compare/out/`, `compare/corpus/` é **versionado** (só PNGs, CSV e logs;
`.svg`/`.vsb` são regeneráveis) — dá para ver cada página e sua história no
próprio git.

### Pendência conhecida: um `.vsb` por página, cada um com a peça inteira

O `compare-page.sh` gera um `.vsb` por página comparada
(`<peça>-p1.vsb`, `<peça>-p2.vsb`, …), mas **`-t vsb` sempre exporta a peça
inteira** — a seleção de página é do `scene-to-png`. Ou seja, os N arquivos
de uma peça são cópias quase idênticas do mesmo conteúdo, e a coluna
`bytes_vsb` do CSV é o tamanho da **peça**, não o da página (foi isso que
induziu ao erro de ler `bytes_vsb` como custo por página). A corrigir no
futuro: gerar o `.vsb` uma vez por peça e reusá-lo nas páginas, e deixar
claro no CSV que o tamanho é por peça. Anotado em 2026-09-20; não mexer
agora — mudar isso altera os nomes dos artefatos da varredura.
