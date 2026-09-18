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

(a preencher por quem executar)
