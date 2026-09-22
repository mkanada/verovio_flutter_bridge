# P03b — Dart: `ScorePageView` e `ScoreView` exibem um `PageRef`

**Depende de:** P03a, P02d (o harness `scene-to-png --alternate` do
critério 2) · **Decisão necessária:** não (D-ALT-INDICE já decide a indexação)

## Objetivo

A vista passa a conseguir **mostrar** uma página alternativa, parada ou atrás
da haste, quando alguém (o player, em P04b) pedir. A navegação do usuário
continua 100% em páginas normais (D-ALT-INDICE).

## Ler antes (só isto)

- `docs/plano/P00-visao-geral-paginas-alternativas.md`.
- `score_bridge/lib/src/score_page_view.dart` (inteiro, é pequeno: `_page`
  L101, overlays L233-L270).
- `score_bridge/lib/src/score_view.dart`: `SweepCurtain` (L60-L92),
  `ScoreViewController` (L151-L216), `ScoreViewState` (`_keyOf` L336,
  `_setCurrent` L425, `goToPage` L448, `_targetOf` L508, `_isValidCurtain`
  L513, `_onCurtainChanged` L538, `_page` L745, `_fit` L763, `_centered`
  L773, `_box` L796, `_buildSweep` L804, `_buildSlide` L843).
- `score_bridge/lib/src/score_cursor.dart` (onde usa geometria/página).
- E03a, "Notas de execução" (como o cache de páginas se comporta: uma
  `GlobalKey` por página mantém a página viva enquanto ela está na árvore).

## Contexto que você precisa (não vá procurar, está aqui)

- A haste já aceita destino arbitrário (`targetPageIndex`, E03a). O que falta
  é poder dizer **de qual sequência** são a página da frente e a de trás.
- A cor e o destaque (`ScoreController`) são por **id**. A página alternativa
  tem os mesmos ids, então acende sozinha, sem código novo.
- Overlays e hit-test (`ScorePageView`) consultam `widget.document.geometry`
  e comparam `ref.page != widget.pageIndex`. Numa alternativa, isso tem que
  usar `document.geometryOf(sequence)`.
- **Modo `continuousScroll` não usa alternativas.** É uma faixa única de
  páginas normais, e o player ali acompanha por `scrollToId`. Não mude esse
  modo.

## O que fazer

1. `ScorePageView`: parâmetro novo `int? sequence` (padrão `null`). `_page`
   = `document.pageAt(PageRef(pageIndex, sequence: sequence))`; geometria de
   overlay e hit-test = `document.geometryOf(sequence)`. Inclua `sequence` na
   comparação de `didUpdateWidget`.
2. `SweepCurtain`: campos novos `int? sequence` (da página da frente) e `int?
   targetSequence` (da de trás), em `==`/`hashCode`/`toString`. Getters
   `PageRef get page` e `PageRef get target` (com o `?? pageIndex + 1` de
   hoje dentro da **mesma** sequência da frente, quando não houver alvo).
3. `ScoreViewState`:
   - estado novo `PageRef? _shown` (página exibida quando **não** é a
     normal `_current`); `PageRef get displayedPage => _shown ??
     PageRef(_current)`;
   - `_keyOf(PageRef)`, `_fit(PageRef, ...)`, `_centered(PageRef, ...)`,
     `_page(PageRef)`;
   - `showPage(PageRef ref)` (API para o player): com `ref` normal, é o
     `goToPage` de hoje (sem animação) e limpa `_shown`. Com `ref`
     alternativo, `_shown = ref` e `_current` = página normal do **primeiro
     compasso** de `ref` (D-ALT-INDICE: o usuário continua vendo "página X"
     com sentido). `onPageChanged` só dispara quando `_current` muda;
   - `goToPage`/`nextPage`/`previousPage` (usuário): limpam `_shown` e
     navegam como hoje, em páginas normais;
   - `_isValidCurtain`/`_targetOf`/`_onCurtainChanged`/`_buildSweep`: usam
     `curtain.page`/`curtain.target`. A conclusão faz `showPage(target)`;
   - `_buildSlide`: `_slideTo` vira `PageRef`, para o player poder deslizar
     até uma alternativa.
4. `ScoreViewController`: expõe `showPage(PageRef)` e `displayedPage`.
   Documente no doc-comment que `showPage` é do player, e que
   `currentPage`/`goToPage` são sempre da indexação normal.
5. `ScoreCursor` e qualquer outro consumidor de `geometry` ligado a uma
   página exibida: use a geometria da sequência exibida.

## Fora de escopo

- Quando exibir uma alternativa (P04a/P04b).
- `continuousScroll`.

## Critérios de aceite

1. Teste de widget: `showPage(PageRef(0, sequence: 0))` na Maple Leaf Rag
   mostra a página cujo primeiro compasso é `alternates[0].start`
   (verificação estrutural: o `ScorePageView` montado tem `sequence == 0`,
   `pageIndex == 0`), e `currentPage` = página normal desse compasso.
2. **Paridade de widget:** a página alternativa desenhada pelo `ScoreView`
   é idêntica, pixel a pixel, à do harness `scene-to-png --alternate`
   (mesma prova de R05c, 0 pixels de diferença).
3. `SweepCurtain(pageIndex: A, edgeX: x, targetPageIndex: 0,
   targetSequence: k)`: a página de trás é a alternativa. Na conclusão,
   `displayedPage == PageRef(0, sequence: k)`.
4. Com uma alternativa exibida, `goToPage(n)` volta às páginas normais e
   `displayedPage == PageRef(n)`.
5. Destaque: `controller.highlight(<id de nota do trecho>)` com a
   alternativa exibida acende a nota **na alternativa** (sonda de cor na bbox
   de `geometryOf(k)`).
6. Sem `sequence` em lugar nenhum, os testes e goldens de A03/A04/E03 ficam
   **byte-idênticos**. `PictureStats.live` volta ao patamar depois de
   alternar normal → alternativa → normal (sem vazamento).
7. `flutter analyze` limpo, `flutter test` verde.

## Notas de execução

_(preencher)_
