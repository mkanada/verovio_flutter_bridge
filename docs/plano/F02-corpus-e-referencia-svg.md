# F02 — Corpus + referência SVG→PNG reproduzível

**Depende de:** F01 · **Decisão necessária:** não

## Objetivo

Trazer o corpus de teste e a metade da ferramenta de comparação que já está
pronta e é independente do formato de saída (`svg_render` em Rust e o `diff`
pixel a pixel), e provar que o PNG de referência sai **idêntico** ao do
projeto anterior. Sem essa base fixa, nenhum número de paridade dos passos R é
comparável com o histórico.

## Ler antes (só isto)

- `../verovio_lottie/compare/README.md` — seções "Por que resvg, não Flutter",
  "Build", "Execução: modo batch sob xvfb" e "Pegadinhas do resvg".
- `../verovio_lottie/compare/scripts/compare-page.sh` (o fluxo inteiro de uma
  página, incluindo a lista de fontes passada ao `svg_render`).
- `../verovio_lottie/corpus/README.md`.

## O que fazer

1. Copiar o corpus (só as partituras, **não** `corpus/lottie/`):

   ```sh
   rsync -a --exclude 'lottie' ../verovio_lottie/corpus/ corpus/
   ```

2. Copiar `compare/svg_render/` (Rust, `resvg`) inteiro, sem alterações.

3. Copiar o app Flutter de comparação mantendo **só** o que não é Lottie:

   - manter: `compare/pubspec.yaml`, `compare/lib/main.dart` (podando os
     comandos removidos), `compare/lib/src/diff.dart`, `compare/linux/`,
     `compare/analysis_options.yaml`, `compare/test/`.
   - remover: `lottie_native.dart`, `lottie_package.dart`, `widget_render.dart`,
     `script.dart`, `render_jobs.dart` e as dependências
     `dotlottie_flutter`/`verovio_viewer` do `pubspec.yaml`.
   - o comando `scene-to-png` entra em R05; aqui o binário expõe só `diff`.

4. Copiar `compare/scripts/compare-page.sh` e `compare-corpus.sh`, comentando
   (não apagando) os trechos que chamam o exportador; eles são reescritos em
   R05/R06. O trecho de SVG→PNG deve continuar funcional desde já.

5. Build dos dois binários (ver "Convenções" no README do plano).

## Fora de escopo

- Qualquer render de cena/Flutter (R05).
- Mudar o `svg_render` (ele já está correto: `--pin-serif-family`, remoção de
  `<title>` aninhado, fundo branco opaco).

## Critérios de aceite

1. `cd compare/svg_render && cargo build --release` compila.
2. `cd compare && flutter build linux --release` compila, e
   `compare … --help` lista o comando `diff`.
3. **PNG de referência idêntico ao do projeto anterior.** Para pelo menos 3
   peças do corpus (uma de `mei`, uma de `musicxml`, e Clair de Lune, que é a
   com mais texto comum), página 1:

   ```sh
   ./verovio/tools/verovio -t svg -p 1 --resource-path verovio/data -o /tmp/ref "$PECA"
   ./compare/svg_render/target/release/svg_render /tmp/ref.svg /tmp/new-svg.png \
     --font verovio/fonts/Leipzig/Leipzig.ttf \
     --font verovio/fonts/Bravura/Bravura.otf \
     --font verovio/fonts/Leland/Leland.otf \
     --font verovio/fonts/Gootville/Gootville.otf \
     --font verovio/data/text/LiberationSerif-Regular.ttf \
     --font verovio/data/text/LiberationSerif-Italic.ttf \
     --font verovio/data/text/LiberationSerif-Bold.ttf \
     --font verovio/data/text/LiberationSerif-BoldItalic.ttf \
     --pin-serif-family "Liberation Serif"
   # e o mesmo comando no repositório antigo, gerando /tmp/old-svg.png
   xvfb-run -a ./compare/build/linux/x64/release/bundle/compare diff \
     /tmp/old-svg.png /tmp/new-svg.png /tmp/d.png --tolerance 0
   ```

   O diff deve reportar **0 pixels divergentes** com tolerância **0**.
4. `corpus/` tem as 5 peças MEI e as 5 MusicXML, e **nenhum** `.lottie`.
5. `compare/out/` está no `.gitignore` e não aparece em `git status`.

## Notas de execução

(a preencher por quem executar)
