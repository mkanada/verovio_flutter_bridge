# A03 — Páginas: navegação, virada e rolagem

**Depende de:** A01 · **Decisão necessária:** não (mas confirme o estilo padrão
com o usuário antes de fixar constantes de tempo)

## Objetivo

Mostrar a partitura inteira — não uma página isolada — com virada de página
animada no estilo Synthesia (a próxima página "espreita" antes de cobrir), mais
uma alternativa de rolagem contínua. No Flutter isso é composição de widgets:
o obstáculo que travou o projeto anterior (dois engines de animação não
compositáveis) não existe aqui.

## Ler antes (só isto)

- `../verovio_lottie/docs/plano/C04-paginas-virada.md`, seções "Decisões de
  escopo" e "Notas de execução" — as constantes já calibradas visualmente
  (peek ≈ 8% da distância, peek 15 frames, cover 20 frames a 30 fps ≈ 500 ms e
  ≈ 667 ms) e o erro já cometido (peek de 60% "vira quase a página inteira").
- `score_bridge/lib/src/score_page_view.dart` (A01).

## O que fazer

1. `ScoreView` (novo widget, acima do `ScorePageView`):

   ```dart
   ScoreView({
     required VsbDocument document,
     required ScoreController controller,
     ScorePageMode mode = ScorePageMode.pagedPeek,   // pagedPeek | pagedSlide | continuousScroll
     Duration peekDuration  = const Duration(milliseconds: 500),
     Duration coverDuration = const Duration(milliseconds: 667),
     double peekFraction = 0.08,
   })
   ```

   API de navegação: `goToPage(int)`, `nextPage()`, `previousPage()`,
   `peekNextPage()` (só a fase de espreitar), `scrollToId(String)` (usa a bbox
   de S04 e o índice).

2. `pagedPeek`: duas fases, como no projeto anterior — (A) `peekNextPage()`
   revela `peekFraction` da próxima página e **para**; (B) `nextPage()` completa
   a transição. As duas são animações de transformação de uma trilha horizontal
   de páginas; cada página continua sendo um `ScorePageView` (com seu cache).

3. `continuousScroll`: as páginas empilhadas verticalmente num `ListView`
   virtualizado — só as páginas visíveis mantêm `Picture` compilado. Defina e
   documente o limite de páginas mantidas em cache (recomendação inicial: a
   visível ± 1).

4. Destaque **atravessa** a virada de página: uma nota acesa na página 1
   continua acesa e animando durante e depois da transição (no Lottie isso era
   impossível — a virada cancelava o fade). Isso deve sair de graça da
   arquitetura; o critério 3 existe para provar que saiu.

## Fora de escopo

- Disparar a virada a partir do tempo/timemap (A05) — aqui é chamada do host.
- Zoom/pan (não é requisito; se aparecer, é passo novo).

## Critérios de aceite

1. Estado de repouso de cada página é **pixel-idêntico** ao render estático
   daquela página (0 pixels de diferença contra o PNG de R05), nas 34 páginas.
   É a garantia de que a trilha/câmera não introduziu deslocamento ou reescala.
2. Sequência `peekNextPage()` → `nextPage()` capturada em 5 frames (repouso,
   meio do peek, fim do peek, meio do cover, repouso da próxima) e inspecionada
   visualmente; anexe as imagens nas notas. No fim do peek, a página atual ainda
   deve estar quase inteira visível (é o erro que o C04 cometeu e corrigiu).
3. **Destaque sobrevive à virada**: acenda uma nota com `release` de 2 s, dispare
   a virada no meio, e confirme por frames que o fade continuou sem
   interrupção e que a cor final é a original.
4. `scrollToId` leva a página/rolagem à posição em que a bbox do elemento fica
   visível — teste com um id da última página de uma peça de 7 páginas.
5. `continuousScroll`: rolar do início ao fim de uma peça de 7 páginas mantém no
   máximo o nº documentado de `Picture`s vivos (contador no teste).

## Notas de execução

(a preencher por quem executar)
