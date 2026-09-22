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

**`model.dart`:** `PageRef` (`@immutable`, `index` + `sequence` opcional,
`isAlternate`, `==`/`hashCode`/`toString`) e `AlternateSequence` (`start` +
`pages`, com sua própria `IdExpansion`/`ScoreGeometry` montadas só sobre as
páginas da sequência — não a do documento inteiro, de propósito: a mesma
nota existe em mais de uma sequência e nas páginas normais, então
`elementOf` só faz sentido "dentro de um escopo"). `VsbDocument.alternates`,
`pageAt(PageRef)`, `geometryOf(int?)`, `alternateStartingAt(String)`.
`VsbManifestFiles.alternates` (opcional).

**`hit_test.dart`:** `ScoreGeometry` deixou de guardar `VsbDocument` e passou
a guardar `List<ScenePage> pages` + `String? Function(String)? sceneIdOf`
diretamente — `ScoreGeometry(document)` agora só redireciona para o
construtor novo `ScoreGeometry.forPages(document.pages, sceneIdOf:
document.sceneIdOf)`. `sceneIdOf` é campo público (não `_sceneIdOf`)
porque `AlternateSequence` (outra biblioteca, `model.dart`) precisa passá-lo
por nome no construtor nomeado — um campo privado não pode ser um parâmetro
nomeado através de fronteira de biblioteca, o que o lint
`prefer_initializing_formals` não sabe (achado ao tentar seguir a sugestão
dele: quebra a chamada cross-library; resolvido tornando o campo público em
vez de forçar `this._sceneIdOf` ou silenciar o lint).

**`parser.dart`:** `parseAlternatesDocument`/`_parseAlternateSequence`,
reusando `_parseScenePage` (a mesma função de `scene.json`, §5) — nenhuma
duplicação de serialização. Caminho de erro no formato pedido:
`alternates.sequences[K].pages[N]...`.

**Parse preguiçoso (critério 4, medido antes de decidir).** Medi primeiro
com parse ansioso: nas 6 peças com repetição, só a Maple Leaf Rag (8
sequências) passou de 2× — 410 ms vs. 89 ms sem alternativas (4,6×);
Mazurka 98/59 ms (1,65×), Little bird 66/38 ms (1,72×), Gymnopédie 20/18 ms
(1,15×) ficaram abaixo do limite. Implementei o parse preguiçoso pedido
pelo critério: `VsbDocument.alternates` é `late final`, inicializado por um
`_alternatesLoader` (closure) que só o parser preenche; no caminho do zip,
o closure adia `readBytes()` + `json.decode` + `parseAlternatesDocument`
inteiros (o zip já trouxe os bytes comprimidos para memória em
`ZipDecoder.decodeBytes`, mas não descomprime/decodifica cada entrada até
`readBytes()`); no JSON único, adia só a montagem da árvore (o `Map` já
estava decodificado). Depois do parse preguiçoso: Maple Leaf Rag 84 ms
(igual ao "sem alternativas", dentro do ruído da medição) — as 6 peças
ficaram todas a ≤1,04× do tempo sem alternativas. `VsbDocument(...,
alternates: [...])` continua aceito (constrói o loader como uma closure que
devolve a lista dada), para não quebrar construção direta em teste; o
parser usa `alternatesLoader:` para adiar de verdade.

**Critério 1.** `maple-leaf-rag.vsb` regenerado com `-x 42` sobre o binário
de P02c (8 sequências, como medido lá). `doc.alternates.length == 8`; cada
`sequence.pages.first` tem `sequence.start` como o 1º nó de classe
`measure` em pré-ordem (checado com uma reimplementação da regra só para o
teste, não a de produção).

**Critério 2.** `flutter test` inteiro — 278/278 verdes, nenhum teste
mudou de expectativa (só os 8 novos de `alternates_test.dart` foram
adicionados). `erik-satie.vsb` (fixture de antes de P02c, sem
`alternates.json`) dá `alternates` vazia e `manifest.files.alternates ==
null`, com `pages`/`geometry` intactos.

**Critério 3.** `geometryOf(0).elementOf('m15xbieh')` (1ª nota da página 0
da sequência 0, que começa no compasso `q1t6l0ej`) devolve página 0 **da
sequência**; comparado com `geometry.elementOf` (páginas normais) para
confirmar que não é a mesma entrada por acidente.

**Critério 5:** `docs/formato/exemplo-alternates.json` (P02a) parseia:
1 sequência, `start: "m5"`, 1 página, 1º `measure` é `m5`.

**Critério 6:** `flutter analyze` limpo (0 avisos, depois de resolver o
achado do lint acima); `flutter test` 278/278.
