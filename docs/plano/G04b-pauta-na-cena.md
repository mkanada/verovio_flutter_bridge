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

_(vazio)_
