# A05b — Virada automática por compasso e evidências visuais

**Depende de:** A05a, A03b · **Decisão necessária:** não

## Objetivo

Fechar o ciclo: o player vira a página sozinho, na fronteira certa, sem
interromper o destaque — e o projeto ganha as imagens que provam os
requisitos para quem não vai rodar o código.

## Ler antes (só isto)

- `../verovio_lottie/docs/plano/C05-host-simulado-timemap.md`, a regra de
  fronteira (já validada visualmente lá).
- `score_bridge/lib/src/score_player.dart` (A05a) e `score_view.dart` (A03b).

## Contexto que você precisa (não vá procurar, está aqui)

Regra de fronteira do projeto anterior, que ficou boa e já foi validada:

- `peekNextPage()` ao entrar no **último compasso** da página atual;
- `nextPage()` ao entrar no **primeiro compasso** da página seguinte.

Com as constantes de A03b (peek 500 ms, cover 667 ms), isso dá ao leitor o
aviso visual com um compasso de antecedência.

Como saber em que compasso se está: o mapa `nota → compasso → página`
construído em A05a a partir da **cena** (o timemap não traz `measureOn`).
Compassos por página no corpus vão de 12 a 31 — um compasso dura de alguns
centésimos a alguns segundos, então a antecedência de um compasso é
suficiente em andamentos normais e curta em andamentos muito rápidos.
Registre esse limite nas notas; se o usuário quiser mais antecedência, é
parâmetro, não mecanismo novo.

**O ponto de prova do projeto**: no Lottie, a virada cancelava o fade (dois
engines não compositáveis). Aqui, o destaque tem que atravessar a virada sem
soluço. A03b já provou isso com chamada manual; aqui a prova é com o player
real dirigindo.

## O que fazer

1. Ligar o player à navegação, com a regra de fronteira acima, e um parâmetro
   `peekLeadMeasures` (padrão 1) para quem quiser mais antecedência.
2. Desligar a virada automática quando o modo for `continuousScroll` — ali a
   rolagem acompanha a posição (use `scrollToId` da nota corrente, com
   alinhamento configurável).
3. Gerar as **evidências visuais** em `docs/exemplos/`:
   - `docs/exemplos/destaque-notas/<peça>/` — 4 a 5 frames com notas em fases
     diferentes;
   - `docs/exemplos/virada-pagina/<peça>/` — 5 frames da sequência de virada;
   - em cada diretório, o **roteiro exato** (instantes, comando) que gerou as
     imagens, de forma reproduzível.

## Fora de escopo

- Áudio e sincronização real.
- Otimização de desempenho (P03).

## Critérios de aceite

1. Uma peça de 3+ páginas toca do início ao fim com viradas automáticas, sem
   exceção, terminando com a última página em repouso.
2. **Nenhum resíduo**: um frame capturado no fim da execução é
   **pixel-idêntico** ao render estático da página final (0 pixels).
3. A virada acontece na fronteira certa: num teste com relógio simulado, o
   `peek` dispara no primeiro instante do último compasso da página e o
   `cover` no primeiro instante do primeiro compasso da seguinte (compare com
   os `tstamp` do timemap, calculados no teste).
4. **Destaque atravessa a virada** dirigido pelo player: notas acesas antes da
   virada continuam animando durante e depois dela (frames anexados).
5. `docs/exemplos/destaque-notas/<peça>/` e
   `docs/exemplos/virada-pagina/<peça>/` existem, com imagens e roteiro
   reproduzível.
6. Modo contínuo: a rolagem acompanha a nota corrente sem saltos bruscos
   (frames ou vídeo curto anexado).
7. `flutter analyze` limpo, `flutter test` verde.

## Notas de execução

(a preencher por quem executar)
