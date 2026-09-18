# A02a — Motor de animação: um `Ticker`, fases e curvas

**Depende de:** A01c · **Decisão necessária:** não

## Objetivo

O mecanismo que o projeto anterior não conseguiu ter: **N notas acesas ao
mesmo tempo, cada uma na sua própria fase**, com um único relógio. Neste
passo, só o motor — sem render, com tempo simulado e testes determinísticos.

## Ler antes (só isto)

- [`docs/licoes-do-verovio-lottie.md`](../licoes-do-verovio-lottie.md), itens
  1 e 2 de "O que travou" — é o problema que este passo existe para resolver.
- `score_bridge/lib/src/score_controller.dart` (A01c).

## Contexto que você precisa (não vá procurar, está aqui)

- **Um `Ticker` só.** Um `AnimationController` por nota significa milhares de
  tickers e um `notifyListeners` por nota por frame; o frame morre. O
  controller mantém um mapa `id → estado de animação` e, a cada tick,
  recalcula as cores ativas e notifica **uma vez**.
- Estado por nota: `{ inicio, fases (attack/hold/release), corDe, corPara,
  curva }`. O tempo corrente vem do `Ticker` (`Duration` desde o início), não
  de `DateTime.now()` — é isso que permite testar com tempo simulado e
  reproduzir bugs.
- **Notas paradas saem do mapa.** Um mapa que só cresce vira vazamento e o
  tick fica linearmente mais caro ao longo de uma peça.
- Quando o mapa fica vazio, **pare o `Ticker`**: uma partitura parada não
  pode consumir frame.
- Reinício: uma nota já acesa que recebe `highlight` de novo **reinicia a
  própria animação** e não toca em nenhuma outra. Era exatamente isso que o
  agrupamento por instante do Lottie não conseguia fazer.
- Interpolação de cor: `Color.lerp` opera em sRGB direto, igual ao que o olho
  espera aqui; não invente espaço de cor. Documente a escolha para que o
  cálculo "à mão" dos testes seja o mesmo.
- Orçamento: com 64 notas ativas, o recálculo do tick precisa ser trivial
  (algumas dezenas de microssegundos). Qualquer alocação por nota por frame
  (listas novas, mapas novos, `Color` intermediários) aparece no perfil.

## O que fazer

1. `score_bridge/lib/src/highlight_engine.dart` (separado do controller, para
   poder testar sem `Ticker` real):

   ```dart
   class HighlightEngine {
     void start(String id, HighlightSpec spec, Duration now);
     void stop(String id, {Duration? at, Duration? release, Curve? curve});
     void stopAll({Duration? at});
     Map<String, Color> colorsAt(Duration now);   // só as ativas
     bool get isIdle;
   }

   class HighlightSpec {
     final Color color;
     final Duration attack, hold, release;
     final Curve curve;
     final Color baseColor;    // a cor original resolvida do nó
   }
   ```

2. Fases: `attack` (corDe → corPara), `hold` (constante), `release`
   (corPara → corDe). Duração zero em qualquer fase é válida e comum
   (destaque instantâneo é `attack: 0`).

3. O `Ticker` vive no `ScoreController` e chama `colorsAt` — o motor não sabe
   o que é um `Ticker`.

## Fora de escopo

- API pública de destaque (A02b) e render (A02c).
- Sincronização com timemap (A05).

## Critérios de aceite

1. `flutter analyze` limpo, `flutter test` verde.
2. Teste com tempo simulado: **50 notas** com `attack`/`hold`/`release`
   diferentes; em 5 instantes escolhidos, a cor de cada uma bate com o valor
   calculado à mão no teste (tolerância **1/255 por canal**).
3. Teste de independência: reiniciar a animação de uma nota não muda a cor de
   nenhuma outra no mesmo instante.
4. Teste de término: ao fim do `release`, a cor é **exatamente** a
   `baseColor` (igualdade, não tolerância) e o id **sai** do mapa.
5. Teste de ociosidade: depois que a última nota termina, `isIdle` é
   verdadeiro.
6. Teste de curva: com `Curves.easeOut`, o valor em t=50% bate com
   `Curves.easeOut.transform(0.5)` aplicado à interpolação (guarda contra
   aplicar a curva no lugar errado).
7. Teste de alocação zero por frame: `colorsAt` chamado 1 000 vezes com 64
   notas ativas não cresce a memória de forma mensurável (registre o método
   usado nas notas).

## Notas de execução

(a preencher por quem executar)
