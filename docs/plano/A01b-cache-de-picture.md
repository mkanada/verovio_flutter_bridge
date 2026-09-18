# A01b — `ScorePageView`: camadas e cache de `ui.Picture`

**Depende de:** A01a · **Decisão necessária:** não

## Objetivo

Transformar os segmentos num widget de produção: cada trecho estático
compilado **uma vez** em `ui.Picture` e reusado, trechos dinâmicos pintados ao
vivo. O critério que manda neste passo é um só: **não pode mudar um pixel**.

## Ler antes (só isto)

- `score_bridge/lib/src/segmentation.dart` (A01a).
- `score_bridge/test/widget_vs_harness_test.dart` (R05c) — continua valendo.
- Risco 3 do [README do plano](README.md).

## Contexto que você precisa (não vá procurar, está aqui)

- Números de A01a: mediana de **196 segmentos** por página (máximo 545), ou
  seja, ~98 `Picture` estáticos por página na mediana e ~273 no pior caso.
  São muitos objetos pequenos: meça o tempo de compilação antes de decidir
  qualquer coisa a mais.
- `ui.Picture` guarda comandos, não pixels: `drawPicture` é barato, mas cada
  `PictureRecorder` tem custo de criação. Se a compilação da página ficar
  cara, a alternativa a medir (e **só** com número na mão) é fundir segmentos
  estáticos adjacentes que não têm interseção de bbox com nenhum nó dinâmico
  entre eles — o que reduz segmentos sem alterar o resultado visível.
- **`ui.Picture` precisa de `dispose()`**: um cache que troca de página sem
  descartar os `Picture` antigos vaza memória nativa que o GC do Dart não
  cobra. Descarte no `dispose()` do estado e ao invalidar o cache.
- A transformação de página (`fit` + `origin`) pode ser aplicada **uma vez**
  no `Canvas` do widget, com os `Picture` gravados em coordenadas de viewBox
  — isso torna o cache independente do tamanho do widget. Se você gravar os
  `Picture` já em pixels, qualquer redimensionamento invalida tudo. Escolha e
  **documente** no código.
- `RepaintBoundary` em volta do `CustomPaint`, e `repaint:` do `CustomPainter`
  ligado a um `Listenable` — assim a mudança de cor repinta sem reconstruir
  widget nem refazer layout.

## O que fazer

1. `score_bridge/lib/src/score_page_view.dart`:

   ```dart
   class ScorePageView extends StatefulWidget {
     const ScorePageView({
       required this.document,
       required this.pageIndex,
       this.controller,                 // A01c
       this.animatableIds,              // null => ids do timemap
     });
   }
   ```

2. Cache de `Picture` invalidado **somente** quando muda documento, página ou
   (se você gravou em pixels) tamanho do canvas. Nunca quando muda cor.

3. Instrumentação permanente (não só de teste): um contador de compilações de
   `Picture` exposto para teste (`@visibleForTesting int get pictureBuilds`).
   É o que prova o critério 2 aqui e em A02.

4. Pintura: percorra os segmentos em ordem, `drawPicture` nos estáticos e
   pintura direta nos dinâmicos, reusando o `ScenePainter` de R02.

## Fora de escopo

- `ScoreController` e cor por id (A01c).
- Animação (A02), navegação (A03), overlays (A04).

## Critérios de aceite

1. **A segmentação não muda um pixel**: para as **34 páginas** do corpus, o
   PNG renderizado pelo `ScorePageView` (sem nenhuma cor sobrescrita) é
   **byte-idêntico** ao PNG de passada única do harness de R05
   (`cmp` nos arquivos). Este é o critério mais importante do passo.
2. Trocar a cor de uma nota (mesmo sem o controller ainda: force pelo
   `colorOverrides`) **não** incrementa `pictureBuilds`.
3. Mudar de página descarta os `Picture` da página anterior (teste com
   contador de `dispose`, ou verifique que `pictureBuilds` volta a crescer ao
   voltar para ela).
4. O teste widget-vs-harness de R05c continua em **0 pixels**.
5. `flutter analyze` limpo, `flutter test` verde.

## Notas de execução

(a preencher por quem executar)
