# G04b — C++: geometria da pauta na cena e glifos reservados

**Depende de:** G04a · **Decisão necessária:** não

## Objetivo

Fazer o `BridgeDeviceContext` gravar, nos nós da cena, o que a §5.1 nova
pede (G04a): `lines`/`ledger`/`gs` no nó `staff` e `staff` nos nós
cross-staff; e fazer o `BridgeWriter` incluir sempre os glifos reservados
(§4) no dicionário. **Nenhum pixel muda.**

## Ler antes (só isto)

- [`G03`](G03-visao-geral-nota-fantasma.md) § Regras e § Invariantes.
- `docs/formato/especificacao-v1.md` §4, §5.1 (como ficaram em G04a).
- `verovio/include/vrv/bridgegeometry.h`: `BridgeNode` (~L108).
- `verovio/src/bridgedevicecontext.cpp`: `StartGraphic` (~L1140),
  `MakeGlyphUse` (dicionário de glifos).
- `verovio/src/bridgewriter.cpp`: serialização do nó (procure `hasBBox`,
  ~L466) e do dicionário de glifos.
- `verovio/include/vrv/staff.h`: `m_drawingLines` (L326),
  `m_drawingStaffSize` (L336), `GetDrawingY` (L200);
  `Staff::CalcPitchPosYRel` (`staff.cpp` L287).
- Espessura/extensão das linhas suplementares como o `View` calcula:
  `view_element.cpp` L1694 (`m_ledgerLineThickness × GetDrawingUnit`),
  `Doc::GetDrawingLedgerLineExtension` (`doc.cpp` L2118).

## Contexto que você precisa

- `StartGraphic(Object *object, …)` recebe o `Object` — é daí que sai o
  `Staff` (e o `LayerElement` cross-staff, via `HasCrossStaff`/
  `GetCrossStaff`). O DC pode **ler** o objeto; a regra do projeto é não
  alterar `View`, `SvgDeviceContext` nem `BBoxDeviceContext`.
- O referencial dos números: y da cena é o do `DeviceContext` (unidades de
  viewBox, eixo y para baixo), **antes** do `translate(origin)` (§3/§5.1).
  Confira que `topY` bate com o y do primeiro filho `p` do nó `staff` (no
  Satie, 808 com `unit` 90).
- Páginas alternativas (P02c) passam pelo mesmo DC: ganham os campos sem
  código a mais. Confira mesmo assim.
- Glifos reservados: use a fonte da peça (a mesma que prefixa os ids, ex.
  `Leipzig:E0A4`) e o mesmo caminho de dicionário de `MakeGlyphUse`, para o
  contorno sair idêntico a um glifo usado.

## O que fazer

1. `BridgeNode`: campos opcionais para `lines`, `ledger` (e `ledgerCue`,
   se diferente), `gs` e `staffRef`.
2. `StartGraphic`: para `STAFF`, calcular e gravar; para nota/acorde/pausa
   com `HasCrossStaff()`, gravar o id do `Staff` de desenho.
3. `BridgeWriter`: emitir os campos só quando presentes (ordem canônica
   §7) e acrescentar os glifos reservados ao dicionário.
4. Regenerar os `.vsb` do corpus em `compare/out/g04b/` (mesmas flags de
   P01c) e rodar a varredura de paridade.

## Fora de escopo

- `pitchpos.json` e `includeRests` (G04c). Lado Dart (`zywny`).

## Critérios de aceite

1. **Paridade inalterada**: `compare-corpus.sh` (normais e
   `SWEEP_ALTERNATES=1`) com os mesmos percentuais de P05, página a página.
2. Todo nó `staff` de todas as páginas (normais e alternativas) do corpus
   tem `lines`, e `topY + k × 2 × unit` bate com o y dos `n` primeiros
   filhos `p` (tolerância 0,5) — script descartável, resultado registrado.
3. Toda cabeça de nota (`u` dentro de `notehead`) do corpus satisfaz
   `y = topY + (2×(n−1) − loc) × unit` para um `loc` inteiro, na pauta de
   desenho (ancestral, ou `staff` quando cross-staff) — conte e registre
   as exceções (esperado: 0).
4. Os 8 glifos reservados estão em todo `glyphs.json` do corpus.
5. Tamanho: `scene.json` e `glyphs.json` antes/depois por peça, registrados.

## Notas de execução

Concluído em 2026-09-29. `BridgeNode` ganhou `hasLines/lines`, `hasLedger/ledger`,
`hasLedgerCue/ledgerCue`, `hasGlyphScale/glyphScale` e `staffRef`;
`BridgeDeviceContext::AnnotateNodeGeometry` (chamado do fim de `EndGraphic`,
que já recebe o `View`; só **lê** o `Object`) grava a geometria e
`BridgeDeviceContext::AddReservedGlyphs` (chamado de
`Toolkit::RenderPagesToBridge`) põe os 8 glifos no dicionário pelo mesmo caminho
de `MakeGlyphUse`. Os números são as mesmas expressões de `View::DrawLedgerLines`/
`Doc::GetDrawingLedgerLineExtension`, com a mesma truncagem para inteiro
(`ledger` [22, 48] e `ledgerCue` [16, 36] com `unit` 90; tamanho de
fonte por `Doc::GetDrawingStaffSize`, sem mutar `m_drawingSmuflFont`). `View`,
`SvgDeviceContext` e `BBoxDeviceContext` intactos.

Critérios (script descartável `compare/scripts/g04b-check.py`, com
`compare/scripts/g04-gen.sh` para gerar antes/depois com `--xml-id-seed 42` —
sem semente os ids mudam a cada execução e nada compara):

1. **Paridade inalterada — provada sem o `compare-corpus.sh`**: o ambiente
   deste passo não tem Flutter, então a varredura de PNG não rodou. No lugar,
   `scene.json` e `alternates.json` de 23 peças (10 do corpus + 13 de
   repetições, normais e alternativas), com os campos novos removidos, são
   **idênticos byte a byte (como JSON) ao baseline**; `manifest`/`timemap`/
   `meta`/`midi` idênticos; nenhuma linha de `View`/`svg`/`bbox` mudou
   (`git diff`). Como os campos novos não são pintados, o PNG é o mesmo por
   construção — mas **rodar `compare-corpus.sh` (e `SWEEP_ALTERNATES=1`) numa
   máquina com Flutter continua pendente** e é barato.
2. **2 197 nós `staff`** (normais e alternativos) com `lines`; `topY + k·2·unit`
   bate com os `n` primeiros filhos `p` em todos (tolerância 0,5): 0 falhas.
3. **18 008 cabeças** (`u` dentro de `notehead`) satisfazem `y = topY + (2(n−1) −
   loc)·unit` com `loc` inteiro (tolerância 0,51), na pauta ancestral ou em
   `staff` (cross-staff): **0 exceções**.
4. Os 8 glifos reservados estão em todos os `glyphs.json`; os **únicos** glifos
   acrescentados em relação ao baseline são eles (e os já existentes não mudam).
5. Tamanho (bytes, antes → depois, `scene.json` / `glyphs.json`): Satie
   356 285 → 363 284 / 14 089 → 25 564; Nocturne 1 894 893 → 1 907 834 /
   30 475 → 41 432; Maple Leaf Rag 1 411 622 → 1 424 295 / 14 794 → 26 444;
   demais no mesmo padrão (cena +0,7% a +2,3%; dicionário +~11 KB, os
   glifos reservados).

A varredura pegou um erro de método, não de código: `-t vsb` a partir do MEI
gerado com a mesma `--xml-id-seed` que o `-t mei` gera ids que **colidem**
com os do MEI (o `Toolkit` recomeça a sequência); o oráculo de G04d usa
sementes diferentes.
