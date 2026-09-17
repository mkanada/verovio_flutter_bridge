# A04 — Overlay de widgets por bbox (cursor, toque, gestos)

**Depende de:** A01, S04 · **Decisão necessária:** não

## Objetivo

Entregar a parte de "gerar widgets nas posições necessárias": permitir que o
app coloque **widgets Flutter de verdade** sobre elementos da partitura
(cursor, alvo de toque, tooltip, indicador de erro do aluno), posicionados pela
bbox exportada, sem que isso custe um widget por path.

## Ler antes (só isto)

- S04 (`bbox` e índice por id) e o que o parser expõe (R01).
- `score_bridge/lib/src/score_page_view.dart` (A01) — a transformação de página
  é a mesma que converte bbox → coordenadas do widget.

## O que fazer

1. Conversão de coordenadas, num único lugar, testada:

   ```dart
   Rect rectForId(String id);        // bbox em coordenadas do widget (px lógicos)
   String? idAt(Offset localPosition, {Set<String>? classes});   // hit-test
   ```

   `idAt` usa o índice + bbox (não geometria exata). Quando várias bboxes se
   sobrepõem, devolve a de **menor área** (a mais específica) — documente isso.

2. `overlayBuilder` no `ScorePageView`:

   ```dart
   Widget? Function(BuildContext, String id, Rect rect) overlayBuilder;
   Iterable<String> overlayIds;   // só estes viram widget
   ```

   Materializa `Positioned` **só** para os ids pedidos. O padrão é lista vazia:
   nenhum widget extra, custo zero.

3. Gestos: `onElementTap(String id)` no `ScoreView`, implementado com
   `GestureDetector` + `idAt` (um detector para a página inteira, não um por
   nota).

4. Um cursor de exemplo pronto para uso (`ScoreCursor`), que recebe um id e
   desenha um retângulo/barra sobre a bbox — serve de exemplo e de teste.

## Fora de escopo

- Hit-test por geometria exata (só se um caso real pedir).
- Semântica de acessibilidade da partitura (passo próprio, se for pedido).

## Critérios de aceite

1. Teste: para 20 ids sorteados de 3 peças, `rectForId` em coordenadas do
   widget, convertido de volta para unidades de viewBox, reproduz a bbox
   exportada (tolerância `1e-6`).
2. Teste de widget: um `overlayBuilder` que desenha uma borda vermelha sobre 5
   notas; o golden mostra as bordas **exatamente** em volta das cabeças de nota
   (compare com o render sem overlay + retângulos desenhados no painter: as
   duas imagens devem coincidir na posição das bordas).
3. `idAt` devolve o id correto ao tocar no centro da bbox de 20 elementos
   testados, e `null` numa área vazia da página.
4. Com `overlayIds` vazio, a árvore de widgets tem o **mesmo** número de
   elementos que antes deste passo (prova de custo zero quando não se usa).
5. Overlay continua alinhado depois de mudar o tamanho do widget (teste com
   duas larguras diferentes) e durante a virada de página de A03.

## Notas de execução

(a preencher por quem executar)
