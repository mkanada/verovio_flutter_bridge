# A02 — Cor e animação individual por nota

**Depende de:** A01 · **Decisão necessária:** não

## Objetivo

Entregar o requisito que o projeto anterior não conseguiu: **N notas acesas ao
mesmo tempo, cada uma com sua própria curva de fade**, endereçadas por
`xml:id`, sem agrupamento por instante e sem modos mutuamente exclusivos.

## Ler antes (só isto)

- `docs/licoes-do-verovio-lottie.md`, itens 1 e 2 de "O que travou" (é o que
  este passo existe para resolver — vale entender o que era impossível lá).
- `score_bridge/lib/src/score_controller.dart` (A01).

## O que fazer

1. Estender o `ScoreController`:

   ```dart
   void highlight(String id, {
     Color color,                       // cor de destaque
     Duration attack = Duration.zero,   // subida até a cor de destaque
     Duration hold  = Duration.zero,
     Duration release,                  // fade de volta à cor original
     Curve curve = Curves.easeOut,
   });
   void release(String id, {Duration duration, Curve curve});
   void highlightAll(Iterable<String> ids, {...});   // acorde: mesma chamada, N ids
   ```

2. Implementação: **um único `Ticker`** no controller (não um
   `AnimationController` por nota — milhares de tickers matam o frame). Cada
   nota acesa vira uma entrada `{startTime, phases, fromColor, toColor, curve}`;
   a cada tick o controller recalcula as cores ativas e notifica **uma vez**.
   Notas paradas saem do mapa.

3. A cor "de volta" é a cor **original resolvida** daquele nó (herdada da cena),
   não um preto fixo — partituras com `@color` no MEI têm notas coloridas.
   Guarde-a no documento ao montar o índice (S04/R01), não recalcule por frame.

4. Sobreposição: uma nota já acesa que recebe `highlight` de novo **reinicia**
   sua própria animação, sem afetar nenhuma outra. Esse é o comportamento que o
   agrupamento M2 do Lottie não conseguia oferecer.

## Fora de escopo

- Cursor, bounding box visual, "piano roll" (A04 e além).
- Disparo por tempo/timemap (A05) — aqui o host chama os métodos na mão.

## Critérios de aceite

1. Testes unitários do controller (sem render), com tempo simulado:
   - 50 notas acesas simultaneamente com `attack`/`release` diferentes; em
     instantes escolhidos, a cor de cada uma bate com o valor calculado à mão
     (tolerância de 1/255 por canal);
   - reiniciar a animação de uma nota não muda a cor de nenhuma outra no mesmo
     frame;
   - ao terminar, toda nota volta **exatamente** à sua cor original (inclusive
     uma nota com `@color` no MEI — inclua uma peça ou fixture com isso);
   - `clearAll()` no meio de 50 fades deixa a página idêntica ao estado de
     repouso (compare com o PNG estático: **0 pixels** de diferença).
2. Teste visual com frames capturados: um acorde de 4 notas + uma voz separada
   com onset diferente, todos acesos ao mesmo tempo, cada um em fase diferente
   do fade — capture 5 frames e confirme visualmente as 5 cores distintas
   convivendo. Anexe as imagens nas notas. (No Lottie isso era impossível: era
   exatamente a limitação "vozes com onsets diferentes se cancelam".)
3. Desempenho: com 64 notas animando simultaneamente, o tempo médio de
   `notifyListeners` + repaint fica abaixo de **8 ms** por frame na máquina de
   desenvolvimento (registre a máquina e o número). Se passar, investigue antes
   de seguir — P03 mede em dispositivo, mas um problema já aparece aqui.
4. Nenhum `Picture` estático recompilado durante as animações (mesmo contador
   de A01).

## Notas de execução

(a preencher por quem executar)
