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
  sentido para 7 páginas, não para 200 (isso vem em P01, com a peça grande).
- Cada página é um `ScorePageView` com o próprio cache de `Picture`
  (A01b). A trilha é composição de widgets: nada de um `Picture` gigante com
  todas as páginas.
- Páginas podem ter **tamanhos diferentes** entre si (o formato carrega
  `widthPx`/`heightPx` por página). No corpus são todas A4, mas não assuma
  isso no layout — a trilha precisa posicionar por tamanho real.
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
       this.mode = ScorePageMode.pagedPeek,     // A03b
       this.onPageChanged,
     });
   }

   enum ScorePageMode { pagedPeek, pagedSlide, continuousScroll }

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

(a preencher por quem executar)
