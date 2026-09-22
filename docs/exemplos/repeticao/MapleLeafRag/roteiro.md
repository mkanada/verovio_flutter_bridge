# Haste nos saltos de repetição — MapleLeafRag

Gerado por `flutter test tool/generate_examples.dart` (em `score_bridge/`).
D-SALTO (decisão do usuário em 2026-09-22): haste generalizada — a mesma
regra de A05b/E03a, com a página de destino do salto atrás da haste, em
vez de sempre a seguinte.

`test/fixtures/maple-leaf-rag.vsb` (`-x 42`), `ScorePlayer` com
`release: 600 ms`.

### salto1: compasso `kkxu5s6` (página 2) → `qqplm6a` (página 1), salto em 39900 ms

`D = min(1 s, duração/4)` = 300 ms.

- 1-repouso: `seek(37900 ms)` — haste ausente, página corrente 2
- 2-meio-da-entrada: `seek(38850 ms)` — haste edgeX = 6455, destino página 1, página corrente 2
- 3-estacionada: `seek(39450 ms)` — haste edgeX = 12911, destino página 1, página corrente 2
- 4-meio-da-conclusao: `seek(40050 ms)` — haste edgeX = 16931, destino página 1, página corrente 2
- 5-repouso-seguinte: `seek(41000 ms)` — haste ausente, página corrente 1

### salto2: compasso `dv3un7a` (página 3) → `y12vaz72` (página 2), salto em 97500 ms

`D = min(1 s, duração/4)` = 300 ms.

- 1-repouso: `seek(94900 ms)` — haste ausente, página corrente 2
- 2-meio-da-entrada: `seek(96450 ms)` — haste edgeX = 18972, destino página 3, página corrente 2
- 3-estacionada: `seek(97050 ms)` — haste edgeX = 4847, destino página 2, página corrente 3
- 4-meio-da-conclusao: `seek(97650 ms)` — haste edgeX = 13222, destino página 2, página corrente 3
- 5-repouso-seguinte: `seek(98600 ms)` — haste ausente, página corrente 2

O quadro "estacionada" de cada salto mostra o compasso de destino já visível
à esquerda da haste, antes de a música chegar lá.
