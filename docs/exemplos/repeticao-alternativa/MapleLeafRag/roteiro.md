# Páginas alternativas nos saltos de repetição — MapleLeafRag

Gerado por `flutter test tool/generate_examples.dart` (em `score_bridge/`).
P04a-P04c (fase P): no único salto desta peça que cruza página (P01c), a
vista não volta para a página normal de destino — mostra uma página
**alternativa**, redesenhada a partir do compasso de chegada
(`Toolkit::Select`, P02c), atrás da haste (D-SALTO/E03a generalizados a
`PageRef` em P04a).

Compasso `z1m4pqeg` (152700–153900 ms) → `jn8k16x`
(sequência alternativa 6, página 0), salto em
153900 ms. `D = min(1 s, duração/4)` = 300 ms.
`ScorePlayer` com `release: 600 ms`.

- 1-repouso: `seek(151900 ms)` — displayedPage PageRef(2) — haste ausente
- 2-meio-da-entrada: `seek(152850 ms)` — displayedPage PageRef(2) — haste edgeX = 8865
- 3-estacionada: `seek(153450 ms)` — displayedPage PageRef(2) — haste edgeX = 17730
- 4-meio-da-conclusao: `seek(154050 ms)` — displayedPage PageRef(2) — haste edgeX = 19341
- 5-repouso-na-alternativa: `seek(155000 ms)` — displayedPage PageRef(0, sequence: 6) — haste ausente
- 6-nota-acesa: `seek(154250 ms)` — displayedPage PageRef(0, sequence: 6), nota `z1o15b0g` (passagem 2) acesa na alternativa
- antes-3-estacionada (`useAlternates: false`, comparação com E03b): `seek(153450 ms)` — displayedPage PageRef(2) (a página normal, não a alternativa)

O quadro "estacionada" mostra o compasso de chegada já visível à esquerda da
haste, no canto superior esquerdo da página alternativa — o 1º compasso
dela, por construção (P02c/P00). O quadro "antes" (`useAlternates: false`)
mostra a mesma haste revelando, em vez disso, a página normal de destino,
como antes desta fase.
