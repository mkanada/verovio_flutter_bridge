# P04a — Dart: a rota de exibição na `ScoreTimeline`

**Depende de:** P03b · **Decisão necessária:** não

## Objetivo

Para cada ocorrência de compasso, calcular **qual página o player exibe**
(`PageRef`), pela regra de P00. Depois, fazer a haste (`curtainAt`) e o
repouso usarem essa rota. É função pura de `(documento, posição)`, como todo
o resto da timeline.

## Ler antes (só isto)

- `docs/plano/P00-visao-geral-paginas-alternativas.md`, seção "Player
  (Dart)" (a regra está lá, numerada; implemente **exatamente** aquela
  ordem).
- `score_bridge/lib/src/score_timeline.dart` inteiro (é o arquivo a mudar):
  comentário "REGRA DA HASTE", `MeasureInfo`, `_Measure`, `_Run`, `_build`,
  `_collect`, `restPageAt`, `curtainAt`, `_multiMeasureEdge`,
  `_singleMeasureEdge`.
- E03b, "Notas de execução" (saltos encadeados e `restNear`).

## Contexto que você precisa (não vá procurar, está aqui)

- `MeasureInfo.page` é a página **normal** do compasso, e é o que o host usa
  hoje. **Não mude o significado** (D-ALT-INDICE). Acrescente `view`
  (`PageRef`).
- `_Measure.left` e os `_Onset.x` saem de `document.geometry` (páginas
  normais). Numa ocorrência exibida numa alternativa, os x têm que vir de
  `document.geometryOf(view.sequence)`: o compasso está em outro lugar da
  página. **Esse é o erro mais fácil de cometer neste passo.**
- `_Run` agrupa ocorrências consecutivas na mesma página e sem salto. Passa
  a agrupar pela mesma `view` e sem salto.
- `_singleMeasureEdge` usa `prev.page == run.page - 1` para decidir se a
  página "aparece" depois da conclusão da virada anterior. Com rota, a
  condição equivalente é "houve haste entre `prev` e `run`", ou seja,
  `prev.view != run.view`. Confira que, nas peças **sem** repetição, isso dá
  exatamente os mesmos valores de hoje (critério 4). Se não der, registre e
  mantenha o comportamento antigo para o caso normal.
- A regra usa "página de `T` na sequência `s`" e "1º compasso de cada página
  de cada sequência". Monte esses mapas **uma vez**, no `_build`, percorrendo
  as páginas de cada sequência com o mesmo `_collect` (parametrizado pela
  sequência).
- Um `.vsb` antigo (sem `alternates.json`) cai no passo 5 da regra em todo
  salto. O resultado tem que ser **idêntico** ao de hoje.

## O que fazer

1. `ScoreTimeline(document, {bool useAlternates = true})`. Com `false`, ou
   sem alternativas no documento, a rota é a de hoje (toda `view` normal).
2. `MeasureInfo.view` (`PageRef`), documentado: "página exibida pelo player
   nesta ocorrência; `page` continua sendo a página normal".
3. `_build`: depois de montar `_measures`, uma passada que aplica a regra de
   P00 e grava `view` em cada `_Measure`. Os x (`left`, `onsets`) passam a
   ser calculados **depois** da rota, com a geometria da `view`.
4. `_runs` por `view`.
5. `restViewAt(ms)` (novo): a `view` do compasso corrente. `restPageAt(ms)`
   continua devolvendo a página **normal** (compatibilidade).
6. `curtainAt`: a haste vai de `run.view` a `next.view` (`SweepCurtain` com
   `pageIndex`/`sequence`/`targetPageIndex`/`targetSequence`). Sem haste
   quando `next.view == run.view`.
7. Atualize o comentário "REGRA DA HASTE" e acrescente um bloco "ROTA DE
   EXIBIÇÃO (fase P)" no topo do arquivo, com a regra numerada de P00.

## Fora de escopo

- `ScorePlayer` e a vista (P04b).
- Mudar a regra da haste (A05b/E03b).

## Critérios de aceite

1. Maple Leaf Rag (fixture de P02c): tabela nas notas, para cada salto,
   com instante, compasso de origem, destino, `view` antes, `view` depois e
   qual passo da regra decidiu. Todo salto para página diferente cujo
   destino tem sequência alternativa cai na página 0 dela, com o destino como
   1º compasso.
2. Invariante nas 23 fixtures de `repeticoes/`: para toda ocorrência, o
   compasso existe na página `view` (`geometryOf(view.sequence)
   .pageOf(id) == view.index`).
3. Invariante: as `view` só mudam em fronteira de página da mesma sequência
   (virada normal) ou em salto.
4. **Regressão:** com `useAlternates: false`, e nas peças sem repetição,
   `curtainAt` amostrado a cada 50 ms dá **0 diferenças** em relação ao
   código de antes deste passo (mesmo método de E02b/E03b, via `git stash`).
5. `curtainAt` ao redor de um salto para alternativa: entrada, estacionada e
   conclusão seguem a regra de A05b, com `targetSequence` preenchido. O
   `edgeX` da conclusão usa a largura da página **da frente**.
6. `flutter analyze` limpo, `flutter test` verde.

## Notas de execução

_(preencher)_
