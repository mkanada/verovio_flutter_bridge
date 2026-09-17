# A05 — Host simulado com `timemap` (playback automático)

**Depende de:** A02, A03, S07 · **Decisão necessária:** não

## Objetivo

Provar o caso de uso real de ponta a ponta: um host que lê o `timemap` do
próprio `.vsb` e conduz o destaque das notas e a virada de página em tempo
real, como o zywny vai fazer.

## Ler antes (só isto)

- `../verovio_lottie/docs/plano/C05-host-simulado-timemap.md` — o roteiro que
  já foi montado uma vez (incluindo a limitação conhecida de peças com
  expansão/repetição, que continua valendo).
- `verovio/include/vrv/timemap.h` — o formato do timemap (`tstamp`, `on`,
  `off`, `tempo`).
- A02 (API de destaque) e A03 (API de navegação).

## O que fazer

1. `ScorePlayer` (em `score_bridge`, ou num `example/` se ficar mais claro):
   - recebe `VsbDocument` + `ScoreController` + `ScoreView` controller;
   - roda um relógio próprio (`Ticker`), em ms musicais;
   - a cada instante do timemap, chama `highlightAll(on)` e `release(off)`;
   - dispara `peekNextPage()` ao entrar no **último compasso** da página atual e
     `nextPage()` ao entrar no **primeiro compasso** da próxima (a mesma regra
     de fronteira do projeto anterior — ela ficou boa e já foi validada
     visualmente).
   - `play()`, `pause()`, `seek(Duration)`, `speed`.

2. Para saber "em que página está o compasso X", use o índice de S04 (nós de
   classe `measure` com bbox e página).

3. Gerar as **evidências visuais** em `docs/exemplos/`, como o projeto anterior
   fazia: 4-5 frames de destaque de notas e 5 frames de virada de página, de
   uma peça do corpus, com o roteiro (tempos exatos) registrado junto.

## Fora de escopo

- Áudio, MIDI, sincronização com microfone/instrumento (é o zywny).
- Modo "aluno tocando ao vivo" — no Flutter ele é a **mesma** API de A02 (não
  há dois modos como havia no Lottie); se o usuário quiser um exemplo dele,
  é um exemplo a mais, não um mecanismo a mais.

## Critérios de aceite

1. Uma peça de 3+ páginas toca do início ao fim sem exceção, sem frame perdido
   perceptível e terminando com a página final em repouso.
2. **Consistência com o timemap**: num teste com relógio simulado, em 20
   instantes sorteados, o conjunto de ids destacados no controller é
   exatamente o conjunto esperado pelo timemap naquele instante (diferença
   vazia nos dois sentidos).
3. `seek` para o meio da peça deixa o estado coerente: página certa, nenhum
   destaque "preso" de antes do seek.
4. `docs/exemplos/destaque-notas/<peça>/` e `docs/exemplos/virada-pagina/<peça>/`
   com as imagens e o roteiro exato que as gerou (comando reproduzível).
5. Um frame de repouso capturado no fim da execução é **pixel-idêntico** ao
   render estático da página final (0 pixels) — prova de que o playback não
   deixa resíduo de cor.

## Notas de execução

(a preencher por quem executar)
