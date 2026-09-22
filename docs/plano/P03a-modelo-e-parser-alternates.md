# P03a — Dart: modelo, parser e geometria das sequências alternativas

**Depende de:** P02a (contrato), P02c (fixtures reais para os critérios) ·
**Decisão necessária:** não

## Objetivo

O `score_bridge` passa a ler `alternates.json` e a endereçar qualquer página,
normal ou alternativa, por um **`PageRef`**. Nada visual muda neste passo.
Todo código que hoje usa `document.pages[i]` continua funcionando igual.

## Ler antes (só isto)

- `docs/plano/P00-visao-geral-paginas-alternativas.md`.
- `docs/formato/especificacao-v1.md` §2.5 (escrita em P02a).
- `score_bridge/lib/src/model.dart`: `VsbDocument` (L106-L160) e
  `VsbManifest`.
- `score_bridge/lib/src/parser.dart`: `parseVsbDocumentBytes` (L64-L100),
  `parseVsbDocumentJson` (L114) e `parseSceneDocument`.
- `score_bridge/lib/src/hit_test.dart`: `ElementRef`, `ScoreGeometry`
  (L60-L220).
- `score_bridge/lib/score_bridge.dart` (API pública).

## Contexto que você precisa (não vá procurar, está aqui)

- `ScoreGeometry(document)` hoje percorre `document.pages`, monta `_byId`
  (id → primeira ocorrência) e `_byPage`, e resolve ids expandidos por
  `document.sceneIdOf`. Numa alternativa, os mesmos ids aparecem de novo, de
  propósito. Por isso a geometria tem que ser **por sequência**: misturar
  tudo num `_byId` só faria `elementOf` devolver a página errada.
- `VsbDocument._expansion` (regra do sufixo) é montado com os ids das páginas
  normais. As alternativas não trazem id de nota novo (P02c, critério 2),
  então a expansão continua certa sem mudança.
- `ScenePage.index` numa alternativa é o índice **dentro da sequência**.
- Parse: as alternativas podem pesar tanto quanto `scene.json` ou mais.
  Parse **preguiçoso** (guardar os bytes/JSON bruto e só montar na primeira
  consulta a `alternates`) é bem-vindo, mas não obrigatório. Meça antes de
  decidir (critério 4).

## O que fazer

1. `model.dart`:
   - `@immutable class PageRef { const PageRef(this.index, {this.sequence});
     final int? sequence; final int index; }`, com `==`, `hashCode`,
     `toString` e o getter `bool get isAlternate => sequence != null`.
     `sequence == null` é a página normal.
   - `class AlternateSequence { final String start; final List<ScenePage>
     pages; late final ScoreGeometry geometry; }`.
   - `VsbDocument.alternates` (`List<AlternateSequence>`, vazia quando não
     há arquivo) e `VsbManifest.files.alternates` (opcional).
   - `ScenePage pageAt(PageRef ref)`, `ScoreGeometry geometryOf(int?
     sequence)` e `AlternateSequence? alternateStartingAt(String measureId)`.
2. `parser.dart`: ler `alternates.json` (zip) ou a propriedade `alternates`
   (JSON único) com o **mesmo** `parseSceneDocument`/parse de página. Erros
   com caminho (`alternates.sequences[2].pages[0]...`), como os demais.
3. `hit_test.dart`: `ScoreGeometry` passa a poder ser montada sobre uma lista
   de páginas qualquer (`ScoreGeometry.forPages(pages, sceneIdOf: ...)`),
   mantendo `ScoreGeometry(document)` como está (as páginas normais).
   `ElementRef.page` continua sendo o índice **dentro da sua sequência**.
4. Exporte `PageRef` e `AlternateSequence` em `score_bridge.dart`.

## Fora de escopo

- Desenhar uma página alternativa (P03b).
- Qualquer regra de quando usar uma alternativa (P04a).

## Critérios de aceite

1. Fixture `maple-leaf-rag.vsb` regenerada com alternativas (P02c, `-x 42`):
   `alternates.length` = número de sequências medido em P02c, e para cada
   sequência a página 0 tem `start` como primeiro nó `measure`.
2. `document.pages`, `document.geometry` e toda a suíte atual: **nenhum**
   teste muda. Um `.vsb` sem `alternates.json` dá `alternates` vazia.
3. `geometryOf(k).elementOf(<nota do trecho>)` devolve a página e a bbox
   **da sequência k**, diferentes das normais (teste com uma nota do compasso
   `start`: na alternativa, ela está na página 0).
4. Tempo de parse (`tool/measure_parse_time.dart`) com e sem alternativas,
   nas peças com repetição, registrado nas notas. Se passar de 2× o tempo
   sem alternativas, implemente o parse preguiçoso e meça de novo.
5. `exemplo-alternates.json` (P02a) parseia.
6. `flutter analyze` limpo, `flutter test` verde.

## Notas de execução

_(preencher)_
