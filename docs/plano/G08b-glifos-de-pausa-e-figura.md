# G08b — C++: glifos de pausa reservados e figura no `pitchpos.json`

**Depende de:** G08a · **Decisão necessária:** não (D-SUM-FIGURA fechada em
G08a)

## Objetivo

O exportador passa a gravar o que a §11 promete: os glifos de pausa e o
ponto de aumento sempre no dicionário, e `dur`/`dots` de cada nota e pausa
no `pitchpos.json`. Sem tocar em nada que desenha.

## Ler antes (só isto)

- [`G07`](G07-visao-geral-nota-escondida.md) e a §2.8, §4 e §11 da spec
  (como G08a as deixou).
- `verovio/src/bridgedevicecontext.cpp`: `AddReservedGlyphs` (L1254-L1268).
- `verovio/src/bridgepitchpos.cpp` inteiro (onde cada campo de evento é
  gravado; a ordem canônica das chaves, §7).
- `verovio/src/rest.cpp` L255-L320 (`Rest::GetRestGlyph`: a tabela figura →
  glifo, para conferir a lista).
- [`G04b`](G04b-pauta-na-cena.md) e [`G04c`](G04c-contexto-por-evento.md),
  notas de execução: como a paridade foi provada sem Flutter e o cuidado
  com `--xml-id-seed`.

## Contexto que você precisa

- **Glifos**: acrescentar a `reserved[]` os códigos `SMUFL_E4E3_restWhole`,
  `E4E4_restHalf`, `E4E5_restQuarter`, `E4E6_rest8th`, `E4E7_rest16th`,
  `E4E8_rest32nd`, `E4E9_rest64th` e `SMUFL_E1E7_augmentationDot`. O caminho
  é o mesmo de hoje (`MakeGlyphUse` com a fonte da peça); glifo que a fonte
  não tem é pulado em silêncio, como já acontece.
- **Figura**: `DurationInterface::GetActualDur()` (a figura, não a duração
  de execução) e `GetDots()`. Nota dentro de acorde não tem duração
  própria: usa a do `Chord`. `dur` no JSON é o denominador (`DURATION_4` →
  `4`); breve, longa e máxima não gravam o campo. `dots` só é gravado
  quando > 0.
- **Pausas** (`rest`): também ganham `dur`/`dots`. `mRest` (pausa de
  compasso inteiro) **não** tem figura: sem o campo.
- **Apojatura** (`grace`) e nota `cue`: gravam a figura escrita, como as
  demais. O host decide o que fazer.
- `View`, `SvgDeviceContext` e `BBoxDeviceContext` continuam intactos
  (regra do `CLAUDE.md`).
- Gerar "antes" e "depois" com `compare/scripts/g04-gen.sh` e
  `--xml-id-seed 42`; sem semente os ids mudam e nada compara.
- Tamanho esperado: 8 glifos (~10 KB no dicionário, pelo que G04b mediu
  com 8) e ~10-18 bytes por evento do `pitchpos.json`.

## O que fazer

1. `AddReservedGlyphs`: os 8 códigos novos.
2. `bridgepitchpos.cpp`: `dur` e `dots`, na ordem canônica definida em
   G08a.
3. `cd verovio/tools && make -j4`; regenerar o corpus em
   `compare/out/g08b/` (antes e depois).
4. Script descartável `compare/scripts/g08b-check.py` para os critérios
   2-4.
5. Regenerar as fixtures de `docs/formato/fantasma/*.vsb` **só se** os
   vetores de G04d continuarem batendo (`ghost_ref.py --self-test`,
   `ghost_oracle.py`) — os campos novos não entram na §10.

## Fora de escopo

- Qualquer campo novo em `scene.json` (plano B de D-SUM-NATIVO: só se G08c
  pedir, e é outro passo).
- O lado Dart (`zywny`).
- Lib do Android/Windows/wasm: quem empacota é o `zywny` (G09 avisa).

## Critérios de aceite

1. **Paridade inalterada**: `scene.json`, `alternates.json`, `timemap`,
   `midi` e `meta` idênticos byte a byte ao baseline nas peças do corpus e
   de `corpus/repeticoes`; `compare-corpus.sh` (normais e
   `SWEEP_ALTERNATES=1`) com os mesmos percentuais de P05, se houver
   Flutter na máquina — senão, registre que ficou pendente, como em G04b.
2. Os 16 glifos reservados estão em todo `glyphs.json` do corpus; os
   **únicos** glifos acrescentados em relação ao baseline são os 8 novos.
3. `pitchpos.json`: toda nota e toda pausa (`t: "r"` que não seja `mRest`)
   de figura entre semibreve e semifusa tem `dur`; conte por peça quantas
   ficaram sem e por quê.
4. Conferência cruzada da figura: para toda **pausa de verdade** do corpus,
   o glifo desenhado na cena é o de `Rest::GetRestGlyph` para o `dur`
   gravado — 0 divergências (é o que garante que a tabela figura → glifo do
   host é a do Verovio).
5. `ghost_ref.py --self-test` e o oráculo de G04d com os mesmos números de
   G06 (32 casos; 2 400 alvos, 0 divergências).
6. Tamanho: `glyphs.json` e `pitchpos.json` antes/depois por peça,
   registrados.

## Notas de execução

_(preencher ao executar)_
