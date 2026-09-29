# G04c — C++: `pitchpos.json` (contexto de notação por nota/pausa) e pausas no timemap

**Depende de:** G04a · **Decisão necessária:** não (D-FANT-PAUSA-TEMPO
resolvida em 2026-09-29: `includeRests` no timemap)

## Objetivo

Gravar `pitchpos.json` (§2.8, G04a) nos dois caminhos do exportador
(`RenderToBridgeJson` e `RenderToBridgeFile`) e ligar `includeRests` no
timemap embutido. Toda a semântica musical (clave, 8va/transposição,
armadura, acidentes em vigor, altura escrita) vem do Verovio.

## Ler antes (só isto)

- [`G03`](G03-visao-geral-nota-fantasma.md) inteiro.
- `docs/formato/especificacao-v1.md` §2.4, §2.8, §10 (como ficaram em G04a).
- [`G01`](G01-gravador-de-notas-midi.md) "Estratégia" e "Notas de
  execução": o molde do gravador opcional dentro do `GenerateMIDIFunctor` e
  os **dois** caminhos de escrita em `toolkit.cpp`.
- `verovio/src/pitchinterface.cpp` L143-L192 (`CalcLoc`, com o
  `clefLocOffset` de `Layer::GetClefLocOffset` e o ajuste cross-staff).
- `verovio/src/midifunctor.cpp`: `HandleOctave` (L1164, é onde nasce
  `m_octaveShift`), `m_transSemi` (L1085), `GetMIDIPitch` (L1149),
  e o timemap das pausas (L1338-L1413).
- `verovio/src/editortoolkit_shared.cpp` L1425-L1480
  (`GetActualAccid`/`GetAccidBefore`): a lógica que o próprio Verovio usa
  para "acidente em vigor"; `KeySig::FillMap` (`keysig.cpp` L199).
- `verovio/src/toolkit.cpp` ~L2417 (`RenderToTimemap("{\"includeMeasures\": true}")`).

## Contexto que você precisa

- **Dois documentos.** A cena é desenhada do `Doc` **notado**
  (`m_doc`); o timemap e o `midi.json` saem do `m_midiDoc` **expandido**
  (`-rend<N>`). `pitchpos.json` é indexado pelo id notado (G03 §
  Invariantes) — o contexto é o mesmo em toda passagem.
- **De onde sai cada campo** (recomendação; registre o que usar):
  - `co`, `loc`, `pn`/`o`/`alt`, `key`, `acc`: do `m_doc` notado, depois do
    layout (o mesmo estado que o `View` usa). `co` como em `CalcLoc`
    (`GetClefLocOffset` + `GetCrossStaffClefLocOffset`); `loc` o que a nota
    usou para desenhar (confirme o acessor — `PositionInterface::
    GetDrawingLoc` ou `CalcLoc`); a armadura **vigente no elemento** (não a
    do fim do sistema — teste com mudança de armadura no meio do sistema);
    `acc` percorrendo o compasso **por pauta** (todas as camadas), como na
    notação comum — `GetAccidBefore` do editor é por camada, não reuse cego.
  - `sh`: `m_transSemi + 12 × m_octaveShift` no momento em que o
    `GenerateMIDIFunctor` visita o elemento (acrescente ao gravador de G01
    uma entrada por nota **e pausa** visitada, com esse valor). Grave por id
    notado; se duas passagens derem `sh` diferente para o mesmo id, é bug —
    conte e registre (esperado: 0).
- **Por que não reusar `GetMIDIPitch` sem argumentos**: ignora 8va e
  transposição (G01, "Por que o exportador MIDI e não o timemap").
- **Timemap**: `includeRests` acrescenta `restsOn`/`restsOff`. O esperado
  (G03, D-FANT-PAUSA-TEMPO) é que as entradas já existam e só as chaves
  sejam novas — **confira**: número de entradas e todos os campos antigos
  byte-idênticos, fixture a fixture.

## O que fazer

1. Gravador de `sh` no `GenerateMIDIFunctor` (nota e pausa), mesmo molde de
   `SetEventLog` (ponteiro nulo por padrão → `.mid` idêntico).
2. Coleta do contexto no `m_doc` notado (função/functor novo em arquivo
   próprio, ex. `bridgepitchpos.cpp`/`.h`; rode `cmake ../cmake` depois de
   criar o `.cpp`).
3. `BridgeWriter::WritePitchPos` + manifest; nos dois caminhos do
   `toolkit.cpp`. Opção de CLI para desligar, no molde de
   `--no-vsb-alternates` (padrão: gerar).
4. `includeRests: true` no timemap embutido.
5. Partituras mínimas de teste (MEI, em `corpus/fantasma/`, no molde de
   `corpus/repeticoes/` de E01a) para o
   que o corpus não cobre, cada uma com uma nota "alvo" conhecida:
   mudança de clave no meio do compasso; 8va e 8vb (o corpus tem 8va no
   Chopin Étude e no Clair de Lune); instrumento transpositor (clarinete
   em Si♭, `trans.semi="-2"`); nota cross-staff; armadura não padronizada;
   mudança de armadura no meio do sistema; acidente escrito antes no
   compasso (inclusive bequadro e dobrado) em outra camada da mesma pauta;
   pausa e `mRest` em duas pautas.

## Fora de escopo

- A fórmula em si e o oráculo (G04d). Lado Dart (`zywny`).

## Critérios de aceite

1. `.mid` byte-idêntico antes/depois (`-t midi`) para o corpus inteiro.
2. Timemap: número de entradas e campos antigos idênticos; só
   `restsOn`/`restsOff` novos (script descartável, resultado por peça).
3. Toda nota e pausa desenhada (id com classe `note`/`rest`/`mRest` na
   cena, `hidden` excluído) tem entrada em `pitchpos.json`, e vice-versa —
   exceções contadas e explicadas.
4. Para toda nota: `loc` gravado = `CalcLoc(pn, o, co)` (ou `@loc`
   explícito) e `midi.p = altura(pn, o, alt) + sh` para as notas que têm
   entrada em `midi.json` — divergências contadas (esperado: 0).
5. Cena, glifos e paridade inalterados (a cena de G04b é a base).
6. Tamanho de `pitchpos.json` e tempo total de export, antes/depois, por
   peça do corpus.

## Notas de execução

Concluído em 2026-09-29. Novo `verovio/src/bridgepitchpos.cpp`/`include/vrv/
bridgepitchpos.h` (`BridgePitchPosBuilder::Build`), `BridgeWriter::WritePitchPos`,
`Toolkit::RenderPitchPos`, opção `--no-vsb-pitchpos`, e, em
`GenerateMIDIFunctor`, `MIDIEventLog::shifts` (um par (id, `m_transSemi + 12 ·
m_octaveShift`) por nota — no topo de `VisitNote`, depois de `HandleOctave`, portanto
também para continuações de ligadura e notas cue — e por `rest`/`mRest`/
`multiRest` em `VisitLayerElement`; `nullptr` por padrão, então o `.mid` não
muda). O `pitchpos.json` sai dos dois caminhos (`-t vsb` e `-t vsb-json`), e
`RenderToBridgeFile` passou a gerar o log MIDI **antes** das alternativas
(elas fazem `Select`/`RedoLayout`; o contexto lê o layout normal).

De onde sai cada campo: `co` = `Layer::GetClefLocOffset` com a resolução cross-staff
copiada de `CalcLoc`/`CalcAlignmentPitchPosFunctor`; `loc` = `Note::GetDrawingLoc()`
(o do desenho); `key` = `KeySig::FillMap` do `KeySig` da camada anterior ao elemento
(mudança de armadura dentro da camada) ou o da pauta no compasso
(`Layer::GetCurrentKeySig`); `acc` = acidentes escritos (`Accid::HasAccid`) do
compasso por pauta de desenho, ordenados por alinhamento (tempo; apojatura antes
da nota principal), incluindo o mesmo instante; `alt` = a
alteração sonora (ver G04a); `sh` = a do MIDI. Timemap embutido com
`includeRests`. Notas ocultas (`visible="false"`) **entram** (o host pode
esperá-las); nota sem `@pname` não.

Critérios (`compare/scripts/g04c-check.py`, `g04c-fantasma-check.py`):

1. `.mid` byte-idêntico e `-t timemap` standalone byte-idêntico, 23 peças.
2. Timemap embutido: mesmo número de entradas e campos antigos idênticos em
   todas; 1 120 ids em `restsOn` no total, nenhuma outra chave nova.
3. 10 369 notas + 850 pausas; toda nota/pausa desenhada tem entrada e toda
   entrada tem nó na cena (oculto incluído): **1 exceção** — `g1157trh` na
   Mazurka Op. 6 nº 1 é uma apojatura (`grace="unknown"`) **sem
   `@pname`** na fonte (`<!-- add grace notes! -->`), desenhada e com evento
   MIDI de altura 0.
4. `loc` gravado = `(o−4)·7 + (pname−1) + co` em **10 369/10 369** notas;
   `midi.p = altura(pn, o, alt) + sh` em **12 692 eventos** de `midi.json`
   (fora ornamentos), 1 exceção (a mesma nota sem `@pname`). Ids visitados
   com `sh` diferente em passagens diferentes (`conflictingShift`): **0**; notas/
   pausas sem `sh` (`missingShift`): **0** (o `Toolkit` avisa por `LogWarning`, e os
   `.log` da geração estão limpos).
5. Cena, glifos e demais arquivos idênticos à saída de G04b.
6. `pitchpos.json`: Satie 26 655 B (334 eventos), Nocturne 199 184 B (1 775),
   Maple Leaf Rag 167 138 B (1 647), Chopin Étude 85 280 B (1 276), peças de
   repetição 126 B a 2 266 B; `.vsb` total +2,4% a +11,2% contra antes de G04
   (mediana ≈ +6,8%); tempo de geração, soma das 10 peças grandes: 3,58 s →
   3,58 s (ruído entre execuções maior que a diferença).

`corpus/fantasma/` (8 partituras MEI, `f01`-`f08`): mudança de clave no meio do
compasso, 8va e 8vb, clarinete em Si♭, nota cross-staff, armadura não
padronizada, mudança de armadura (dó → 3♯ → 3♭), acidentes em outra camada
(♯, ♮, dobrado ♯♯ e acidente já em vigor no compasso seguinte), pausas e `mRest` em duas
pautas. `corpus/fantasma/esperado.json` tem 30 ids com valores **escritos à
mão** (pela teoria, não copiados da saída) e
`compare/scripts/g04c-fantasma-check.py` confere: **0 divergências**.
Nas fixtures MEI, `accid.ges` precisa ser escrito nas notas alteradas pela
armadura (como os importadores fazem): o Verovio não aplica a armadura no MIDI.
