# A03a — `ScoreView`: trilha de páginas e navegação direta

**Depende de:** A01b · **Decisão necessária:** não

## Objetivo

Sair de "uma página na tela" para "a partitura inteira", com navegação
direta (`goToPage`, `nextPage`, `previousPage`) e **sem** mudar um pixel do
estado de repouso de nenhuma página. A animação da virada é A03b.

## Ler antes (só isto)

- `score_bridge/lib/src/score_page_view.dart` (A01b).
- `../verovio_lottie/docs/plano/C04-paginas-virada.md`, seção "Decisões de
  escopo" (a trilha horizontal + câmera já foi desenhada uma vez).

## Contexto que você precisa (não vá procurar, está aqui)

- O corpus tem 34 páginas em 10 peças, de 2 a 7 páginas por peça — a maior é
  o Chopin Nocturne (7). Toda medida de "cache de páginas" tem que fazer
  sentido para 7 páginas, não para 200 (uma peça grande fica para o `zywny`).
- Cada página é um `ScorePageView` com o próprio cache de `Picture`
  (A01b). A trilha é composição de widgets: nada de um `Picture` gigante com
  todas as páginas.
- Páginas podem ter **tamanhos diferentes** entre si (o formato carrega
  `widthPx`/`heightPx` por página). No corpus são todas A4, mas não assuma
  isso no layout — a trilha precisa posicionar por tamanho real.
- **Dois arranjos de página.** `pagedSlide` usa a trilha horizontal (páginas
  lado a lado, câmera). `pagedSweep` (o padrão, A03b) **sobrepõe** a página
  atual e a próxima no mesmo lugar (uma `Stack`), e a virada é uma haste que
  recorta a de cima. Este passo só precisa entregar navegação instantânea, mas
  deixe a estrutura de `ScoreView` capaz de montar **a página atual e a
  seguinte ao mesmo tempo** (a seguinte só é instanciada quando existir e for
  necessária) — A03b se apoia nisso.
- O estado de repouso de uma página tem que continuar **pixel-idêntico** ao de
  A01b: qualquer deslocamento fracionário da câmera (um `translate` com valor
  não inteiro) muda o antialiasing e quebra a comparação. Se precisar de
  posição fracionária durante a animação, tudo bem — mas o repouso tem que
  cair em posição exata.

## O que fazer

1. `score_bridge/lib/src/score_view.dart`:

   ```dart
   class ScoreView extends StatefulWidget {
     const ScoreView({
       required this.document,
       required this.controller,
       this.mode = ScorePageMode.pagedSweep,    // A03b
       this.onPageChanged,
     });
   }

   enum ScorePageMode { pagedSweep, pagedSlide, continuousScroll }

   class ScoreViewController {          // ou métodos no State via GlobalKey
     void goToPage(int index);
     void nextPage();
     void previousPage();
     int get currentPage;
   }
   ```

2. Neste passo, `goToPage` é **instantâneo** (sem animação): o objetivo é a
   trilha, o mapeamento de páginas e a garantia de repouso idêntico.

3. Limites: `goToPage` fora do intervalo não lança — satura no primeiro/último
   e devolve o índice efetivo (documente).

4. `onPageChanged` dispara uma vez por mudança efetiva, nunca por frame.

## Fora de escopo

- Virada animada (A03b) e rolagem contínua (A03c).
- Overlays (A04).

## Critérios de aceite

1. **Repouso pixel-idêntico**: nas 34 páginas do corpus, o render de repouso
   via `ScoreView` é byte-idêntico ao de `ScorePageView` (A01b) e ao do
   harness (R05). É a prova de que a trilha não introduziu deslocamento nem
   reescala.
2. `goToPage`/`nextPage`/`previousPage` chegam na página certa, inclusive nos
   limites (primeira e última), e `onPageChanged` dispara exatamente uma vez
   por mudança.
3. Uma peça de 7 páginas navegada do início ao fim e de volta não vaza
   `Picture` (contador de compilações e de `dispose` registrados nas notas).
4. Teste com páginas de tamanhos diferentes (fabrique um documento de teste
   com duas páginas de tamanhos distintos): as duas aparecem inteiras e
   centradas.
5. `flutter analyze` limpo, `flutter test` verde; widget-vs-harness em 0
   pixels.

## Notas de execução

Concluído em 2026-09-21. `score_bridge/lib/src/score_view.dart` (o mesmo arquivo
serve A03a/b/c: os três modos compartilham página corrente, haste e rolagem),
testes em `test/score_view_test.dart`.

- **API real**: `ScoreView(document, controller, viewController, mode,
  onPageChanged, initialPage, ...)` e `ScoreViewController` (`goToPage`,
  `nextPage`, `previousPage`, `currentPage`, `pageCount`, `mode`). `controller`
  é o `ScoreController` de cores (A01c); a navegação vai em `viewController`.
  `goToPage` fora do intervalo **satura** e devolve o índice efetivo;
  `onPageChanged` e o `notifyListeners` do controller disparam uma vez por
  mudança efetiva.
- **`nextPage`/`previousPage` têm `animate: true`** por padrão (A03b): em
  `pagedSweep` `nextPage` faz a varredura; passe `animate: false` (ou use
  `goToPage`) para o salto instantâneo de A03a.
- **Repouso pixel-idêntico (critério 1)**: 34 páginas × 2 caminhos (paginado e
  contínuo) = **0 pixels** contra o harness. Só a página corrente fica na
  árvore, centrada em escala exata (caixa do tamanho da página → escala 1,0).
  Sem `ClipRect`/`Transform` no repouso.
- **Picture (critério 3)**, Nocturne 7 páginas do início ao fim e de volta:
  `builds = 916`, `disposals = 865`, `live = 51` (só a página corrente), pico
  `live = 98` (a página mais pesada); ao desmontar `live = 0`. A vista
  soma os contadores de todas as páginas num `PictureStats` compartilhado
  (`ScorePageView.stats`, novo parâmetro).
- **Tamanhos diferentes (critério 4)**: páginas 400×600 e 900×500 numa janela
  1000×800 aparecem inteiras (escala `meet`) e centradas.
- **Achado (bug de A02b, corrigido)**: `ScoreController._syncAnimated` deixava
  presa a cor do último quadro de uma nota cujo `release` terminou enquanto
  **outras** notas ainda estavam acesas (só voltava ao repouso quando o motor
  ficava ocioso). Agora o id que terminou volta ao repouso no mesmo quadro.
  Novos: `ScoreController.highlightedIds`, `clearHighlights()` (usado no
  `seek` do player; preserva `setColor`).
- Hosts precisam de `Directionality` acima do `ScoreView` só no modo
  contínuo (`ListView`); nos paginados os `Stack` já fixam `ltr`.
