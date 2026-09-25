# G02 — `score_bridge`: modelo e parser de `notes.json`

**Depende de:** G01 · **Decisão necessária:** não

> Este passo nasceu como **N02** no plano do host (`zywny/docs/plano/
> README.md` e `N02-notes-no-score-bridge.md`, cross-repo): lá o passo virou
> um ponteiro para aqui (modelo/parser) mais um item pequeno que continua no
> zywny (`just native` + rodar o app + conferir `document.notes`), porque
> `score_bridge/` é um pacote **deste** repo, não do zywny (o zywny só o usa
> por `path:` no `pubspec.yaml`).

## Objetivo

`VsbDocument.notes`: mapa `id (expandido) → NoteInfo`, lido de `notes.json`
quando o pacote o traz. Fixtures regeneradas.

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
  o parse. `notes` é pequeno (uma linha por nota: ~10 mil no corpus
  inteiro) — leia direto, mas **meça** o tempo de parse com
  `score_bridge/tool/measure_parse_time.dart` (roda com `flutter test`, não
  `dart run`) antes e depois e registre.
- Modelo sugerido (imutável, como o resto do `model.dart`):

  ```dart
  enum TieRole { none, start, continuation }   // start opcional: ver G01
  class NoteInfo {
    final String id;          // id expandido, igual ao timemap
    final int pitch;          // MIDI 0-127, já com 8va/transposição
    final int staff;          // n da pauta (1 = de cima; piano: 1 = MD, 2 = ME)
    final int layer;
    final int channel;        // 0-15
    final int program;        // 0-127 (GM)
    final int velocity;       // 1-127
    final TieRole tie;
    final String? tieHead;    // id da 1ª nota da cadeia, se continuation
    final bool ornament;      // trinado/tremolo expandido no MIDI
  }
  // VsbDocument:
  final Map<String, NoteInfo> notes;   // vazio quando não há notes.json
  ```
- Fixtures em `score_bridge/test/fixtures/` (`erik-satie.vsb`,
  `maple-leaf-rag.vsb`, `mazurka.vsb` e as de `repeticoes/`): regenere com o
  CLI de G01 usando **as mesmas flags** com que foram geradas (procure nas
  notas de P01c/P04c/P05 deste plano, ex.: `-x 42` = `--xml-id-seed 42`).
  Confira com `git diff --stat` que só mudou o que devia.

## O que fazer

1. `NoteInfo`, `TieRole`, `VsbDocument.notes`, parser (zip e JSON único),
   exports.
2. Regenerar fixtures.
3. Testes: parse de fixture; nota ligada; id `-rend2`; pacote sem
   `notes.json` → mapa vazio sem erro; `notes.json` malformado → erro com
   caminho.

## Fora de escopo

- Juntar com o timemap em eventos tocáveis: fica no zywny (`N03`,
  `PerformanceTrack`), fora deste repo.
- Refazer a `libverovio.so`/rodar o app do zywny: item próprio do plano do
  host (`N02` de lá, depois deste passo concluído).

## Critérios de aceite

1. `cd score_bridge && flutter test` verde, com os testes novos.
2. Para cada fixture com timemap: todo id de nota em `timemap[].on` tem
   `NoteInfo` (mesma regra de exceções de G01).
3. Tempo de parse antes/depois registrado (mesma peça, mesma máquina).

## Notas de execução

(preencher)
