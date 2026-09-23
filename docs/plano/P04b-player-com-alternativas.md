# P04b — Dart: `ScorePlayer` segue a rota com páginas alternativas

**Depende de:** P04a · **Decisão necessária:** não

## Objetivo

Ligar a rota de P04a à vista de P03b: tocando, o player mostra as páginas
alternativas nos saltos, com a mesma haste de sempre. Parado, o usuário
navega nas páginas normais como antes.

## Ler antes (só isto)

- `docs/plano/P00-visao-geral-paginas-alternativas.md`.
- `score_bridge/lib/src/score_player.dart` inteiro (em especial `_publish`,
  L293-L333, `seek` e `seekToElement`).
- `score_bridge/lib/src/score_view.dart`: `ScoreViewController.showPage` e
  `displayedPage` (de P03b).

## Contexto que você precisa (não vá procurar, está aqui)

- Hoje `_publish` faz: modo contínuo → `scrollToId`, e retorna; senão
  publica a `curtainAt` e, sem haste, chama `v.goToPage(restPageAt)` quando
  `v.currentPage` difere.
- Com alternativas, o repouso é um `PageRef`: compare com
  `v.displayedPage` e chame `v.showPage(restViewAt)`.
- `seek` e `seekToElement` chamam `_publish(seeking: true)`. Num seek para
  dentro de um trecho repetido, a rota já diz qual página mostrar.
  `seekToElement` não muda (D-TOQUE decide a passagem, e a rota decide a
  página).
- Se o usuário navegar manualmente durante a execução (`goToPage`), o player
  reassume a página da rota no próximo `_publish`, como já faz hoje.

## O que fazer

1. `ScorePlayer({..., bool useAlternates = true})`, repassado à
   `ScoreTimeline`.
2. `_publish` (modos paginados): repouso com `restViewAt` + `showPage`. A
   haste já vem com as sequências de `curtainAt`.
3. Modo contínuo: sem mudança (usa `measures[index].id` e a faixa normal).
4. `pause()` não mexe na página exibida. `dispose()` não precisa de nada
   novo.
5. Doc-comments: explique que, em execução, a vista pode mostrar páginas
   alternativas, e que `currentPage` continua na numeração normal.

## Fora de escopo

- Evidências visuais (P04c).

## Critérios de aceite

1. Maple Leaf Rag, `pagedSweep`, tocando do início ao fim a 4× (passos de
   200 ms, como E03b): sem exceção, termina em `player.duration`, todas as
   notas apagadas no fim, e a sequência de `displayedPage` observada bate
   com a rota de P04a (tabela: instante de cada troca e `PageRef`).
2. O mesmo em `pagedSlide`, e em `continuousScroll` (que não pode mostrar
   alternativa nenhuma: `displayedPage.isAlternate` sempre `false`).
3. `seek` para dentro da 2ª passagem de um trecho repetido: a vista mostra a
   alternativa certa (a da rota naquele instante) e as notas acesas estão
   **na alternativa**.
4. `useAlternates: false`: comportamento idêntico ao de antes do passo
   (reusa os testes de E03b sem mudança).
5. `PictureStats.live` volta ao patamar no fim (sem vazamento).
6. `flutter analyze` limpo, `flutter test` verde.

## Notas de execução

Implementado exatamente como o "O que fazer" descreve — sem desvios:
`ScorePlayer` ganhou `useAlternates` (repassado a `ScoreTimeline`); `_publish`
troca `restPageAt`/`goToPage` por `restViewAt`/`showPage` (compara com
`v.displayedPage`, não `v.currentPage`); o modo contínuo continua igual
(`scrollToId` na faixa normal); `pause`/`dispose` não precisaram de nada
novo. Os doc-comments do topo do arquivo ganharam um parágrafo "PÁGINAS
ALTERNATIVAS" explicando a relação `displayedPage`/`currentPage`.

Critérios verificados em `test/score_player_alternates_test.dart` (novo),
com `test/fixtures/maple-leaf-rag.vsb` (8 sequências):

1. e 2. `pagedSweep` e `pagedSlide`, tocando a peça toda a 4× (passos de
   200 ms): a sequência de `displayedPage` observada (deduplicada por
   mudança) bate, item a item, com a sequência de `MeasureInfo.view`
   deduplicada de `ScoreTimeline` (a rota de P04a) — nenhuma exceção, chega
   em `player.duration`. `continuousScroll`: `displayedPage.isAlternate`
   nunca vira `true`, do início ao fim.
3. `seek(160000ms)` (dentro da sequência 6, depois do salto de 153900ms):
   `displayedPage == PageRef(0, sequence: 6)` — a `view` que
   `ScoreTimeline.measures[measureIndexAt(160000)]` também dá — com a nota
   ativa (`noteIds.first` daquela ocorrência) destacada e com bbox dentro
   da página 0 da sequência 6 (`geometryOf(6).elementOf(id)!.page == 0`),
   sonda de pixel vermelho na tela confirma.
4. `useAlternates: false`: `displayedPage.isAlternate` fica `false` do
   início ao fim, tocando a peça inteira — e a suíte inteira (295 casos,
   incluindo os testes de E03b que usam `ScorePlayer` sem passar
   `useAlternates`, portanto com o padrão `true`) continua verde, porque
   nenhuma delas consulta `displayedPage`/`view` (só `currentPage`/`page`,
   inalterados).
5. `PictureStats.live`: depois de tocar a peça toda (que passa pela
   alternativa) e desmontar a árvore, volta a 0.
6. `flutter analyze`: nenhum problema. `flutter test` (suíte inteira, 295
   casos — os 289 de P04a + os 6 novos de
   `test/score_player_alternates_test.dart`): todos passam.
