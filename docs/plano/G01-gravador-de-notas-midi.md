# G01 — Gravador de eventos MIDI: `midi.json` no `.vsb`

**Depende de:** — · **Decisão necessária:** talvez (**D-RELOGIO**, só se o
critério 4 falhar — ver abaixo)

> Este passo nasceu como **N01** no plano do host (`zywny/docs/plano/README.md`
> e `N01-notes-json-no-fork.md`, cross-repo): lá o passo virou um ponteiro
> para aqui, porque é 100% código deste repo (exportador C++ + spec). A
> letra **G** é nova neste plano (as fases existentes são F/S/R/A/E/P) e não
> colide com as letras que o zywny já usa (C/K/M/N/T/V/W/X) — evite reusar
> `N` aqui por causa disso.
>
> **Revisão de 2026-09-25** (antes de executar): a primeira versão deste
> passo gravava só **atributos** por nota (`notes.json`: pitch, pauta,
> canal…) e deixava o **tempo** com o timemap; o host teria de juntar
> ligaduras e ornamentos sozinho. Decisão do usuário: gravar o **fluxo de
> eventos que o exportador MIDI emite**, cada um com o `xml:id` de origem —
> o que o `.mid` tocaria, em ms, com ligaduras já unidas, ornamentos já
> expandidos e pedal incluído. Continua sendo um gravador dentro do
> `GenerateMIDIFunctor`, **não** uma cópia do exportador.

## Objetivo

O timemap diz **quando** cada id acende e apaga (para o destaque visual),
mas não **o que soa**. Acrescentar ao `.vsb` um arquivo opcional
`midi.json`: a lista de notas e pedais exatamente como o exportador MIDI do
Verovio as tocaria, com tempo em ms e o `xml:id` (expandido, `-rend<N>`, os
mesmos do timemap) de onde cada evento veio. É a base de o host tocar a
partitura por soundfont, mandar MIDI para um teclado externo e avaliar o que
o aluno toca — nenhuma dessas três coisas é deste repo (ficam no zywny), mas
todas dependem deste arquivo existir.

## Ler antes (só isto)

- `CLAUDE.md` (convenções) e `docs/formato/especificacao-v1.md` §2 a §2.6
  (empacotamento; leia principalmente §2.1 `manifest.json`, §2.4 `timemap.json`
  pela regra de sufixo `-rend<N>`, e §9 compatibilidade/aditividade).
- `verovio/src/midifunctor.cpp` — **os pontos de emissão**, todos dentro do
  `GenerateMIDIFunctor`:
  - `VisitNote` L808-904: filtros (sameas L813, cue L818, ligadura
    secundária L823, `velocity == 0` L828), nota adiada L835
    (`m_deferredNotes`), ornamento expandido L842-851 (`m_expandedNotes`),
    nota de tablatura segurada L855-890 (`m_heldNotes`), nota comum
    L892-896.
  - `VisitLayerEnd` L754-767: note-offs pendentes das notas de tablatura.
  - `VisitPedal` L906-939: `down`/`up`/`bounce` → `addSustainPedalOn/Off`.
  - `VisitMeasure` L784-799: `m_totalTime` (onset do compasso em
    semínimas) e o único ponto onde o MIDI emite **mudança de andamento**
    (`addTempo`, só no início de compasso).
  - `GetMIDIPitch` L1149 (privado; já aplica `m_transSemi`,
    `m_octaveShift` e afinação customizada).
- `verovio/include/vrv/midifunctor.h`: `GenerateMIDIFunctor` L349-478
  (setters L375-387; membros `m_staffN`, `m_layerN`, `m_midiChannel`,
  `m_instrDef`, `m_expandedNotes`, `m_heldNotes`); `MIDIHeldNote` L341.
- `verovio/src/doc.cpp` `Doc::ExportMIDI` L445-633: andamento inicial
  L457-472; laço por pauta/camada L522-630, onde cada `GenerateMIDIFunctor`
  é criado e configurado (L608-620).
- `verovio/src/toolkit.cpp`: `Toolkit::RenderToBridgeJson` L2092 e
  `Toolkit::RenderToBridgeFile` L2365 — **são dois caminhos de código
  separados** que montam manifest/scene/glyphs/timemap/meta/alternates/debug
  cada um à sua vez (o primeiro via `BridgeWriter::WriteSingleJson`, o
  segundo escrevendo direto no zip, L2431-2444); os dois precisam do
  `midi.json`. Referência de uso do exportador: `RenderToMIDIFile` (L1877,
  `SetMidiDoc()` + `m_midiDoc->ExportMIDI(...)`).
- `verovio/include/vrv/bridgewriter.h` L85-112 / `src/bridgewriter.cpp`
  L597-700: `WriteManifest` (L622; chamado em `bridgewriter.cpp:678` e
  `toolkit.cpp:2431`), `WriteMeta`/`WriteAlternates` (modelos de writer a
  copiar).

## Contexto que você precisa

### Por que o exportador MIDI e não o timemap

O `GenerateMIDIFunctor` já resolve tudo o que o host precisaria refazer:

- **Ligadura**: a nota principal sai com duração até o fim da cadeia
  (`GetScoreTimeTiedDuration`, L893) e as secundárias são puladas (L823).
- **Ornamentos**: trinado/tremolo/mordente viram a sequência de notas curtas
  que o MIDI toca (`m_expandedNotes`, L842).
- **Appoggiatura/Nachschlag/arpejo**: início adiado (`m_deferredNotes`,
  L835).
- **Altura**: `GetMIDIPitch(note)` = transposição (`transSemi`) + 8va/8vb
  (`HandleOctave` → `m_octaveShift`) + afinação customizada. (O
  `getMIDIValuesForElement` do toolkit usa `note->GetMIDIPitch()` sem
  argumentos e **erra** instrumento transpositor e 8va — não use.) O corpus
  tem 8va (classe `octave` no Chopin Étude e no Clair de Lune).
- **Pedal**: `VisitPedal` já emite sustain on/off.

### Estratégia: gravador opcional no `GenerateMIDIFunctor`

Mesmo molde das outras opções do functor (`SetDeferredNotes`,
`SetTempoEventTicks`): um ponteiro `nullptr` por padrão → **zero mudança**
no `.mid`.

- Em `midifunctor.h`:

  ```cpp
  struct MIDIEventRecord {
      enum class Type { Note, PedalDown, PedalUp };
      Type type;
      std::string id;      // xml:id da nota/pedal de origem (documento expandido)
      double onQ;          // tempo em semínimas (o valor antes de "* tpq")
      double offQ;         // só Note: fim, sem o "- 1 tick" do MIDI
      int pitch, staff, layer, channel, program, velocity; // pitch/velocity só Note
      bool ornament;       // nota de sequência expandida (trinado/tremolo...)
  };
  struct MIDIEventLog {
      std::vector<MIDIEventRecord> events;
      std::vector<std::pair<double, double>> tempos; // (semínima, bpm), na ordem de emissão
  };
  // GenerateMIDIFunctor:
  void SetEventLog(MIDIEventLog *log) { m_eventLog = log; }
  ```

- Grave **ao lado de cada chamada** `addNoteOn`/`addNoteOff`/
  `addSustainPedal*`/`addTempo`, com os mesmos valores (antes de
  multiplicar por `tpq`):
  - nota comum (L895-896): um `Note` com `onQ = startTime`,
    `offQ = stopTime`;
  - ornamento (L846-847): um `Note` **por nota da sequência**, todos com o
    id da nota escrita e `ornament = true`;
  - tablatura (L889 + o off diferido em L873/L759): guarde o id em
    `MIDIHeldNote` e grave o `Note` quando o off for emitido. O corpus é de
    piano, então isso não é testado aqui — só não pode quebrar;
  - pedal (L929-933): `down` → `PedalDown`, `up` → `PedalUp`, `bounce` →
    `PedalUp` + `PedalDown` no mesmo instante (o `+0.1` tick do MIDI some
    no arredondamento para ms). `half` e `@dir` ausente continuam não
    emitindo nada, como no MIDI;
  - andamento (`VisitMeasure` L794 e o inicial em `Doc::ExportMIDI`
    L466/L471): `(semínima, bpm)` em `tempos`.
- `staff = m_staffN`, `layer = m_layerN`, `channel = m_midiChannel`,
  `program = m_instrDef && m_instrDef->HasMidiInstrnum() ?
  m_instrDef->GetMidiInstrnum() : 0`.
- `Doc::ExportMIDI(smf::MidiFile *midiFile, MIDIEventLog *log = nullptr)`
  repassa o ponteiro para cada `GenerateMIDIFunctor` do laço (L608-620) —
  o mesmo log para todas as pautas/camadas.
- **Semínimas → ms** depois do export, pela lista `tempos` (integração por
  trechos: `ms = ms_do_trecho + (q - q_do_trecho) * 60000 / bpm`), que é o
  que um tocador MIDI faz — mas sem a quantização em ticks do `.mid`. Não
  use `MidiFile::doTimeAnalysis`/`getTimeInSeconds`: eles trabalham em
  ticks inteiros e somam até 1 tick de erro por evento.
- `Toolkit::RenderToBridgeJson`/`RenderToBridgeFile`: `SetMidiDoc()`,
  `smf::MidiFile scratch; m_midiDoc->ExportMIDI(&scratch, &log);`,
  converter e serializar. Repita nos **dois** lugares — não há um terceiro
  caminho que os unifique hoje.
- **Ids**: o `m_midiDoc` é o documento expandido; os ids de nota são
  exatamente os do timemap (inclusive `-rend<N>`). O pedal carrega o id do
  `<pedal>` (que não aparece no timemap — o leitor não deve esperar isso).

### Ligadura: o que o host precisa além do evento

O evento de uma nota ligada leva o id da **primeira** nota da cadeia e soa
até o fim da última. O host ainda precisa saber quais ids de continuação
pertencem a ela (para acender/apagar no destaque e não exigir que o aluno
os toque). Grave `tied`: a lista de ids de continuação, na ordem. Duas
maneiras de achá-los — escolha e registre nas notas de execução:

1. percorrer `Tie::GetStart/GetEnd` a partir da nota (ver
   `InitTimemapTiesFunctor::VisitTie`, `midifunctor.cpp` L313);
2. gravar também as notas puladas em L823 (id + pauta + camada + pitch) e,
   no pós-processamento, ligar cada uma ao evento aberto de mesmo
   pitch+pauta+camada.

### Formato proposto

Mesma regra de omissão do timemap/`meta`/`alternates` (§2.1/§9): sem
nenhum evento, sem arquivo nem entrada no manifest; aditivo, `version`
continua `1`.

```json
{
  "notes": [
    {"id":"n1a2b","on":0,"off":500,"p":64,"s":1,"l":1,"c":0,"pg":0,"v":90},
    {"id":"n77-rend2","on":12000,"off":14000,"p":52,"s":2,"l":1,"c":0,"pg":0,"v":90,"tied":["n9f-rend2"]},
    {"id":"n33","on":3000,"off":3062.5,"p":71,"s":1,"l":1,"c":0,"pg":0,"v":90,"orn":true},
    {"id":"n33","on":3062.5,"off":3125,"p":72,"s":1,"l":1,"c":0,"pg":0,"v":90,"orn":true}
  ],
  "pedal": [
    {"id":"pd12","t":1000,"dir":"down","s":1,"c":0},
    {"id":"pd13","t":4000,"dir":"up","s":1,"c":0}
  ]
}
```

- `on`/`off`/`t` em ms, **mesmo relógio e mesma precisão do `tstamp` do
  timemap** (§2.4) — é isso que o critério 4 mede.
- `notes` ordenado por `on` (depois `s`, `l`, `p`); `pedal` por `t`. Um id
  pode aparecer em várias entradas (ornamento), então o leitor indexa por id
  em **lista**, não em valor único.
- Chaves curtas porque o corpus tem ~10 mil notas; campos com valor padrão
  (`c:0`, `pg:0`, `orn:false`, `tied:[]`) podem ser omitidos se a spec
  disser (decida e documente na spec).
- `manifest.files.midi = "midi.json"`; no JSON único, propriedade `midi`.
  `BridgeWriter::WriteManifest` (`bridgewriter.h` L102) ganha
  `bool hasMidi = false`; atualize as duas chamadas (`bridgewriter.cpp:678`,
  `toolkit.cpp:2431`) e o corpo (`bridgewriter.cpp` L622-644, mesmo padrão
  de `hasAlternates`/`hasDebug`).
- Atualize `docs/formato/especificacao-v1.md`: nova §2.7 (entre §2.6 modo
  debug e §3 unidades), linha nova em §2.1 (tabela `files`) e em §2.2 (JSON
  único), linha nova em **Histórico de revisões** com a data de execução —
  siga o tom das entradas de P02a/E01b (o que mudou, por que, se é aditivo).
  A §2.7 deve dizer, com todas as letras: *os tempos seguem o que o
  exportador MIDI do Verovio toca; o `off` não tem o "−1 tick" do `.mid`;
  ornamentos repetem o id; `pedal[].id` não aparece no timemap*.
  `docs/formato/schema-v1.json`: `$defs/midiDocument` (mesmo padrão de
  `$defs/timemapDocument`/`$defs/metaDocument`/`$defs/alternatesDocument`,
  `$defs` começa em L13), referência em `files`/`manifest`/raiz do JSON único
  (mesmo lugar de `timemap`/`meta`/`alternates`, ~L291-293 e ~L502-504).
- Saídas de teste em `compare/out/g01/`.

### O risco: dois relógios (D-RELOGIO)

O destaque visual usa o timemap; o som vai usar o `midi.json`. Se os dois
divergirem, a nota acende fora do tempo do som. Os dois partem dos mesmos
onsets (`GetScoreTimeOnset`), mas há diferenças conhecidas a verificar:

- **Andamento**: o MIDI só muda de andamento **no início do compasso**
  (`VisitMeasure` L789); o cálculo do timemap também lê `<tempo>`
  (`InitMaxMeasureDurationFunctor::VisitTempo` L295). Um `<tempo>` no meio
  do compasso pode separar os relógios.
- **`--midi-tempo-adjustment`** (`m_timemapTempo`, `doc.cpp` L442): confira
  se entra nos dois.
- **Notas adiadas** (`m_deferredNotes`): o MIDI desloca; confira se o
  timemap desloca igual.

O critério 4 mede isso. Se **bater** (tolerância 1 ms), nada a decidir. Se
**não bater**, **pare e leve ao usuário** (D-RELOGIO): qual relógio é o
canônico e se o outro deve ser corrigido no fork (e onde). Não corrija
sozinho — mexer no cálculo do timemap muda um arquivo que as fases A/E/P já
consomem.

## O que fazer

1. `MIDIEventRecord`/`MIDIEventLog` + `SetEventLog` no
   `GenerateMIDIFunctor`; gravação ao lado de cada emissão (nota, ornamento,
   tablatura, pedal, andamento); parâmetro em `Doc::ExportMIDI` repassado no
   laço de `doc.cpp`.
2. `tied` (uma das duas maneiras acima) e conversão semínimas → ms.
3. `BridgeWriter::WriteMidi` (novo, mesmo molde de `WriteMeta`/
   `WriteAlternates`) + `hasMidi` no manifest + os dois pontos de integração
   (`RenderToBridgeJson`/`WriteSingleJson` e `RenderToBridgeFile`).
4. Spec (§2.7 + tabelas de manifest/JSON único + histórico) e schema
   (`$defs/midiDocument`).
5. Script de verificação (Python 3 da máquina, sem dependências — leia o
   `.mid` com um parser mínimo ou use `mido` se estiver instalado; registre
   qual).

## Fora de escopo

- Qualquer código Dart (**G02**, no `score_bridge/` deste mesmo repo).
- Velocity de dinâmicas (`p`, `f`) — o Verovio não converte; fica
  `MIDI_VELOCITY` salvo `@vel` explícito. Se um dia o MIDI passar a
  converter, o `midi.json` acompanha de graça.
- `@func` do pedal (una corda/sostenuto): o MIDI trata tudo como sustain
  (`TODO` em `midifunctor.cpp` L927); o `midi.json` segue o MIDI.
- CCs, pitch bend, andamento como evento no JSON (o andamento já está
  embutido nos ms).

## Critérios de aceite

1. **Nada muda sem o gravador**: `verovio -t midi` e `-t svg` nas 10 peças
   do corpus ficam **byte-idênticos** aos de antes; no `-t vsb`,
   `scene.json`/`glyphs.json`/`timemap.json` também (compare com uma geração
   feita antes da mudança, ex.: `compare/out/s08/*.vsb` ou um `git stash`
   rápido).
2. **`midi.json` = `.mid`**: para cada peça, o multiconjunto
   `(canal, pitch, on)` das notas do `midi.json` bate com os note-on do
   `verovio -t midi` da mesma peça, com o tick do `.mid` convertido para ms
   pelo mapa de andamento do próprio `.mid`, tolerância de 1 tick no
   andamento local. Mesmo teste para os eventos de pedal (CC 64). Divergência
   zero, inclusive no Chopin Étude e no Clair de Lune (8va).
3. **Cobertura de ids**: todo id em `timemap[].on` que é nota aparece em
   `midi.json`, como `id` de uma entrada ou dentro de um `tied`; as exceções
   (silenciosa `vel=0`, cue com `--midi-no-cue`, `sameas`) são contadas e
   listadas. Nenhum id de nota em `midi.json` fora do timemap.
4. **Dois relógios**: para toda entrada **sem** `orn` e sem adiamento, `on`
   = `on` do mesmo id no timemap, e `off` = `off` do **último** id de
   `tied` (ou do próprio id), tolerância 1 ms. Relate o total por peça e
   liste as divergências. Divergência ≠ 0 → D-RELOGIO (acima).
5. **Repetições**: Gymnopédie e Maple Leaf Rag têm ids `-rend2` com o mesmo
   pitch da passagem 1.
6. **Pedal**: as quatro peças do corpus que desenham pedal (Chopin Étude,
   Chopin Nocturne, Clair de Lune, Grieg Butterfly — classe `pedal` no SVG
   de `compare/corpus/`) têm `pedal` não-vazio batendo com o critério 2.
   Se alguma não tiver, é porque o `<pedal>` veio sem `@dir` (o MIDI também
   não emite nada): conte e registre.
7. `score_bridge` (**G02**, ainda não escrito quando G01 roda) continua sem
   quebrar: um leitor que ignora arquivo extra no zip não é afetado — não é
   um critério a rodar aqui, só uma garantia de que G01 não obriga G02 a
   existir para o `.vsb` continuar válido.
8. Spec/schema atualizados; um `midi.json` do corpus valida contra o
   schema.

## Notas de execução

(preencher)
