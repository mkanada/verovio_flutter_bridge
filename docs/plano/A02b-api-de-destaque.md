# A02b — API de destaque e restauração da cor original

**Depende de:** A02a · **Decisão necessária:** não

## Objetivo

Expor o motor numa API que o host usa sem pensar: acender uma nota, acender
um acorde, apagar, apagar tudo — e garantir que apagar devolve a página
**exatamente** ao estado de repouso.

## Ler antes (só isto)

- `score_bridge/lib/src/highlight_engine.dart` (A02a).
- `score_bridge/lib/src/score_controller.dart` (A01c).
- Requisitos 2 e 3 do [`CLAUDE.md`](../../CLAUDE.md).

## Contexto que você precisa (não vá procurar, está aqui)

- **A cor de volta é a cor original resolvida do nó**, não preto. Ela vem do
  índice/segmentação (A01a), resolvida uma vez ao carregar a página. Se você
  recalcular por frame, além de caro, vai errar em nó com `@color`.
- O host chama por `xml:id` — os mesmos ids do `timemap`. Um id que não existe
  na página deve ser **ignorado silenciosamente** (no corpus, Gymnopédie tem
  180 ids de timemap sem correspondente na cena e Maple Leaf Rag tem 883;
  lançar exceção aqui quebraria o playback de A05 em duas das dez peças).
- Uma chamada com N ids deve produzir **uma** notificação, não N.
- Defaults razoáveis (e documentados) importam mais que flexibilidade: o host
  típico vai chamar `highlight(id)` sem parâmetro nenhum.

## O que fazer

1. Estender o `ScoreController`:

   ```dart
   void highlight(String id, {
     Color color = const Color(0xFFD32F2F),
     Duration attack = Duration.zero,
     Duration hold = Duration.zero,
     Duration release = const Duration(milliseconds: 300),
     Curve curve = Curves.easeOut,
   });
   void highlightAll(Iterable<String> ids, { /* mesmos parâmetros */ });
   void release(String id, {Duration? duration, Curve? curve});
   void releaseAll({Duration? duration, Curve? curve});
   void clearAll();    // imediato, sem fade
   ```

2. `highlight` numa nota já acesa **reinicia** a animação dela, sem tocar nas
   outras (o comportamento que o Lottie não permitia).

3. Interação com `setColor` de A01c: definir e documentar a precedência
   (recomendação: `setColor` é uma cor "fixa" que a animação sobrepõe
   enquanto dura e para a qual volta ao terminar — ou seja, `setColor` muda a
   `baseColor`). Teste a combinação.

4. O `Ticker` liga ao receber a primeira animação e desliga quando o motor
   fica ocioso.

## Fora de escopo

- Evidência visual e desempenho (A02c).
- Disparo automático por tempo (A05).

## Critérios de aceite

1. `flutter analyze` limpo, `flutter test` verde.
2. `highlightAll` com 50 ids dispara **uma** notificação.
3. Ids inexistentes em `highlightAll` são ignorados, e os existentes acendem
   normalmente (teste com a mistura exata: ids reais + ids `-rend2`).
4. Reinício: acender uma nota no meio do `release` a leva de volta ao começo
   do `attack`, sem alterar a fase das outras 49.
5. **Restauração exata**: depois de `clearAll()` no meio de 50 fades, a
   página renderizada é **byte-idêntica** ao PNG de repouso (0 pixels).
6. `releaseAll` com duração termina com todas de volta às cores originais
   (igualdade exata por canal), inclusive uma nota com `@color` no MEI.
7. Precedência entre `setColor` e `highlight` documentada e testada.
8. O `Ticker` está parado quando não há animação ativa (teste com
   `Ticker.isActive`).

## Notas de execução

Executado em 2026-09-21. `flutter test` verde; testes em
`test/score_controller_test.dart` (grupo "destaques").

**O que foi feito** — API no `ScoreController`: `highlight`, `highlightAll`,
`release`, `releaseAll`, `clearAll` (imediato, sem fade), `isHighlighted`,
`highlightedCount`. Defaults: cor `#D32F2F`, `attack` 0, `hold` 0, `release`
300 ms, `Curves.easeOut` (`kDefaultHighlightColor`).

**Decisões**

- O `Ticker` é do controller (um `Ticker` próprio, sem `TickerProvider` de
  widget): liga na primeira animação e **desliga** quando o motor fica ocioso;
  o tick notifica **uma vez por frame**, e só se alguma cor mudou.
- **Relógio:** o tempo do controller só avança enquanto o `Ticker` roda. Um
  destaque novo parte do tempo do último frame (o primeiro frame depois do
  `start` do `Ticker` tem `elapsed == 0`); nos testes, dê um `pump()` antes de
  avançar o relógio.
- **Precedência entre `setColor` e `highlight`:** ver A01c. `setColor` durante
  a animação só muda a base (destino do `release`); ao terminar, o id fica na
  cor fixa.
- Ao fim de uma animação o id volta ao repouso **por remoção** do override
  (cor fixa ou original do nó), não por uma cor calculada — é isso que garante
  a byte-identidade com o repouso.
- `highlight` de id inexistente é ignorado, sem notificar nem ligar o `Ticker`.

**Critérios**

1. `flutter analyze` limpo, `flutter test` verde (130/130).
2. `highlightAll` com 50 ids → 1 notificação.
3. Mistura exata de ids reais e `-rend2`: os 50 reais acendem, os 20 `-rend2`
   são ignorados.
4. Reinício no meio do `release`: a nota vai à cor nova imediatamente e as
   outras 49 mantêm exatamente a cor que tinham.
5. `clearAll()` no meio de 50 fades (mais uma cor fixa): página **0 pixels**
   diferente do PNG de repouso e `Ticker` parado.
6. `releaseAll` com duração: termina com `colors` vazio e 0 pixels contra o
   repouso, com uma nota `@color` azul no meio (no meio do `release` a nota
   azul está entre vermelho e azul, não preto).
7. Precedência `setColor`/`highlight`: parte do verde fixo, volta ao azul novo
   quando o `setColor` muda durante a animação; `clearColor` durante o
   destaque leva o `release` à cor original.
8. `Ticker` parado sem animação ativa (`tickerActive`, também para
   `release: 0`, que termina no mesmo instante).
