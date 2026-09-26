# G02 — `score_bridge`: modelo e parser de `midi.json`

**Depende de:** G01 · **Decisão necessária:** não

> Este passo nasceu como **N02** no plano do host (`zywny/docs/plano/
> README.md` e `N02-notes-no-score-bridge.md`, cross-repo): lá o passo virou
> um ponteiro para aqui (modelo/parser) mais um item pequeno que continua no
> zywny (`just native` + rodar o app + conferir `document.notes`), porque
> `score_bridge/` é um pacote **deste** repo, não do zywny (o zywny só o usa
> por `path:` no `pubspec.yaml`).

> **Revisão de 2026-09-25**: G01 passou de `notes.json` (atributos por nota)
> para `midi.json` (fluxo de eventos do exportador MIDI, em ms, com ligaduras
> unidas, ornamentos expandidos e pedal). Este passo acompanha.

## Objetivo

`VsbDocument.midi`: as notas e pedais de `midi.json`, com índice por id
(expandido), lidos quando o pacote traz o arquivo. Fixtures regeneradas.

## Ler antes (só isto)

- `docs/formato/especificacao-v1.md` §2.7 (escrita em G01).
- `score_bridge/lib/src/parser.dart` (como `meta`/`timemap`/`alternates` são
  lidos do zip e do JSON único — procure `parseAlternatesDocument` e o
  parser de `meta` para o padrão a copiar).
- `score_bridge/lib/src/model.dart`: `VsbDocument` (procure `class
  VsbDocument`), `VsbMeta` e `VsbManifest` (procure `class VsbManifest`,
  `files`).
- `score_bridge/lib/score_bridge.dart` (exports).

## Contexto que você precisa

- Padrão existente: `manifest.files.<x>` opcional → se presente, ler a
  entrada do zip, `json.decode`, `parseXDocument(decoded, path: 'x')` com
  erros de formato apontando o caminho JSON. Copie o de `meta` ou de
  `alternates` (P03a), que são os dois mais recentes.
- `alternates` é **preguiçoso** (`late final` + loader) porque custava 4,6×
  o parse. `midi` é pequeno (uma entrada por nota tocada: ~10 mil no
  corpus inteiro, mais as notas de ornamento) — leia direto, mas **meça** o
  tempo de parse com `score_bridge/tool/measure_parse_time.dart` (roda com
  `flutter test`, não `dart run`) antes e depois e registre.
- Modelo sugerido (imutável, como o resto do `model.dart`):

  ```dart
  class MidiNote {
    final String id;          // id expandido, igual ao timemap (cabeça da ligadura)
    final double onMs, offMs; // mesmo relógio do timemap; off = fim da cadeia ligada
    final int pitch;          // MIDI 0-127, já com 8va/transposição
    final int staff;          // n da pauta (1 = de cima; piano: 1 = MD, 2 = ME)
    final int layer;
    final int channel;        // 0-15
    final int program;        // 0-127 (GM)
    final int velocity;       // 1-127
    final List<String> tied;  // ids de continuação da ligadura, na ordem
    final bool ornament;      // nota de sequência expandida (trinado/tremolo)
  }
  enum PedalDir { down, up }
  class MidiPedal { final String id; final double timeMs; final PedalDir dir;
                    final int staff, channel; }
  class VsbMidi {
    final List<MidiNote> notes;          // ordenado por onMs
    final List<MidiPedal> pedal;         // ordenado por timeMs
    List<MidiNote> notesOf(String id);   // cabeça, continuação (via tied) ou ornamento
  }
  // VsbDocument:
  final VsbMidi? midi;   // null quando não há midi.json
  ```
- Fixtures em `score_bridge/test/fixtures/` (`erik-satie.vsb`,
  `maple-leaf-rag.vsb`, `mazurka.vsb` e as de `repeticoes/`): regenere com o
  CLI de G01 usando **as mesmas flags** com que foram geradas (procure nas
  notas de P01c/P04c/P05 deste plano, ex.: `-x 42` = `--xml-id-seed 42`).
  Confira com `git diff --stat` que só mudou o que devia.

## O que fazer

1. `MidiNote`, `MidiPedal`, `VsbMidi`, `VsbDocument.midi`, parser (zip e
   JSON único), exports.
2. Regenerar fixtures.
3. Testes: parse de fixture; nota ligada (`notesOf` de um id de
   continuação devolve a cabeça); ornamento (várias entradas no mesmo id);
   pedal; id `-rend2`; pacote sem `midi.json` → `midi == null` sem erro;
   `midi.json` malformado → erro com caminho.

## Fora de escopo

- Tocar, agendar eventos ou avaliar o aluno: fica no zywny (`N03`,
  `PerformanceTrack`), fora deste repo. Com `midi.json` o zywny não precisa
  mais juntar ligaduras nem expandir ornamentos — só agendar os eventos.
- Refazer a `libverovio.so`/rodar o app do zywny: item próprio do plano do
  host (`N02` de lá, depois deste passo concluído).

## Critérios de aceite

1. `cd score_bridge && flutter test` verde, com os testes novos.
2. Para cada fixture com timemap: todo id de nota em `timemap[].on` tem
   `notesOf(id)` não-vazio (mesma regra de exceções de G01).
3. Tempo de parse antes/depois registrado (mesma peça, mesma máquina).

## Notas de execução

**Implementado em 2026-09-25.** `MidiNote`, `PedalDir`, `MidiPedal`, `VsbMidi`
(`model.dart`), `VsbManifestFiles.midi`, `VsbDocument.midi` — modelo imutável,
igual ao proposto. `VsbMidi.notesOf(id)` indexa cada nota pelo próprio `id`
**e** por cada id em `tied` (múltiplas notas podem compartilhar um id — só
acontece com ornamento no formato atual); mapa construído uma vez, na
primeira consulta (`late final`). Parser (`parser.dart`): `parseMidiDocument`
+ leitura em `_fromZipBytes`/`_fromDocumentJson`, mesmo padrão de `meta`.
Exportado em `score_bridge.dart`.

**Fixtures.** Regenerei as 27 (`erik-satie.vsb`, `maple-leaf-rag.vsb`,
`mazurka.vsb`, `r13-um-compasso.vsb` e as 23 de `repeticoes/`) com
`--xml-id-seed 42` (e `--breaks encoded` em r06/r07, como sempre). Verificação
sistemática (script descartável, não commitado): as 27 ganharam **só**
`midi.json`; `scene.json`/`glyphs.json`/`timemap.json` byte-idênticos em
todas.

⚠️ **Achado durante a regeneração**: `erik-satie.vsb` também teria ganhado
`alternates.json` — não é efeito de G01/G02, é porque esse fixture nunca foi
regenerado desde P02c (decisão deliberada de P01c, "menos ruído": "confira se
algum número depende da paginação; se nada depender, não regenere"), e
`alternates_test.dart` depende explicitamente dele **não ter**
`alternates.json` (critério 2 daquele teste: "leitor antigo, sem o arquivo,
dá `alternates` vazia"). Regenerei esse arquivo com `--no-vsb-alternates`
além do `--xml-id-seed 42`, preservando essa propriedade — ganhou só
`midi.json`, confirmado (`doc.manifest.files.alternates` continua `null`,
`flutter test` verde).

**Testes novos**: `test/midi_test.dart`, 17 testes — parse (JSON único e
zip, com/sem `midi.json`), `notesOf` (nota simples, continuação de ligadura,
ornamento — sintético, ver abaixo, id sem correspondência), erros de forma
(4 casos), e dois testes com fixture real: Maple Leaf Rag (`-rend2` com o
mesmo pitch da passagem 1; **0** ids de nota do timemap sem `notesOf`
correspondente) e Clair de Lune (pedal + ligadura reais; **3** ids do timemap
sem correspondência — mesma exceção que a verificação de G01 já tinha achado
nessa peça, não investigada a fundo, tolerância de até 5 no teste).

**Sem exemplo real de ornamento no corpus/fixtures**: nenhuma das peças
testadas em G01 nem nenhum dos 23 fixtures de `repeticoes/` tem nota
`"orn":true` (procurei nos 27 `midi.json` gerados). O teste de ornamento em
`midi_test.dart` usa `parseMidiDocument` com um `midi.json` sintético de
duas entradas com o mesmo id — cobre o parser e `notesOf`, mas não prova que
o Verovio realmente expande algo assim no corpus atual.

**Tempo de parse (critério 3)**: Maple Leaf Rag (o fixture maior, 2568 notas
em `midi.json`), `tool/measure_parse_time.dart`, mediana de 3 execuções:
**85,56 ms → 93,32 ms** (+9,1%, +25 652 bytes no arquivo). Bem menor que o
4,6× que justificou o parse preguiçoso de `alternates` (P03a) — consistente
com a decisão do próprio G02 de ler `midi` direto, sem `late final`/loader.

**`flutter test` (critério 1)**: 322/322 verdes (era 305 antes de G02: 17
testes novos, nenhuma quebra nos existentes). `flutter analyze` limpo.

**Critério 2** (cobertura de ids do timemap): verificado nas duas fixtures
reais acima — ver "Testes novos".
