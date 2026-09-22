# P02b — C++: pontos de chegada das repetições

**Depende de:** P01c, P02a · **Decisão necessária:** não

## Objetivo

No exportador, calcular a **lista de compassos de chegada** que ganham
sequência alternativa (regra normativa de §2.5 da spec, escrita em P02a). É
uma função pura e testável. Nada é renderizado ainda (P02c).

## Ler antes (só isto)

- `docs/plano/P00-visao-geral-paginas-alternativas.md`, seção "Exportador
  (C++)".
- `docs/formato/especificacao-v1.md` §2.4 (regra do sufixo) e §2.5.
- `verovio/src/toolkit.cpp`: `Toolkit::RenderToBridgeFile` (L2114), em
  especial a chamada `RenderToTimemap("{\"includeMeasures\": true}")`.
- `verovio/include/vrv/timemap.h` (a estrutura das entradas, com
  `measureOn`).
- `score_bridge/lib/src/score_timeline.dart`, `_build` (a definição de salto,
  `isJump`, é a referência que o C++ tem que reproduzir).
- A tabela "Saltos e pontos de chegada (P01c)" do README do plano.

## Contexto que você precisa (não vá procurar, está aqui)

- Ordem de documento dos compassos: `m_doc.FindAllDescendantsByType(MEASURE,
  false)` na ordem retornada (é o que `Doc::PrepareMeasureIndices` numera).
  Use o índice na lista, não o `@n`.
- Página normal de um compasso: `measure->GetFirstAncestor(PAGE)` e o índice
  da página em `m_doc.GetPages()`. O 1º compasso de cada página é o primeiro
  `MEASURE` descendente dela.
- O timemap já é gerado dentro de `RenderToBridgeFile`. Prefira ler a
  estrutura do `Timemap` direto (sem reparsear JSON) se o `Toolkit` tiver
  acesso a ela. Se só houver o JSON, parsear com `jsonxx` (já incluído no
  `toolkit.cpp`) é aceitável.
- Regra do sufixo (§2.4): o id existe no `Doc` → é ele; senão, casa com
  `^(.*)-rend([0-9]+)$` e a base existe → a base; senão, ignore a entrada.
- Arquivo novo: `src/bridgealternates.cpp` + `include/vrv/bridgealternates.h`.
  **Rode `cmake ../cmake` de novo** antes do `make` (o CMake coleta por glob).
  Estilo do `svgdevicecontext.cpp` (namespace `vrv`, cabeçalho, `//----`).

## O que fazer

1. Em `bridgealternates.h/.cpp`, uma função pura, sem `Doc`:

   ```cpp
   // executionOrder: ids de compasso (já resolvidos ao id notado), em ordem de execução.
   // docOrder: id -> posição na ordem de documento.
   // firstOfNormalPage: ids que são o 1º compasso de alguma página normal.
   // Devolve os pontos de chegada, sem repetição, em ordem de documento.
   std::vector<std::string> FindAlternateStarts(const std::vector<std::string> &executionOrder,
       const std::map<std::string, int> &docOrder, const std::set<std::string> &firstOfNormalPage);
   ```

2. No `Toolkit`, um método privado que monta as três entradas a partir do
   `Doc` e do timemap e chama a função.
3. Exposição para teste (temporária ou permanente, você escolhe e registra):
   um modo de depuração da CLI que imprime os pontos de chegada em JSON, por
   exemplo `-t vsb-json` gravando uma chave `"_alternateStarts"` **só** quando
   a opção nova de depuração estiver ligada. **Não** mude o `.vsb` normal
   neste passo.

## Fora de escopo

- `Select`, renderização, `alternates.json` (P02c).

## Critérios de aceite

1. Para as 6 peças com repetição e as 13 partituras de E01a
   (`corpus/` + fixtures de `score_bridge/test/fixtures/repeticoes/` e suas
   fontes), a lista de pontos de chegada bate com a derivada da tabela
   "Saltos e pontos de chegada (P01c)" (destinos que não são 1º compasso de
   página, sem repetição). Tabela nas notas: peça, esperados, obtidos.
2. Peças sem repetição (Étude, Nocturne, Clair de Lune, Prelude): lista
   vazia.
3. A sequência `executionOrder` montada no C++ é **igual** à de
   `ScoreTimeline.measures` (ids) do Dart nas 23 fixtures. Escreva um teste
   Dart pequeno ou um script que compare as duas saídas.
4. `.vsb` sem a opção de depuração: byte-idêntico ao de P01c nas 10 peças.
5. Build do Verovio sem avisos novos.

## Notas de execução

**Arquivos novos.** `verovio/include/vrv/bridgealternates.h` +
`verovio/src/bridgealternates.cpp`: `BridgeAlternates::FindAlternateStarts`,
função pura (sem `Doc`) exatamente com a assinatura do passo. No `Toolkit`
(`toolkit.h`/`toolkit.cpp`), três métodos privados novos:

- `ComputeMeasureDocOrder()` — `xml:id` de compasso → posição em
  `m_doc.FindAllDescendantsByType(MEASURE, false)`;
- `ComputeMeasureExecutionOrder(docOrder)` — lê `RenderToTimemap({"includeMeasures":
  true})`, aplica a regra do sufixo (§2.4) a cada `measureOn` e monta a
  sequência de ids resolvidos, uma por ocorrência;
- `ComputeAlternateStarts()` — monta `firstOfNormalPage` (1ª `MEASURE`
  descendente de cada `Page`) e chama `BridgeAlternates::FindAlternateStarts`
  com os três.

Nenhum dos três mexe no `.vsb`/`vsb-json` normal.

**Depuração (item 3).** Opção nova `--debug-alternate-starts`
(`m_debugAlternateStarts`, `options.h`/`options.cpp`, grupo geral). Só
`Toolkit::RenderToBridgeJson` a lê: quando ligada, costura duas chaves a
mais no JSON de saída — `_executionOrder` (a sequência completa, útil para
o critério 3) e `_alternateStarts` (o resultado final) — por fora do
`BridgeWriter` de propósito (não é o formato documentado; `alternates.json`
de verdade é P02c). `-t vsb` nunca ganha essas chaves, com ou sem a opção.

**Critério 1** (23 fontes: 10 peças do corpus + 13 partituras de E01a,
`--xml-id-seed 42`, `--breaks encoded` extra em r06/r07). Comparei a saída
de `--debug-alternate-starts` contra uma derivação independente em Python
reaproveitando `SceneIndex`/`find_jumps` de `compare/scripts/repeat-order.py`
(gera `.vsb`, lê `scene.json`+`timemap.json`, acha os saltos e filtra os que
já são 1º compasso de alguma página) — **23/23 batem exatamente**, incluindo
a ordem (o resultado já sai em ordem de documento dos dois lados). Tabela:

| Peça/partitura | Pontos de chegada obtidos |
| --- | --- |
| Chopin Étude Op.10 No.9 | `[]` |
| Chopin Mazurka Op.6 No.1 | `['d1e3853']` |
| Grieg Butterfly Op.43 No.1 | `[]` |
| Grieg Little bird Op.43 No.4 | `['d418889e2505']` |
| Scarlatti Sonata in C major | `[]` |
| Chopin Nocturne Op.9 No.1 | `[]` |
| Clair de Lune, Debussy | `[]` |
| Erik Satie Gymnopédie No.1 | `['lkh51fy']` |
| Maple Leaf Rag, Joplin | `['q1t6l0ej', 'ock08kg', 'qqplm6a', 'qhi6f7l', 'y12vaz72', 'm1bcumr2', 'jn8k16x', 'd132vz0f']` (8) |
| Prelude I BWV 846 | `[]` |
| r01-r02 (ritornelo) | `[]` (o destino, compasso 1, já é a 1ª página) |
| r03-r05 (casas) | `['m5']` |
| r06/r07 (salto de página) | `[]` (destino já é 1ª página, mesmo cruzando página no salto) |
| r08 (D.C. al fine) | `[]` |
| r09 (D.S. al coda) | `['m2', 'm5']` |
| r10 (3 vezes) | `[]` |
| r11 (várias sections) | `['m5']` |
| r12 (expansion codificada) | `[]` |
| r13 (1 compasso) | `[]` |

Achado que vale registrar: a regra normativa de §2.5 **não** filtra por
"cruza página" — só por "já é 1º compasso de página normal". Por isso a
Maple Leaf Rag sai com 8 pontos de chegada (todos os saltos da peça, a
maioria na mesma página), não só o único que cruza página (medido em P01c).
Isso é deliberado: o mesmo compasso pode ser alcançado a partir de estados
de página diferentes em execuções futuras (a peça tem 4 ritornelos), e o
exportador não tenta prever em que página o player estará quando o salto
acontecer — ele gera uma sequência para todo destino elegível e deixa o
player (P03b/P04a) decidir, em runtime, se precisa dela (regra de P00: "1.
T está na página exibida → fica", sem consultar `alternates.json`).

**Critério 2** (peças sem repetição: Étude, Nocturne, Clair de Lune,
Prelude): lista vazia nas 4 — confirmado na tabela acima.

**Critério 3** (`executionOrder` do C++ == `ScoreTimeline.measures` ids do
Dart, 23 fixtures). Script descartável em `score_bridge/test/` (apagado
depois) que carrega cada fixture de `test/fixtures/repeticoes/` e imprime
`tl.measures.map((m) => m.id)`; comparado ids a ids, em ordem, com
`_executionOrder` do C++ sobre as mesmas 23 fontes/flags. **23/23 idênticos**
(comprimentos de 3 a 145 ocorrências). Nenhuma pequena reordenação nem
divergência de um só id.

**Critério 4** (`.vsb` sem a opção nova, byte-idêntico a antes deste
passo). Gerado antes/depois via `git stash` dos 4 arquivos tocados
(`options.h`, `toolkit.h`, `options.cpp`, `toolkit.cpp`) nas 10 peças do
corpus, `-t vsb`, `--xml-id-seed 42`. `scene.json`, `glyphs.json`,
`timemap.json` e `meta.json` byte-idênticos em todas; só `manifest.json`
diferiu, e só no sufixo `-dirty` do `generator` (embutido pelo
`git describe` no momento do build, conforme a árvore de trabalho estava
suja ou não naquele instante) — mesmo artefato de build já observado em
P01a/P01b, sem relação com o código deste passo.

**Critério 5**: build sem avisos novos (conferido nas duas recompilações
completas que este passo disparou, por mudar `options.h`, incluído por
quase todo o projeto).

`flutter analyze` limpo (script descartável removido antes da checagem
final).
