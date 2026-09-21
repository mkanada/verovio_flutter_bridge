# Destaque de notas — Gymnopedie, página 1

Gerado por `flutter test tool/generate_examples.dart` (em `score_bridge/`).

Notas (ids do timemap na página 1): `yw90mxt, orw55dt, q1t6l0ej, r1c5f34m, t1mebzmw, m15xbieh, o16b3pjn, qkcdn2b`.

Roteiro (relógio simulado do Flutter Tester):

- t = 0: `highlight(ids[0], attack: 200 ms, hold: 600 ms, release: 800 ms)`
- t = 100 ms: frame 1
- t = 100 ms: `highlight(ids[3], release: 2 s)`; t = 400 ms:
  `highlight(ids[5], azul, attack: 300 ms, hold: 1 s, release: 600 ms)`;
  t = 700 ms: `highlight(ids[7], release: 1,5 s)`
- 1-t0100 (t = 100 ms)
- 2-t0700 (t = 1000 ms)
- 3-t1100 (t = 1400 ms)
- 4-t1700 (t = 2000 ms)
- 5-t3200 (t = 3500 ms)

Cada frame é um recorte da região das notas; nenhuma nota "salta" — cada uma
tem a própria fase (attack, hold, release) ao mesmo tempo.
