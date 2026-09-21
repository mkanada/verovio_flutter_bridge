# A03c — `continuousScroll`, `scrollToId` e cache de páginas

**Depende de:** A03b · **Decisão necessária:** não

## Objetivo

O segundo modo de leitura: páginas empilhadas verticalmente, roladas sem
virada, com virtualização — e a navegação por elemento (`scrollToId`), que é
o que o host usa para "levar a tela até esta nota".

## Ler antes (só isto)

- `score_bridge/lib/src/score_view.dart` (A03a/A03b).
- [Especificação](../formato/especificacao-v1.md), seção **5.5** (índice de
  elementos e bbox).
- Notas de execução de [S08](S08-corrigir-bbox-de-glifo.md) — a bbox usada
  aqui só é confiável depois daquela correção.

## Contexto que você precisa (não vá procurar, está aqui)

- **Não há virada por haste aqui.** No modo contínuo não existe página atual
  nem página de trás: `SweepCurtain` (A03b) é ignorado e a rolagem acompanha a
  posição (A05b). Nos modos paginados, `scrollToId` navega com `goToPage`, que
  cancela qualquer virada em curso.
- Cada página visível mantém um `ScorePageView` com seu cache de `Picture`.
  Fora da janela, o cache tem que ser **descartado** (`dispose`), senão uma
  peça longa acumula memória nativa. Recomendação inicial: manter a visível
  ± 1; **meça** e documente o limite escolhido.
- `ScrollController` + `ListView.builder` com `itemExtent` calculado a partir
  de `heightPx` por página (as páginas podem ter alturas diferentes; use
  `itemExtentBuilder` ou um delegate que consulte a página).
- `scrollToId` precisa de: a **página** onde o id está e a **bbox** dele. O
  índice de §5.5 (`ScenePage.elements`, derivado no parse desde 2026-09-20 —
  não vem mais do arquivo) dá os dois, mas ele é por página — monte um mapa
  `id → (página, bbox)` **uma vez** ao carregar o documento (R01 já monta
  `byId` por página; agregue).
- A bbox está em unidades de viewBox **antes** do `translate(origin)`: para
  virar posição de tela é `(bbox + origin) * fit.scale + (fit.tx, fit.ty)` —
  a mesma conversão de A04a. Faça num lugar só, compartilhado pelos dois
  passos.
- No corpus, a peça mais longa tem 7 páginas. Uma peça grande (20+
  páginas), fora do corpus, é o caso que realmente testa a virtualização —
  se houver uma disponível (por exemplo, do `zywny`), use-a aqui também.

## O que fazer

1. Modo `continuousScroll` no `ScoreView`, com virtualização e limite
   documentado de páginas com `Picture` vivo.
2. `scrollToId(String id, {double alignment = 0.5, Duration duration})`:
   - modo paginado → navega para a página do elemento;
   - modo contínuo → rola até deixar a bbox visível, com o alinhamento pedido.
3. Contador de `Picture` vivos exposto para teste.
4. Comportamento para id inexistente: **não lança**, devolve `false`
   (documente) — os ids de repetição do timemap (`-rend2`) chegam aqui.

## Fora de escopo

- Overlays e hit-test (A04).
- Zoom/pan.

## Critérios de aceite

1. Repouso de cada página no modo contínuo é **pixel-idêntico** ao render
   estático da página (0 pixels), nas 34 páginas.
2. Rolar do início ao fim de uma peça de 7 páginas mantém no máximo o número
   documentado de `Picture` vivos (contador no teste) e volta ao início sem
   vazamento.
3. `scrollToId` com um id da **última** página de uma peça de 7 páginas deixa
   a bbox daquele elemento visível, nos dois modos.
4. `scrollToId` com id inexistente devolve `false` e não altera a posição.
5. Números nas notas: limite de cache escolhido, memória observada antes e
   depois da rolagem completa, e o tempo de `scrollToId`.
6. `flutter analyze` limpo, `flutter test` verde; widget-vs-harness em 0
   pixels.

## Notas de execução

Concluído em 2026-09-21 (`score_view.dart`, `test/score_view_test.dart`).

- `ListView.builder` com `itemExtentBuilder` (altura = largura × `heightPx /
  widthPx` de cada página), `padding: EdgeInsets.zero` (senão o
  `MediaQuery` desloca) e `scrollCacheExtent` de **uma altura de página**:
  ficam vivas as páginas que cruzam a viewport ± 1 — **limite documentado: 3
  páginas com viewport de uma página**.
- **Repouso (critério 1)**: 34 páginas → **0 pixels** (janela do tamanho da
  primeira página; `goToPage(i)` rola até a página).
- **Rolagem completa (critério 2)** no Nocturne (7 páginas, ida e volta):
  pico de **278** `Picture` vivos = exatamente as 3 páginas mais pesadas
  (limite calculado por `segmentPage` = 278); `builds = 769`, `disposals =
  662` durante o percurso; **ao desmontar, `live = 0`** (sem vazamento).
  **Memória nativa (RSS) não foi medida** — só os contadores de `Picture`;
  a medição em dispositivo fica para o `zywny`.
- **`scrollToId(id, {alignment = 0.5, duration = 0})`** devolve `bool`:
  `false` (sem lançar, sem mexer) para id inexistente (`-rend2`) ou vista ainda
  não montada. Contínuo: rola até a bbox ficar visível com o alinhamento
  (`topo da bbox + a·altura − a·viewport`, saturado ao intervalo); paginado:
  `goToPage`. Testado com uma nota da **última** página do Nocturne nos dois
  modos: bbox dentro da viewport de meia página. **Tempo**: 437 µs
  (paginado) e 339 µs (contínuo), sem animação.
- No contínuo a "página corrente" é a que contém o **centro** da viewport
  (`currentPage`/`onPageChanged` acompanham a rolagem); saltos programáticos
  não disparam o listener duas vezes.
- `SweepCurtain` é ignorado fora de `pagedSweep`.
