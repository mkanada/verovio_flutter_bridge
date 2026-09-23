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

Implementado como planejado. `MeasureInfo` ganhou `view` (`PageRef`) e
`isJump` (`bool`, novo em relação ao "O que fazer" original — necessário
para o critério 3 e para achar os saltos de fora da classe, já que
`_docOrderOfMeasure` é privado). `_Measure`/`_Run` migraram de `page: int`
para `view: PageRef`; a `view` de cada ocorrência é calculada em
`openOccurrence` (não numa passada separada — o cálculo dela precisa da
`view` da ocorrência **anterior**, então acontece no mesmo lugar em que a
ocorrência é criada), e os `x` (`left`/`onsets`) passam a usar
`document.geometryOf(m.view.sequence)`. `ScoreTimeline(document,
{useAlternates = true})`: `false`, ou um documento sem `alternates.json`,
pula a regra inteira (`routeAlternates = useAlternates &&
document.alternates.isNotEmpty`) e toda `view` é `PageRef(page normal)` —
idêntico ao código de antes deste passo. `restViewAt(ms)` novo;
`restPageAt` inalterado (continua a página normal, D-ALT-INDICE).
`curtainAt` monta o `SweepCurtain` com `sequence`/`targetSequence` de
`run.view`/`next.view`; `_singleMeasureEdge`'s `prev.page == run.page - 1`
virou `prev.view != run.view` (a mesma tradução literal do passo, sem
ganhar nem perder generalidade: para as peças **sem** repetição usadas no
critério 4, nunca há salto, então as duas condições sempre concordam).

Critérios verificados em `test/score_timeline_route_test.dart` (novo) e
`test/score_timeline_jump_curtain_test.dart` (existente, com um ajuste —
ver abaixo):

1. **Tabela de saltos da Maple Leaf Rag** (impressa pelo teste, 8 saltos no
   total):

   | Instante | Origem | Destino | View antes | View depois | Passo |
   | --- | --- | --- | --- | --- | --- |
   | 19500ms | mdf3uku | q1t6l0ej | `PageRef(0)` | `PageRef(0)` | a (mesma página) |
   | 37500ms | x1fh1gwb | ock08kg | `PageRef(0)` | `PageRef(0)` | a |
   | 57900ms | kkxu5s6 | qqplm6a | `PageRef(0)` | `PageRef(0)` | a |
   | 75900ms | e1g6ai9h | qhi6f7l | `PageRef(0)` | `PageRef(0)` | a |
   | 115500ms | dv3un7a | y12vaz72 | `PageRef(1)` | `PageRef(1)` | a |
   | 133500ms | m1ua1zdc | m1bcumr2 | `PageRef(1)` | `PageRef(1)` | a |
   | **153900ms** | z1m4pqeg | jn8k16x | `PageRef(2)` | **`PageRef(0, sequence: 6)`** | **d** |
   | 171900ms | cp9fsg8 | d132vz0f | `PageRef(0, seq 6)` | `PageRef(0, seq 6)` | a (mesma página, já dentro da sequência 6) |

   Só o salto de 153900ms cruza página (é o mesmo já conhecido de P01c/E03b);
   os outros 7 caem no passo "a" porque o destino já está na página exibida
   (mesma leitura da coluna "mesma página" da tabela "Saltos e pontos de
   chegada" do README). Os passos "b"/"c" nunca disparam nesta peça porque a
   `view` antes de qualquer salto é sempre normal (`s = null`) — não há
   sequência da qual "continuar" antes do primeiro salto que sai do normal.
2. Invariante nas 23 fixtures de `test/fixtures/repeticoes/`: para toda
   ocorrência, `geometryOf(view.sequence).pageOf(id) == view.index` — todas
   passam (nenhuma dessas fixtures tem `alternates.json`, então a regra
   sempre reduz à identidade de hoje, mas o invariante é verificado do
   mesmo jeito).
3. Invariante: nas mesmas 23 fixtures, toda mudança de `view` entre
   ocorrências consecutivas é `isJump` ou uma virada de página dentro da
   mesma sequência (`sequence` inalterado) — 0 violações.
4. **Regressão** (script temporário, removido depois de usado — mesma
   metodologia de E02b/E03b): amostragem de `curtainAt`/`restPageAt`/
   `measureIndexAt` a cada 50ms nas 4 peças do corpus **sem** repetição
   (`Chopin_Etude_Op10_No9`, `Chopin_-_Nocturne_Op._9_No._1`,
   `Clair_de_Lune__Debussy`, `Prelude_I_in_C_major_BWV_846_-...`), via
   `git stash` de `lib/src/score_timeline.dart` +
   `test/score_timeline_jump_curtain_test.dart`. **0 diferenças** em
   qualquer amostra de qualquer peça.
5. `test/score_timeline_jump_curtain_test.dart` precisou de um ajuste: o
   teste antigo (de E03b) esperava `targetPageIndex = 1` para o salto
   153900ms da Maple Leaf Rag, assumindo a página normal de destino. Isso
   deixou de valer **por design**: a fixture (regenerada em P03a/P02c) tem
   `alternates.json`, e `useAlternates` é `true` por padrão, então a regra
   de P00 agora escolhe a alternativa (`targetPageIndex = 0`,
   `targetSequence = 6`) — exatamente o comportamento que este passo
   implementa, não uma regressão. O teste foi atualizado para a nova
   expectativa (critério 5), com o resto da asserção (entrada/estacionada/
   conclusão, `edgeX`) inalterado.
6. `flutter analyze`: nenhum problema. `flutter test` (suíte inteira, 289
   casos — os 285 de antes + os 4 novos de
   `test/score_timeline_route_test.dart`): todos passam.
