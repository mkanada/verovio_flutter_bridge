# G01 — Gravador de notas MIDI: `notes.json` no `.vsb`

**Depende de:** — · **Decisão necessária:** não

> Este passo nasceu como **N01** no plano do host (`zywny/docs/plano/README.md`
> e `N01-notes-json-no-fork.md`, cross-repo): lá o passo virou um ponteiro
> para aqui, porque é 100% código deste repo (exportador C++ + spec). A
> letra **G** é nova neste plano (as fases existentes são F/S/R/A/E/P) e não
> colide com as letras que o zywny já usa (C/K/M/N/T/V/W/X) — evite reusar
> `N` aqui por causa disso.

## Objetivo

O timemap diz **quando** cada id liga e desliga, mas não **qual nota** é.
Acrescentar ao `.vsb` um arquivo opcional `notes.json` com, por id de nota
(expandido, `-rend<N>`, os mesmos do timemap): altura MIDI, pauta, camada,
canal, programa, velocity e papel na ligadura. É a base de o host tocar a
partitura por soundfont, mandar MIDI para um teclado externo e avaliar o que
o aluno toca — nenhuma dessas três coisas é deste repo (ficam no zywny), mas
todas dependem deste arquivo existir.

## Ler antes (só isto)

- `CLAUDE.md` (convenções) e `docs/formato/especificacao-v1.md` §2 a §2.6
  (empacotamento; leia principalmente §2.1 `manifest.json`, §2.4 `timemap.json`
  pela regra de sufixo `-rend<N>`, e §9 compatibilidade/aditividade).
- `verovio/src/toolkit.cpp`: `Toolkit::RenderToBridgeJson` L2092-L2146 e
  `Toolkit::RenderToBridgeFile` L2365-L2450 — **são dois caminhos de código
  separados** que hoje montam manifest/scene/glyphs/timemap/meta/alternates/
  debug cada um à sua vez (o primeiro via `BridgeWriter::WriteSingleJson`, o
  segundo escrevendo direto no zip); os dois precisam do `notes.json` novo,
  então mexem os dois.
- `verovio/src/doc.cpp` `Doc::ExportMIDI` L445-L640-ish, laço por pauta/camada
  L526-L620: é aqui que cada `GenerateMIDIFunctor` é criado e configurado
  (`SetStaffN`/`SetLayerN`/`SetChannel`/`SetTransSemi`/`SetInstrDef`, L608-L620).
- `verovio/src/midifunctor.cpp` `GenerateMIDIFunctor::VisitNote` L808-L904 e
  `GetMIDIPitch` L1149 (privado); `verovio/include/vrv/midifunctor.h`
  `GenerateMIDIFunctor` L349-L478 (membros `m_staffN`, `m_layerN`,
  `m_midiChannel`, `m_instrDef`, `m_expandedNotes`).
- `verovio/include/vrv/bridgewriter.h` L85-L112 / `src/bridgewriter.cpp`
  L597-L700: `WriteManifest` (L622, chamada em `bridgewriter.cpp:678` dentro
  de `WriteSingleJson`, e em `toolkit.cpp:2431` dentro de
  `RenderToBridgeFile`), `WriteMeta` (modelo de um writer pequeno a copiar).

## Contexto que você precisa

- **Por que não `getMIDIValuesForElement`**: ele usa `note->GetMIDIPitch()`
  sem argumentos, ignorando `transSemi` (instrumento transpositor) e 8va/8vb
  (`HandleOctave` → `m_octaveShift`). O `GenerateMIDIFunctor` aplica os dois
  (`GetMIDIPitch(note)` = `note->GetMIDIPitch(m_transSemi, m_octaveShift)`,
  ou afinação customizada). O corpus tem 8va (classe `octave` no Chopin
  Étude e no Clair de Lune) — use-os no teste.
- **Estratégia recomendada** (mínima, sem duplicar lógica): um "gravador"
  opcional no `GenerateMIDIFunctor`:
  - `struct MIDINoteRecord { std::string id; int pitch; int staff; int layer;
    int channel; int program; int velocity; bool tieContinuation; bool
    expanded; }` (em `midifunctor.h`).
  - `void SetNoteLog(std::vector<MIDINoteRecord> *log)`; `nullptr` por padrão
    → zero mudança de comportamento no MIDI. Padrão do arquivo: as outras
    "opções de gravação" do functor já seguem esse molde (`SetDeferredNotes`,
    `SetTempoEventTicks`).
  - Em `VisitNote` (`midifunctor.cpp` L808), gravar **antes** dos `return
    FUNCTOR_SIBLINGS` de ligadura secundária (`GetScoreTimeTiedDuration() < 0`,
    L823-825 → `tieContinuation = true`, grava e retorna como hoje). Notas
    `HasSameasLink` (L813) e cue puladas (L818) não entram. `velocity == 0`
    (L827-828, silenciosa) não entra. Nota de trinado/tremolo
    (`m_expandedNotes`, ramo L842-851) entra **uma vez** com o pitch principal
    (`midiNote.pitch` da primeira entrada da sequência) e `expanded = true`.
  - `staff = m_staffN`, `layer = m_layerN`, `channel = m_midiChannel`,
    `program` = `m_instrDef && m_instrDef->HasMidiInstrnum() ?
    m_instrDef->GetMidiInstrnum() : 0`.
  - `Doc::ExportMIDI(smf::MidiFile *, std::vector<MIDINoteRecord> *noteLog =
    nullptr)` ganha o parâmetro e repassa o ponteiro (`generateMIDI.SetNoteLog(
    noteLog)`) para cada `GenerateMIDIFunctor` que cria no laço por
    pauta/camada (`doc.cpp` L608-L620) — mesmo objeto de log para todas, já
    que id de nota é único no documento expandido.
  - `Toolkit::RenderToBridgeJson`/`RenderToBridgeFile`: `SetMidiDoc()`, rodar
    `m_midiDoc->ExportMIDI(&scratchMidi, &log)` num `smf::MidiFile`
    descartado e serializar `log`. Repita nos **dois** lugares (L2092 e
    L2365) — não há um terceiro caminho que os unifique hoje.
- **Ids**: o `m_midiDoc` é o documento expandido; seus ids são exatamente os
  do timemap (inclusive `-rend<N>`).
- **Ligadura**: o timemap traz **toda** nota, inclusive a secundária, com
  on/off próprios. Com `tieContinuation`, o leitor (Dart, G02) junta a cadeia:
  soa do `on` da primeira até o `off` da última; o aluno aperta só a
  primeira. Para achar a cabeça da cadeia, grave também `tieHead`: o id da
  primeira nota (percorra `Tie::GetStart/GetEnd` — ver
  `InitTimemapTiesFunctor::VisitTie` `midifunctor.cpp` L313 — ou, mais
  simples, mantenha no functor um mapa `pitch+staff → id da última nota com
  ligadura aberta`; escolha e documente a escolhida nas notas de execução).
- **Formato proposto** (mesma regra de omissão do timemap/`meta`/`alternates`,
  §2.1/§9: sem notas, sem arquivo nem entrada no manifest; aditivo, `version`
  continua `1`):

  ```json
  { "notes": [
      {"id":"n1a2b","p":64,"s":1,"l":1,"c":0,"pg":0,"v":90},
      {"id":"n9f-rend2","p":52,"s":2,"l":1,"c":0,"pg":0,"v":90,"tie":"cont","th":"n77-rend2"},
      {"id":"n33","p":71,"s":1,"l":1,"c":0,"pg":0,"v":90,"orn":true}
  ]}
  ```
  Chaves curtas porque o corpus tem ~10 mil notas; campos com valor padrão
  podem ser omitidos se a spec disser (decida e documente na spec). Ordem:
  por id do timemap não é necessária — o leitor indexa por id.
- `manifest.files.notes = "notes.json"`; no JSON único, propriedade `notes`.
  `BridgeWriter::WriteManifest` (`bridgewriter.h` L102) ganha `bool hasNotes
  = false`; atualize as duas chamadas (`bridgewriter.cpp:678`,
  `toolkit.cpp:2431`) e o corpo (`bridgewriter.cpp` L622-644, mesmo padrão de
  `hasAlternates`/`hasDebug`).
- Atualize `docs/formato/especificacao-v1.md`: nova §2.7 (entre §2.6 modo
  debug e §3 unidades), linha nova em §2.1 (tabela `files`) e em §2.2 (JSON
  único), linha nova em **Histórico de revisões** com a data de execução —
  siga o tom das entradas de P02a/E01b (o que mudou, por que, se é aditivo).
  `docs/formato/schema-v1.json`: `$defs/notesDocument` (mesmo padrão de
  `$defs/timemapDocument`/`$defs/metaDocument`/`$defs/alternatesDocument`,
  `$defs` começa em L13), referência em `files`/`manifest`/raiz do JSON único
  (mesmo lugar de `timemap`/`meta`/`alternates`, ~L291-293 e ~L502-504).
- Saídas de teste em `compare/out/g01/`.

## O que fazer

1. `MIDINoteRecord` + `SetNoteLog` no `GenerateMIDIFunctor`; gravação em
   `VisitNote`; parâmetro em `Doc::ExportMIDI` repassado no laço de
   `doc.cpp`.
2. `BridgeWriter::WriteNotes` (novo, mesmo molde de `WriteMeta`/
   `WriteAlternates`) + `hasNotes` no manifest + os dois pontos de
   integração (`RenderToBridgeJson`/`WriteSingleJson` e `RenderToBridgeFile`).
3. Spec (§2.7 + tabelas de manifest/JSON único + histórico) e schema
   (`$defs/notesDocument`).
4. Script de verificação (Python 3 da máquina, sem dependências — leia o
   `.mid` com um parser mínimo ou use `verovio -t midi` + `mido` se estiver
   instalado; registre qual).

## Fora de escopo

- Qualquer código Dart (**G02**, no `score_bridge/` deste mesmo repo).
- Velocity de dinâmicas (`p`, `f`) — o Verovio não converte; fica
  `MIDI_VELOCITY` salvo `@vel` explícito.
- Pedal, CCs, andamento (o andamento já está no `tstamp` do timemap).

## Critérios de aceite

1. `verovio -t vsb` nas 10 peças do corpus gera `notes.json`; `-t svg` e os
   `scene.json`/`glyphs.json`/`timemap.json` ficam **byte-idênticos** aos de
   antes (compare com uma geração feita antes da mudança, ex.:
   `compare/out/s08/*.vsb` ou um `git stash` rápido).
2. Para cada peça: todo id em `timemap[].on` que é nota tem entrada em
   `notes.json` (exceto notas silenciosas/cue, contadas e listadas); nenhum
   id em `notes.json` fora do timemap.
3. **Pitch = MIDI**: o multiconjunto `(onset arredondado, pitch)` das notas
   **sem** `tie:"cont"` e sem `orn` bate com os note-on do `verovio -t midi`
   da mesma peça (onset em ms do timemap vs. tick convertido pelo andamento —
   ou compare só a sequência ordenada de pitches por pauta). Divergência zero
   no Chopin Étude e no Clair de Lune (8va).
4. Gymnopédie e Maple Leaf Rag: ids `-rend2` presentes com o mesmo pitch da
   passagem 1.
5. `score_bridge` (**G02**, ainda não escrito quando G01 roda) continua sem
   quebrar: um leitor que ignora arquivo extra no zip não é afetado — não é
   um critério a rodar aqui, só uma garantia de que G01 não obriga G02 a
   existir para o `.vsb` continuar válido.
6. Spec/schema atualizados; um `notes.json` do corpus valida contra o schema.

## Notas de execução

(preencher)
