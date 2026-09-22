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

_(preencher)_
