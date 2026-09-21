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

Executado em 2026-09-21 (Flutter 3.47.4). `flutter analyze` limpo; `flutter test` 130/130.

**O que foi feito**

- `lib/src/page_layers.dart` (novo): `PageLayers` (segmentos de A01a + cache de
  `ui.Picture` dos estáticos, gravação preguiçosa ou `compileAll()`, `dispose()`
  idempotente) e `PictureStats` (contadores `builds`, `disposals`, `live`,
  `buildMicroseconds`, compartilhados entre as gerações de cache de um widget).
- `lib/src/score_page_view.dart` (novo): `ScorePageView` (`document`,
  `pageIndex`, `controller`, `animatableIds`, `backgroundColor`) e o `State`
  público `ScorePageViewState`, com `pictureBuilds`, `pictureDisposals`,
  `pictureStats` e `layers` (`@visibleForTesting`). `AspectRatio` →
  `RepaintBoundary` → `CustomPaint`, com `repaint:` ligado ao controller.
- `ScenePainter` ganhou `applyPageTransform`, `paintLeaf` e `paintSubtree`
  (públicos), e a constante `kPageInitialColor`; o percurso continua sendo o de
  `walkScene`.

**Decisões (documentadas no código)**

- **Os `Picture` são gravados em unidades de viewBox**, no espaço de conteúdo;
  `fit`/`origin` e a escala do widget são aplicados **uma vez** no `Canvas` de
  quem pinta. Redimensionar o widget não recompila nada (teste
  "redimensionar não recompila") e o `Picture` continua vetorial em qualquer
  escala. O widget tem a proporção da página (`widthPx : heightPx`) e escala
  pela largura recebida; a 1:1 nenhuma escala é aplicada.
- O cache só é invalidado por documento, página ou conjunto de ids dinâmicos —
  nunca por cor. A única exceção é a promoção de id (ver A01c).
- Estático: `save`/`transform`/`restore` só quando o item tem `rotate`
  herdado; dinâmico: `paintSubtree` com o `colorOverrides` do controller.
- Ids animáveis: `null` → `on`/`off` do timemap (`animatableIdsFromTimemap`,
  calculado a cada mudança estrutural, não por frame).
- **Nenhuma fusão de segmentos estáticos foi necessária**: compilar a página
  inteira custa ~1,9 ms (mediana; máx 4,0 ms) — ver A01c.

**Critérios**

1. `flutter analyze` sem avisos; `flutter test` 130/130.
2. **Byte-identidade (critério 1 do passo): as 34 páginas do corpus** —
   `test/score_page_view_test.dart` compara o RGBA cru do `ScorePageView` com o
   do harness de passada única (0 pixels de diferença em todas, incluindo as
   4 páginas com `rotate`). Comparação em bytes crus, mais estrita que `cmp`
   de PNG codificado. Lê `../compare/out/s08/*.vsb`; sem o diretório o grupo é
   pulado.
3. `setColor` em vários ids não incrementa `pictureBuilds`.
4. Trocar de página descarta os `Picture` da anterior (`pictureDisposals ==`
   builds da página 0), voltar a ela recompila, e remover o widget deixa
   `live == 0`.
5. `widget_vs_harness_test.dart` (R05c) continua em 0 pixels.

**Afeta os passos seguintes**

- Para A03, cada página é um `ScorePageView` com o próprio cache; o `State` é
  o que expõe as contagens para teste.
- Os testes de render usam `test/support/render_helpers.dart` (harness,
  captura por `RepaintBoundary`, contagem de pixels) e
  `test/support/colored_fixture.dart` (o corpus **não tem** `@color`: o fixture
  colorido é o Satie com `"color"` gravado em nós escolhidos).
