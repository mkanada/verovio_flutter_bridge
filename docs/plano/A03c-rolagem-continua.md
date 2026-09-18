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

- Cada página visível mantém um `ScorePageView` com seu cache de `Picture`.
  Fora da janela, o cache tem que ser **descartado** (`dispose`), senão uma
  peça longa acumula memória nativa. Recomendação inicial: manter a visível
  ± 1; **meça** e documente o limite escolhido.
- `ScrollController` + `ListView.builder` com `itemExtent` calculado a partir
  de `heightPx` por página (as páginas podem ter alturas diferentes; use
  `itemExtentBuilder` ou um delegate que consulte a página).
- `scrollToId` precisa de: a **página** onde o id está e a **bbox** dele. O
  índice de S04 (`pages[].elements`) dá os dois, mas ele é por página — monte
  um mapa `id → (página, bbox)` **uma vez** ao carregar o documento (R01 já
  monta `byId` por página; agregue).
- A bbox está em unidades de viewBox **antes** do `translate(origin)`: para
  virar posição de tela é `(bbox + origin) * fit.scale + (fit.tx, fit.ty)` —
  a mesma conversão de A04a. Faça num lugar só, compartilhado pelos dois
  passos.
- No corpus, a peça mais longa tem 7 páginas. A peça grande de P01a (20+
  páginas) é o caso que realmente testa a virtualização — se ela já estiver
  disponível, use-a aqui também.

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

(a preencher por quem executar)
