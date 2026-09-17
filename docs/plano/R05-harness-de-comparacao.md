# R05 — Harness cena→PNG + diff no `compare/`

**Depende de:** R02, F02 · **Decisão necessária:** SIM (backend gráfico)

## Objetivo

Fechar o ciclo de validação: um comando que pega um `.vsb` (ou o JSON) e
escreve o PNG de uma página, no mesmo tamanho do PNG do SVG, para o `diff`
existente comparar. Sem isso, nenhum passo R/A tem número.

## Decisão necessária

**Qual backend gráfico** o `compare` usa para render — Impeller (padrão atual
do Flutter no Linux) ou Skia (`--no-enable-impeller` / `FLUTTER_ENABLE_IMPELLER=0`).
Meça os dois (critério 3) e leve os dois números ao usuário antes de fixar. O
escolhido passa a ser o backend oficial da comparação e tem que ser registrado
no `compare/README.md` — números medidos com backends diferentes não são
comparáveis entre si.

## Ler antes (só isto)

- `../verovio_lottie/compare/README.md`, seções "Execução: modo batch sob
  xvfb" e "Arquitetura: FFI direto" (a primeira vale; a segunda é o que **não**
  precisamos mais).
- `../verovio_lottie/compare/lib/src/diff.dart` (já copiado em F02).
- `score_bridge/lib/src/scene_painter.dart` (R02).

## O que fazer

1. Adicionar ao app `compare` a dependência de caminho `score_bridge` e o
   comando:

   ```
   compare scene-to-png <arquivo.vsb|json> <saida.png> --page N [--width W --height H]
   ```

   Implementação: `PictureRecorder` + `Canvas` → `ScenePainter.paint` →
   `Picture.toImage(W, H)` → `toByteData(format: png)`. Fundo **branco opaco**
   (o `svg_render` também compõe sobre branco — ver F02).
   Se `--width/--height` forem omitidos, use `widthPx`/`heightPx` da página.

2. Rodar sob `xvfb-run -a` quando não houver `DISPLAY` (o padrão dos scripts).

3. Reescrever `compare/scripts/compare-page.sh` para o fluxo novo:
   `verovio -t svg` → `svg_render` → PNG de referência; `verovio -t vsb` →
   `compare scene-to-png` → PNG da cena; `compare diff` → imagem + estatística.
   Mantenha a leitura de dimensões do PNG do SVG (o trecho em Python já existe)
   e a lista de fontes.

4. **Prova de que o harness mede o que o app vai mostrar**: acrescente um
   teste de widget (`score_bridge/test/`) que renderiza a mesma página pelo
   caminho do widget (A01 ainda não existe: use um `CustomPaint` mínimo
   inline) e compara com o PNG do harness — **diferença exata de 0 pixels**.
   Esse teste é a garantia de que a comparação não valida um caminho paralelo
   ao de produção; mantenha-o vivo em todos os passos seguintes.

## Fora de escopo

- Varredura do corpus e relatório (R06).
- Qualquer ajuste de render para "melhorar a %" — se a % estiver ruim, o
  conserto é no passo da primitiva correspondente, não no harness.

## Critérios de aceite

1. `cd compare && flutter build linux --release` compila com o comando novo.
2. `compare scene-to-png` gera PNG com as dimensões exatas do PNG do SVG para
   5 páginas de peças diferentes.
3. **Comparação de backends**: a mesma página renderizada com Impeller e com
   Skia, cada uma diffada contra o PNG do SVG (tolerância 32). Registre as duas
   percentagens e o tempo de execução nas notas, e leve ao usuário.
4. O teste widget-vs-harness dá **0 pixels** de diferença.
5. `compare-page.sh <peça> 1` roda de ponta a ponta e escreve
   `compare/out/<peça>-p1-{svg,scene,diff}.png` mais a estatística no stdout.
6. Determinismo: rodar `scene-to-png` duas vezes na mesma entrada produz PNGs
   byte-idênticos (`cmp`).

## Notas de execução

(a preencher por quem executar)
