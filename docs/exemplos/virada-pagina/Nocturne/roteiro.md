# Virada de página por haste — Nocturne

Gerado por `flutter test tool/generate_examples.dart` (em `score_bridge/`).

Página 1 → 2; último compasso da página 1: `m1vrmzxb` (38511–41614 ms),
primeiro da página 2 começa em 41614 ms; `D = min(1 s, duração/4)` =
776 ms. Player com `release: 600 ms`, `ScoreView` com a haste azul
padrão (`barWidth` = 2 × noteheadBlack, teto 1 s).

Cada frame é `player.seek(t)` seguido de um quadro:

- 1-repouso: `seek(37711 ms)` — haste ausente, página 1
- 2-meio-da-entrada: `seek(38899 ms)` — haste edgeX = 6041, página 1
- 3-estacionada: `seek(40450 ms)` — haste edgeX = 12083, página 1
- 4-meio-da-conclusao: `seek(42002 ms)` — haste edgeX = 16517, página 1
- 5-repouso-seguinte: `seek(43190 ms)` — haste ausente, página 2

Nos frames 2–4 as notas do compasso tocando estão destacadas em vermelho, à
direita da haste; à esquerda dela aparece a página seguinte.
