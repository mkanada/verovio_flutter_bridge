# R05c — Prova widget-vs-harness (0 pixels)

**Depende de:** R05b · **Decisão necessária:** não

## Objetivo

Garantir que o que a comparação mede é **o mesmo caminho de código** que o
app vai mostrar. Sem essa prova, é possível passar meses otimizando um
renderizador paralelo que não é o de produção — e descobrir a divergência só
no aparelho.

## Ler antes (só isto)

- `compare/lib/main.dart`, comando `scene-to-png` (R02d/R05b).
- `score_bridge/lib/src/scene_painter.dart`.

## Contexto que você precisa (não vá procurar, está aqui)

- Hoje há **um** caminho (`ScenePainter.paint`) e dois chamadores: o comando
  de linha de comando e, em A01, o `CustomPaint` do widget. O teste deste
  passo trava os dois no mesmo resultado **antes** de A01 existir, usando um
  `CustomPaint` mínimo escrito no próprio teste.
- Em teste de widget, a captura vem de
  `tester.runAsync(() => boundary.toImage(pixelRatio: 1.0))` sobre um
  `RepaintBoundary`, e as fontes precisam ser carregadas explicitamente
  (helper de R04a) — senão o texto some do golden e o teste "passa" comparando
  duas páginas sem texto.
- A comparação é de **bytes crus RGBA** (`toByteData()`), não de PNG
  codificado: dois PNGs podem diferir em metadados sem diferir em pixel.
- O tamanho do canvas do widget tem que ser exatamente `widthPx × heightPx`
  da página, com `pixelRatio: 1.0`; qualquer diferença de tamanho vira
  reamostragem e o teste deixa de valer.

## O que fazer

1. Teste em `score_bridge/test/widget_vs_harness_test.dart`:
   - carrega uma página do fixture;
   - renderiza pelo caminho "harness" (`PictureRecorder` + `ScenePainter` +
     `Picture.toImage`);
   - renderiza pelo caminho "widget" (`CustomPaint` mínimo dentro de
     `RepaintBoundary`, tamanho fixo, `pixelRatio: 1.0`);
   - compara os dois `ByteData` RGBA — **diferença exata de 0 pixels**.
2. Marcar o teste como **permanente**: ele é critério de aceite de A01, A02 e
   A03 também. Deixe isso escrito no topo do arquivo de teste, não só no
   plano.
3. Se der diferença: não relaxe a tolerância. Investigue — as causas plausíveis
   são fundo (branco opaco vs. transparente), `pixelRatio`, tamanho do canvas
   e fontes não carregadas.

## Fora de escopo

- Qualquer comparação contra o SVG (é R05b/R06).
- A arquitetura de camadas (A01) — aqui o widget é o mínimo possível.

## Critérios de aceite

1. O teste existe, roda em `flutter test` e dá **0 pixels** de diferença.
2. O teste cobre uma página com texto e glifos (não uma página vazia) —
   registre nas notas qual página e quantos elementos ela tem.
3. O teste falha de propósito quando você muda uma constante de render no
   painter (verifique isso uma vez na mão e registre — um teste que nunca
   falha não prova nada).
4. O arquivo de teste diz, em comentário no topo, que ele é critério de
   aceite recorrente dos passos A01-A03.

## Notas de execução

(a preencher por quem executar)
