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

_(preencher)_
