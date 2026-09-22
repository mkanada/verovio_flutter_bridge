# E01a — Corpus de repetições e roteiro esperado

**Depende de:** A05b · **Decisão necessária:** não

## Objetivo

Dar ao resto da fase E um **alvo verificável**: um punhado de partituras
mínimas com cada tipo de repetição, a **sequência de compassos que um músico
tocaria** em cada uma (escrita à mão, a partir da partitura, nunca do Verovio)
e um script que imprime a sequência que o `.vsb` realmente toca e compara as
duas. Este passo **não muda código de produção**: mede o estado atual.

## Ler antes (só isto)

- `score_bridge/lib/src/score_timeline.dart` (`_build`, L115): como a
  sequência de compassos sai hoje do timemap + cena.
- `verovio/src/expansionmap.cpp`: `GenerateExpansionFor` (L367) e
  `GeneratePredictableIDs` (L340).
- `verovio/src/iomusxml.cpp`: `CreateExpansion` (L1322).

## Contexto que você precisa (não vá procurar, está aqui)

**Como uma repetição chega ao `.vsb`.** A cena é desenhada do documento
**notado** (sem expansão). O timemap vem de outro documento, o `m_midiDoc`
(`Toolkit::SetMidiDoc`, `toolkit.cpp` L283): uma cópia reimportada do MEI com
`expandAlways`, que passa por `Doc::ExpandExpansions` (`doc.cpp` L1660). A
expansão **clona** cada trecho repetido, e cada clone ganha o id
`<id original>-rend<N>` (`ExpansionMap::GeneratePredictableIDs`), com `N = 2,
3, …` = a N-ésima execução daquele elemento. Na cena só existe o original.

**De onde vem a expansão:**

- **MusicXML**: `MusicXmlInput::CreateExpansion` monta um `<expansion>` a partir
  de `<repeat>`, `<ending>` e `<sound dacapo/dalsegno/tocoda/fine>`, incluindo
  `times`.
- **MEI**: usa um `<expansion>` codificado, ou gera um com
  `ExpansionMap::GenerateExpansionFor` a partir das barras `rptstart`/`rptend`/
  `rptboth`. Esse gerador **recusa** partituras com mais de uma `<section>`
  (log: `An expansion cannot be generated with more than one section`) e com
  conteúdo editorial, e **ignora `<ending>`** (só olha os `measure` filhos
  diretos da `section`).

**Medido no corpus em 2026-09-21** (índices de compasso em ordem de documento,
base 1):

| Peça | Formato | Marcação | Verovio hoje | Ocorrências de compasso: hoje → esperado |
| --- | --- | --- | --- | --- |
| Gymnopédie | MusicXML | 1 ritornelo, casas 1 (32-39) e 2 (40-47) | **correto** | 78 → 78 (31 na 2ª passagem) |
| Maple Leaf Rag | MusicXML | 4 ritornelos, 4 casas 1, 3 casas 2 | **perde o 1º ritornelo** (casa 1 no compasso 17 sem casa 2) | 130 → 145 |
| Mazurka Op. 6 nº 1 | MEI, 3 `section` | `rptend` 17, `rptstart` 18, `rptend` 42 | **não expande** | 75 → 117 |
| Butterfly | MEI, 2 `section` | `rptend` 6 | **não expande** | 42 → 48 |
| Little bird | MEI, 3 `section` | `rptend` 9, `rptstart` 10, `rptend` 30 | **não expande** | 39 → 69 |
| Scarlatti | MEI, 2 `section` | `rptend` 31 | **não expande** | 68 → 99 |
| Étude, Nocturne, Clair de Lune, Prelude | — | nenhuma | — | = nº de compassos |

(`section` contadas só na partitura. Cada arquivo MEI tem mais uma, a do
`<incip>` no `meiHead`, que o gerador não vê. A Étude, também MEI, tem uma
só.)

O corpus **não tem** D.C., D.S., coda, fine, `times` nem casas em MEI: por
isso as partituras mínimas abaixo existem.

**Ids estáveis.** O importador de MusicXML sorteia ids a cada execução (duas
chamadas ao `verovio` dão ids diferentes, a menos que se use
`--xml-id-seed`), mas respeita `<measure id="…">` (`iomusxml.cpp` L1881) e o
`id` das notas (L3113). Nas partituras mínimas, dê ids explícitos: compassos
`m1`…`mN` em ordem de documento e notas `m1n1`, `m1n2`… Assim a sequência
esperada se escreve com os números dos compassos.

**Quebra de página controlada.** Para os casos de salto entre páginas use
`<print new-page="yes"/>` (MusicXML) ou `<pb/>` (MEI) e gere com
`--breaks encoded`.

**Timemap com compassos.** `-t timemap --timemap-options
'{"includeMeasures":true}'` preenche `measureOn` com o id do compasso (com
`-rendN` nas repetições). Na Gymnopédie dá 78 entradas com `measureOn`, 31
delas `-rend2`, que é exatamente a sequência derivada das notas. O `.vsb` de
hoje **não** traz `measureOn` (E01b muda isso).

## O que fazer

1. Criar `corpus/repeticoes/` com as partituras mínimas (uma pauta, semínimas,
   4 a 12 compassos, ids explícitos):

   | Arquivo | Caso | Sequência esperada |
   | --- | --- | --- |
   | `r01-ritornelo.musicxml` | ‖: 1-4 :‖ 5-6 | `1-4 1-4 5-6` |
   | `r02-ritornelo.mei` | o mesmo, MEI com uma `section` | `1-4 1-4 5-6` |
   | `r03-casas.musicxml` | ‖: 1-3 [1. 4] :‖ [2. 5] 6 | `1-4 1-3 5-6` |
   | `r04-casas.mei` | o mesmo, MEI com `<ending>` e sem `<expansion>` | `1-4 1-3 5-6` |
   | `r05-casa-1-sozinha.musicxml` | como r03, mas só a casa 1 marcada (o padrão da Maple Leaf Rag) | `1-4 1-3 5-6` |
   | `r06-salto-de-pagina.musicxml` | ‖: 1-4 ⏎página 5-8 :‖ 9-10 | `1-8 1-8 9-10` |
   | `r07-salto-de-pagina.mei` | o mesmo em MEI (uma `section`, `<pb/>`) | `1-8 1-8 9-10` |
   | `r08-dc-al-fine.musicxml` | 1-4, Fine no fim do 2, D.C. no fim do 4 | `1-4 1-2` |
   | `r09-ds-al-coda.musicxml` | 1, segno no 2, To Coda no 3, D.S. no 4, coda 5-6 | `1-4 2-3 5-6` |
   | `r10-tres-vezes.musicxml` | ‖: 1-2 :‖ `times="3"`, 3 | `1-2 1-2 1-2 3` |
   | `r11-varias-sections.mei` | o padrão do corpus MEI: `section` 1-4 com `rptend`, `section` 5-8 com `rptstart`/`rptend`, 9 | `1-4 1-4 5-8 5-8 9` |
   | `r12-expansion-codificada.mei` | ‖: 1-2 :‖ 3 com dois `<expansion>` (com e sem repetição) | `1-2 1-2 3` (padrão) e `1-3` com `--expand <id da segunda>` |
   | `r13-um-compasso.musicxml` | ‖: 1 :‖ 2, **a mesma nota** no fim e no começo do 1 | `1 1 2` |

   Escreva cada sequência esperada num `<arquivo>.esperado` ao lado da
   partitura (uma linha, formato da tabela). Para as 10 peças do corpus, crie
   `corpus/repeticoes/esperado/<peça>.esperado`, derivado **da marcação** da
   partitura (a tabela do contexto traz as contagens; a sequência exata é
   sua).

2. Criar `compare/scripts/repeat-order.py`:

   ```
   repeat-order.py <partitura | .vsb> [--expected <arquivo>] [-- <opções do verovio>]
   ```

   - Com uma partitura, gera o `.vsb` em `compare/out/e01/` (`-t vsb
     --breaks encoded` para as partituras mínimas, mais as opções extras).
   - Lê do `.vsb` a cena (compassos em ordem de documento e a página de cada
     um) e o timemap.
   - Monta as **ocorrências de compasso**: por `measureOn`, quando existir;
     senão, pelas notas de `on`, tirando o `-rendN` para achar o nó da cena e
     usando o `N` como passagem (uma ocorrência nova sempre que o par
     compasso/passagem muda).
   - Imprime a sequência em blocos (`1-4 1-4 5-6`), o número de ocorrências e
     quantas estão em cada passagem, e a lista de saltos (ocorrência cujo
     compasso não é o seguinte do anterior na ordem de documento), com a
     página de origem e a de destino.
   - Com `--expected`, compara as duas e sai com código 1 se forem diferentes,
     mostrando a primeira divergência.

3. Rodar o script em tudo (13 partituras mínimas + 10 peças) e registrar a
   tabela "caso × resultado" nas notas de execução: correto, ou o que o
   Verovio tocou no lugar e quais avisos apareceram no log.

## Fora de escopo

- Corrigir qualquer coisa (E01b, E02, E04).
- Casos que não aparecem na tabela (repetição aninhada, `<ending>` com várias
  casas numa só, MEI com `repeatMark@func`). Anote, se encontrar, e não
  resolva aqui.

## Critérios de aceite

1. As 13 partituras mínimas e os 23 arquivos `.esperado` existem. Cada
   partitura mínima gera `.vsb` sem erro, e um PNG de cada uma (SVG do
   Verovio → `svg_render`) mostra os sinais de repetição no lugar certo:
   anexe os PNGs em `compare/out/e01/`.
2. O script reproduz os números conhecidos: Gymnopédie com 78 ocorrências (31
   na 2ª passagem, salto `39 → 1` na página 0) e Maple Leaf Rag com 130 (45
   na 2ª passagem, saltos `34 → 19` da página 1 para a 0, `67 → 52` da
   página 2 para a 1 e `83 → 69` na página 2).
3. A tabela "caso × resultado" das 23 entradas está nas notas de execução. Os
   números "hoje" da tabela de contexto ou batem, ou foram corrigidos neste
   arquivo **e** no README.
4. `git diff --stat` não mostra mudança em `verovio/src`, `verovio/include`
   nem `score_bridge/lib`.

## Notas de execução

_(preencher ao executar)_
