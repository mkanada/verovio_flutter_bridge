# R02d — Primeira imagem: `scene-to-png` mínimo e sobreposição

**Depende de:** R02c, F02 · **Decisão necessária:** não

## Objetivo

Sair do teste unitário e ver a página desenhada: um comando que lê um `.vsb`
e escreve um PNG, e a primeira conferência visual contra o PNG do SVG. Ainda
faltam glifos e texto, então o critério **não** é percentual — é alinhamento:
as linhas que existem têm que cair exatamente sobre as do SVG.

## Ler antes (só isto)

- `compare/lib/main.dart` (o `ArgParser` atual, com o comando `diff`) e
  `compare/lib/src/diff.dart`.
- `compare/scripts/compare-page.sh` (vindo de F02; o trecho SVG→PNG funciona,
  o trecho Lottie está comentado).
- `score_bridge/lib/src/scene_painter.dart` (R02b/R02c).

## Contexto que você precisa (não vá procurar, está aqui)

- O `compare` é um **app Flutter/Linux** em modo batch: precisa de display.
  Sem `DISPLAY`, rode sob `xvfb-run -a` (os scripts já fazem isso).
  Build: `cd compare && flutter build linux --release` →
  `compare/build/linux/x64/release/bundle/compare`.
- O PNG de referência é gerado pelo binário Rust `compare/svg_render`
  (`resvg` 0.48 + `tiny-skia`), que **compõe sobre fundo branco opaco**. O
  PNG da cena precisa do mesmo fundo branco opaco, senão o diff acusa a
  página inteira.
- As dimensões do PNG do SVG vêm de `width`/`height` do `<svg>` raiz, que são
  `widthPx`/`heightPx` da página no `.vsb` (numa A4 do corpus: 2100×2970).
  Use `page.widthPx`/`page.heightPx` quando `--width/--height` forem omitidos.
- `verovio -t vsb -p N` gera o pacote de **uma** página; sem `-p`, todas. O
  índice de página no `.vsb` é 0-based (`page.index`), enquanto o `-p` do
  Verovio é 1-based — erre isso e você compara a página errada e perde uma
  tarde.
- O `-o` do Verovio trunca o caminho a partir do último `.` (`RemoveExtension`
  em `tools/main.cpp`): para entradas com ponto no nome (vários `.mxl` do
  corpus), renderize num nome temporário e mova depois — o
  `compare-page.sh` já tem esse cuidado, copie-o.

## O que fazer

1. Adicionar em `compare/pubspec.yaml` a dependência de caminho:

   ```yaml
   dependencies:
     score_bridge:
       path: ../score_bridge
   ```

2. Comando novo em `compare/lib/main.dart`:

   ```
   compare scene-to-png <entrada.vsb|json> <saida.png> \
           --page N [--width W --height H]
   ```

   Implementação: `PictureRecorder` + `Canvas` → pinta fundo branco opaco →
   `ScenePainter.paint` → `Picture.toImage(W, H)` →
   `toByteData(format: ImageByteFormat.png)` → grava.

3. Gerar, para uma peça simples (Gymnopédie ou Scarlatti), os dois PNGs da
   página 1 e **sobrepor** as imagens (um script Python de 20 linhas com
   `image`/PIL, ou o próprio `compare diff` com tolerância alta só para ver a
   forma do resíduo).

## Fora de escopo

- Reescrever `compare-page.sh` para o fluxo completo (R05b).
- Decidir backend gráfico (R05a) — use o padrão do Flutter e **registre qual
  foi** nas notas, porque o número muda com o backend.
- Perseguir percentual de divergência: sem glifos nem texto, a divergência
  vai ser de vários por cento e isso é esperado.

## Critérios de aceite

1. `cd compare && flutter build linux --release` compila com o comando novo.
2. `compare scene-to-png` gera um PNG com as dimensões exatas do PNG do SVG
   para a página 1 de duas peças diferentes.
3. **Sobreposição sem deslocamento**: nas duas peças, pentagramas, barras de
   compasso e hastes coincidem com os do SVG. Anexe a imagem sobreposta (ou o
   diff) nas notas de execução. Qualquer deslocamento constante indica erro na
   transformação de página (R02b), e qualquer deslocamento que cresce com a
   posição indica escala errada.
4. A espessura das linhas bate a olho nu: um pentagrama do SVG e o da cena
   sobrepostos não mostram borda dupla. Se a linha da cena sair
   sistematicamente mais fina ou mais grossa, o erro está no `strokeWidth` de
   R02c (provavelmente escala aplicada duas vezes).
5. Nas notas: a peça usada, o comando exato, o backend gráfico ativo e a
   imagem.

## Notas de execução

Executado em 2026-09-19. `compare/pubspec.yaml` ganhou a dependência de
caminho `score_bridge: path: ../score_bridge`; criado
`compare/lib/src/scene_to_png.dart` (`sceneToPng`: fundo branco opaco em
pixels de saída + `ScenePainter.paint` via `PictureRecorder` →
`toImage(W, H)` → PNG; `--page` 1-based como o `-p` do Verovio, `--width`/
`--height` omitidos viram `widthPx`/`heightPx`) e o subcomando
`scene-to-png` em `compare/lib/main.dart` (ajuda lista `diff, scene-to-png`;
página fora do intervalo e inteiro inválido dão erro legível, sem throw
cru). `flutter analyze` limpo, `dart format` limpo, `flutter test` 4/4,
`flutter build linux --release` ok (critério 1).

Peças (página 1, comandos exatos a partir da raiz; nomes temporários sem
ponto pelo `RemoveExtension`, como no `compare-page.sh`):
- `corpus/musicxml/Erik_Satie_-_Gymnopedie_No.1.mxl` (Satie) e
  `corpus/mei/Scarlatti_Sonata_in_C-major.mei` (Scarlatti).
- SVG: `verovio/tools/verovio -t svg -p 1 -o compare/out/_r02d-tmp
  --resource-path verovio/data <peça>` → `r02d-{satie,scarlatti}-p1.svg`;
  PNG: `svg_render` com as 8 fontes + `--pin-serif-family "Liberation Serif"`
  → `r02d-*-p1-svg.png` (2100×2970).
- Cena: `verovio -t vsb -p 1 ...` → `r02d-*-p1.vsb`; `xvfb-run -a
  compare/build/linux/x64/release/bundle/compare scene-to-png
  <...>.vsb <...>-scene.png --page 1` → `r02d-*-p1-scene.png` (2100×2970
  exatos nas duas peças — critério 2).
- Backend ativo (log do embedder sob xvfb): **Impeller
  (OpenGLES-SDF)** — `Using the Impeller rendering backend (OpenGLESSDF)`;
  Flutter 3.47.4. A decisão Impeller×Skia continua em R05a.

Sobreposição (critério 3, quantitativo em vez de olho nu; scripts Python
com PIL+numpy, limiar de tinta <128):
- `diff --tolerance 32` (tolerância da época): Satie 126 977/6 237 000 = **2,0359%**, Scarlatti
  122 333 = **1,9614%**, maxDiff 255 (diferenças esperadas: glifos e texto
  ausentes em R02d). Diffs em `r02d-*-p1-diff32.png`.
- Teste de deslocamento ±3px: a cobertura "tinta da cena sobre tinta do
  SVG" é máxima em (0,0) nas duas peças (Satie 87,62%, Scarlatti 95,68%) —
  **nenhum deslocamento constante** (erro de transformação de R02b
  descartado).
- Picos de pauta (faixa x 400..1700): 102/102 (Satie) e 146/148
  (Scarlatti) picos da cena casados com picos do SVG a ≤5px, de y≈185 até
  y≈2906; offset médio −0,11px / −0,05px e inclinação offset×y de
  +4,6e-05 / −2,5e-05 px/px (≈0,1px na página inteira) — **sem erro de
  escala** (critério 3: deslocamento que cresce com a posição descartado).
- Espessura (critério 4): perfil de escuridão de uma linha de pauta em
  janela limpa de 200 colunas é idêntico nos dois (`[2.2 2.2 2.2 128.1
  192.5 ...]` vs `[2.2 2.2 2.2 129.3 191.3 ...]` — a linha cai entre as
  mesmas duas fileiras de pixels, com o mesmo peso); a contagem binária
  <128 oscila 1↔2px porque o núcleo está exatamente sobre o limiar 128,
  igual nos dois renderizadores — **sem borda dupla nem erro sistemático
  de `strokeWidth`**. Recortes lado a lado (SVG à esquerda, cena à direita,
  ampliados 2×, NEAREST) em `r02d-{satie,scarlatti}-p1-staff-side.png`.
OBSERVAÇÃO fora de escopo (para R05b/R06a): `verovio -t vsb -p 1` **ignora
o `-p`** — `tools/main.cpp` L552 chama `RenderToBridgeFile` sem intervalo
de páginas (só `vsb-json` honra `from/to`, L568-569); os `.vsb` acima têm
todas as páginas (Satie 2, Scarlatti 3) e o `--page 1` selecionou o índice
0 corretamente.
