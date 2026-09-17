# R03 — Glifos: `Path` por `glyphId`, cache e instâncias

**Depende de:** R02, S03 · **Decisão necessária:** não

## Objetivo

Desenhar os glifos SMuFL a partir do dicionário: cada `glyphId` vira um
`ui.Path` uma única vez, e cada ocorrência é esse mesmo path sob uma
transformação. É a maior parte da tinta de uma partitura.

## Ler antes (só isto)

- Especificação, seções 4, 4.1 e 5.3.
- Notas de execução de S03 (razão usos/glifos distintos por peça).
- `../verovio_lottie/verovio/src/lottiedevicecontext.cpp` `MakeGlyphShape` —
  a fórmula de `sx`/`sy` e o comentário sobre `fill`+`stroke` herdados.

## O que fazer

1. `GlyphCache`: `Map<String, ui.Path>` construído sob demanda a partir de
   `GlyphDef.paths` (mesma conversão v/i/o de R02), em **unidades de fonte**.
   O cache vive no `VsbDocument`, não no painter (várias páginas o compartilham).

2. Desenhar uma instância:

   ```dart
   canvas.save();
   canvas.translate(use.x, use.y);
   canvas.scale(use.sx, use.sy);
   canvas.drawPath(glyphPath, fillPaint);        // cor herdada
   canvas.drawPath(glyphPath, strokePaint);      // strokeWidth: 1.0 (unidade de fonte)
   canvas.restore();
   ```

   `strokeWidth: 1.0` em espaço de glifo equivale a `sy` em unidades de viewBox
   — que é exatamente o que o exportador do projeto anterior usava, reproduzindo
   a regra CSS `path {stroke:currentColor}` com largura 1 do SVG. **Não** omita
   o traço: sem ele os glifos saem visivelmente mais finos que no SVG.

3. `fill`/`stroke` explícitos na instância (quando houver) sobrepõem a herança.

4. Medir: quantos `ui.Path` distintos são criados por peça (deve bater com o nº
   de glifos distintos do dicionário, nunca com o nº de usos).

## Fora de escopo

- Caminho alternativo de render por TTF (o formato carrega os metadados, mas
  este passo implementa **só** o caminho de contorno — ver `CLAUDE.md`).
- Texto comum (R04).

## Critérios de aceite

1. `flutter test` verde, incluindo um teste que renderiza um único glifo
   conhecido (ex.: `Leipzig:E0A4`, cabeça de nota) e confere que o `Path.getBounds()`
   transformado bate com a `bbox` declarada no dicionário (tolerância: 1 unidade
   de viewBox).
2. O nº de `ui.Path` criados por peça == nº de entradas do dicionário usadas
   (teste com contador no cache; registre os números nas notas).
3. **Paridade visual parcial**: página 1 de Scarlatti e de Gymnopédie
   renderizadas e comparadas com o PNG do SVG (use o harness de R05 se já
   existir; senão, um teste golden local). Sem texto comum ainda, a divergência
   deve cair para a ordem de **poucos por cento** e toda concentrada em
   títulos/indicações de texto — se houver divergência **dentro** dos
   pentagramas, é bug de glifo: investigue antes de seguir.
4. Nenhum glifo aparece espelhado ou de cabeça para baixo (o `scale(1,-1)` do
   XML já vem aplicado pelo exportador — se algo estiver invertido, o bug é em
   S03, não aqui; registre e volte).

## Notas de execução

(a preencher por quem executar)
