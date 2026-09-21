# A05a — `ScorePlayer`: relógio próprio e timemap → destaque

**Depende de:** A02b, S07 · **Decisão necessária:** não

## Objetivo

O host simulado: um relógio que lê o `timemap` embutido no `.vsb` e acende e
apaga as notas nos instantes certos, com `play`/`pause`/`seek`/`speed`. É o
caso de uso real do zywny, sem áudio.

## Ler antes (só isto)

- `../verovio_lottie/docs/plano/C05-host-simulado-timemap.md` — o roteiro já
  montado uma vez, incluindo a limitação de peças com repetição.
- `verovio/include/vrv/timemap.h` (o formato do timemap no lado C++).
- `score_bridge/lib/src/model.dart`: `TimemapEntry`.
- A02b (API de destaque).

## Contexto que você precisa (não vá procurar, está aqui)

`TimemapEntry` (R01) traz `tstamp`, `qstamp`, `qfrac`, `on`, `off`,
`restsOn`, `restsOff`, `tempo`, `measureOn`. Fatos medidos nos pacotes do
corpus:

- `tstamp` está em **milissegundos**; é a coluna que o player usa.
  (Scarlatti: 447 entradas, `tstamp` final 134 500 ms ≈ 2 min 15 s.)
- **`measureOn` não vem preenchido** nos timemaps gerados pelo pipeline atual
  (0 entradas em todas as peças). Portanto, "em que compasso estou" **não**
  sai do timemap: tem que sair da cena — o nó de classe `measure` que é
  ancestral da nota. Monte esse mapa (`id de nota → id de compasso → página`)
  ao carregar o documento, percorrendo a árvore uma vez.
- `on`/`off` trazem ids de nota. **Nem todos existem na cena**: Gymnopédie tem
  180 ids extras (sufixo `-rend2`) e Maple Leaf Rag 883 — são repetições/
  expansões. O player tem que ignorá-los sem erro (a API de A02b já faz isso,
  mas o player não pode contar quantos "acendeu" e se assustar).
- `tempo` aparece em algumas entradas (mudança de andamento). O player não
  precisa dele para tocar — o `tstamp` já embute o andamento — mas exponha-o,
  porque o host real vai querer mostrar.
- Compassos por página no corpus: de 12 a 31 (Scarlatti). É esse mapa que
  A05b usa para a virada automática.

## O que fazer

1. `ScorePlayer` (em `score_bridge`, ou em `example/` se ficar mais claro):

   ```dart
   class ScorePlayer {
     ScorePlayer({required this.document, required this.controller, this.view});
     void play();
     void pause();
     void seek(Duration position);
     double speed;                       // 1.0 = tempo do timemap
     Duration get position;
     Duration get duration;
     ValueListenable<int> get currentMeasureIndex;
   }
   ```

2. Relógio: um `Ticker` próprio, em ms musicais (`posição += delta * speed`).
   Nunca `DateTime.now()` — o teste precisa de tempo simulado.

3. A cada avanço, aplique **todas** as entradas cujo `tstamp` foi
   ultrapassado desde o último tick (não só a próxima): com `speed` alto ou um
   frame perdido, pular entradas deixa notas acesas para sempre.

4. `seek`: recalcula o estado do zero para o instante pedido — nada de
   destaque "preso" de antes do seek.

5. Expor o **índice de compassos** que A05b precisa para dirigir a haste de
   virada (construído junto com o mapa `nota → compasso → página`, no mesmo
   percurso da árvore):

   ```dart
   class MeasureInfo {
     final String id;              // xml:id do compasso
     final int page;               // página onde ele está
     final List<String> noteIds;   // notas do compasso, na ordem do timemap
     final int startMs;            // tstamp da primeira nota do compasso
     final int endMs;              // tstamp da primeira nota do compasso seguinte
   }
   List<MeasureInfo> get measures; // em ordem de execução
   ```

   `endMs` do último compasso da peça é o `tstamp` final. Compassos de
   repetição (ids `-rend2`) que não existem na cena ficam de fora, como as
   notas ausentes.

## Fora de escopo

- Virada automática de página e evidências (A05b).
- Áudio, MIDI, sincronização com instrumento (é o zywny).
- Modo "aluno tocando ao vivo": no Flutter é a **mesma** API de A02 — não é
  um mecanismo a mais.

## Critérios de aceite

1. **Consistência com o timemap**: com relógio simulado, em **20 instantes
   sorteados**, o conjunto de ids destacados no controller é exatamente o
   esperado pelo timemap naquele instante (diferença vazia nos dois
   sentidos), ignorando ids ausentes da cena.
2. Uma peça de 3+ páginas toca do início ao fim sem exceção e termina com
   todas as notas apagadas.
3. `seek` para o meio da peça deixa o estado coerente: nenhum destaque preso,
   `currentMeasureIndex` correto.
4. `speed = 4.0` não perde nenhuma entrada do timemap (compare o conjunto de
   ids acesos ao longo da execução com o da execução a 1.0).
5. `pause`/`play` não movem a posição nem reiniciam animações em curso.
6. Ids do timemap ausentes da cena não geram erro nem log ruidoso (teste com
   Gymnopédie, que tem 180 deles).
7. `measures` cobre todos os compassos de uma peça de 3+ páginas: `startMs`
   estritamente crescente, `endMs == startMs` do seguinte, cada `page` coerente
   com a cena.
7. `flutter analyze` limpo, `flutter test` verde.

## Notas de execução

Concluído em 2026-09-21 (`score_timeline.dart`, `score_player.dart`,
`test/score_player_test.dart`, `test/score_timeline_test.dart`).

- **Divisão**: a lógica pura (índice de compassos e `curtainAt`) mora em
  `ScoreTimeline` (sem widget nem `Ticker`); `ScorePlayer` é o relógio + a
  ligação com `ScoreController` e `ScoreViewController`. `ScorePlayer.view`
  é um **`ScoreViewController`** (não o widget).
- **Índice de compassos**: um percurso da árvore (nós `hidden` ignorados) monta
  `id → compasso` e a página de cada compasso; a ordem e os instantes vêm do
  timemap (`on` e `restsOn`). Ids ausentes da cena ficam de fora sem erro.
  `MeasureInfo(id, page, noteIds, startMs, endMs)` exatamente como no plano.
  `currentMeasureIndex` é 0 antes do primeiro compasso.
- **Critério 1**: Gymnopédie, Scarlatti e Nocturne — 20 instantes sorteados por
  `seek` e, também, avanço incremental em passos irregulares (1–1500 ms): o
  conjunto de `controller.highlightedIds` é **igual** ao esperado pelo timemap
  (com `release: 0`, e restrito aos ids visíveis para o controller).
  Implementação: `on` → `highlightAll(hold: 365 dias)`, `off` → `release(id)`
  (o fim da nota é dirigido pelo `off`, não por uma duração fixa — com `speed`
  ≠ 1 isso mantém a nota alinhada à música).
- **Critérios 2–6**: Nocturne (7 páginas) toca até o fim e termina com
  `highlightedCount == 0`; `seek` para 30 s do Scarlatti cai no compasso
  certo e preserva cores fixas do host (`clearHighlights`, novo em
  `ScoreController`); a 4× os conjuntos de ids acesos são idênticos aos de 1×
  (todos os `on` do timemap); pausar não anda e não apaga notas seguradas; a
  Gymnopédie (≥100 ids ausentes) toca a 30× sem exceção.
- **Critério 7**: nas 10 peças `startMs` estritamente crescente, `endMs ==
  startMs` do seguinte, cada `page` coerente com a cena, todas as notas do
  compasso existem na página dele.
- `tempo` exposto em `ValueListenable<double?> tempo`; `onEntry` chama o host a
  cada entrada aplicada (som, por exemplo).
- Relógio: `Ticker` próprio em ms musicais; `advance(Duration)` é o mesmo
  caminho para tempo simulado.
