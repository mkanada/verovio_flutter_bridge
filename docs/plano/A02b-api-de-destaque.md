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

(a preencher por quem executar)
