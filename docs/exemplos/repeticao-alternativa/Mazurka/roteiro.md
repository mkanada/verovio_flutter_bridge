# Páginas alternativas nos saltos de repetição — Mazurka

Gerado por `flutter test tool/generate_examples.dart` (em `score_bridge/`).
P04a-P04c (fase P): no único salto desta peça que cruza página (P01c), a
vista não volta para a página normal de destino — mostra uma página
**alternativa**, redesenhada a partir do compasso de chegada
(`Toolkit::Select`, P02c), atrás da haste (D-SALTO/E03a generalizados a
`PageRef` em P04a).

Compasso `d1e9361` (98500–100375 ms) → `d1e3853`
(sequência alternativa 0, página 0), salto em
100375 ms. `D = min(1 s, duração/4)` = 469 ms.
`ScorePlayer` com `release: 600 ms`.

- 1-repouso: `seek(97700 ms)` — displayedPage PageRef(1) — haste ausente
- 2-meio-da-entrada: `seek(98734 ms)` — displayedPage PageRef(1) — haste edgeX = 8343
- 3-estacionada: `seek(99672 ms)` — displayedPage PageRef(1) — haste edgeX = 16687
- 4-meio-da-conclusao: `seek(100609 ms)` — displayedPage PageRef(1) — haste edgeX = 18819
- 5-repouso-na-alternativa: `seek(101644 ms)` — displayedPage PageRef(0, sequence: 0) — haste ausente
- 6-nota-acesa: `seek(100894 ms)` — displayedPage PageRef(0, sequence: 0), nota `d1e3855` (passagem 2) acesa na alternativa
- antes-3-estacionada (`useAlternates: false`, comparação com E03b): `seek(99672 ms)` — displayedPage PageRef(1) (a página normal, não a alternativa)

O quadro "estacionada" mostra o compasso de chegada já visível à esquerda da
haste, no canto superior esquerdo da página alternativa — o 1º compasso
dela, por construção (P02c/P00). O quadro "antes" (`useAlternates: false`)
mostra a mesma haste revelando, em vez disso, a página normal de destino,
como antes desta fase.
