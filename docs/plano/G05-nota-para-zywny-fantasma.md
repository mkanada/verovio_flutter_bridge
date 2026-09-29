# G05 — Nota para o `zywny`: ler `pitchpos.json` e desenhar a nota fantasma

**Depende de:** G04d · **Decisão necessária:** não

> O `score_bridge` mora no `zywny` desde o commit `276bdf6`. Este passo,
> **neste repositório**, só escreve `docs/nota-para-zywny-fantasma.md` (no
> molde de `nota-para-zywny-fase-p.md`) e copia os vetores; a execução é
> no plano do host.

## Objetivo

Entregar ao `zywny` tudo o que ele precisa para implementar o lado Dart sem
reabrir decisões: o que mudou no `.vsb`, a API sugerida, a pintura, os
vetores de teste e o que conferir no que já existe.

## Ler antes (só isto)

- [`G03`](G03-visao-geral-nota-fantasma.md) inteiro.
- `docs/nota-para-zywny-fase-p.md` (molde).
- `docs/formato/especificacao-v1.md` §2.4 (`restsOn`/`restsOff`), §2.8,
  §5.1, §10.

## O que a nota deve cobrir

1. **O que mudou no `.vsb`** (tudo aditivo, `version` 1): `pitchpos.json`;
   `lines`/`ledger`/`gs` no nó `staff`; `staff` em nós cross-staff; glifos
   reservados; `restsOn`/`restsOff` no timemap. Regenerar fixtures.
2. **Conferir no que existe**: o parser do timemap e o `ScoreTimeline`/
   `ScorePlayer` com as chaves de pausa (D-FANT-PAUSA-TEMPO) —
   testes existentes verdes com as fixtures novas.
3. **Modelo/parser** (sugestão, no molde de `VsbMidi` de G02):
   `VsbPitchPos` (mapa id notado → contexto), `StaffGeometry` no nó
   `staff`, `VsbDocument.pitchPos` (null sem o arquivo).
4. **Cálculo**: `List<GhostNote> ghostsFor({required List<String>
   expectedIds, required List<int> wrongKeys, PageRef page})` — porta da
   §10, validada contra `docs/formato/fantasma/vetores.json` (os mesmos
   números da referência Python, tolerância 0,5 unidade de viewBox).
   `GhostNote`: pauta, `loc`, posição da cabeça, acidente (glifo + posição),
   linhas suplementares, marcador de oitava.
5. **Pintura**: uma camada de overlay `CustomPaint` por cima das notas,
   no molde da camada dinâmica (A01b) — nunca widget por forma; glifos pelo
   `GlyphCache` existente, com a cor da fantasma definida pelo host;
   repinta só quando o conjunto de teclas erradas muda.
6. **Ciclo de vida** (D-FANT-DURACAO): note-on de tecla errada → fantasma
   aparece; note-off → fade curto e some. Tempo de fade e tempo mínimo na
   tela são parâmetros do host (sugestão inicial: fade de 150 ms, mínimo
   de 250 ms, a ajustar no uso).
7. **Qual evento é o "esperado"** num instante (inclusive durante pausa,
   D-FANT-PAUSA) é decisão da avaliação do aluno no host (`N03`,
   `PerformanceTrack`), não do formato: o `ghostsFor` recebe os ids.
8. Limitações aceitas da v1 (G03).

## Critérios de aceite

1. `docs/nota-para-zywny-fantasma.md` escrito, cobrindo os 8 itens.
2. Linha da fase no `README.md` do plano atualizada; o usuário avisado de
   que o trabalho segue no `zywny`.

## Notas de execução

_(vazio)_
