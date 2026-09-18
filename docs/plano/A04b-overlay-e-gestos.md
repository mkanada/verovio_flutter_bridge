# A04b — Overlay de widgets, toque e `ScoreCursor`

**Depende de:** A04a · **Decisão necessária:** não

## Objetivo

Permitir que o app ponha **widgets Flutter de verdade** sobre elementos da
partitura (cursor, alvo de toque, tooltip, marca de erro do aluno) — sem
pagar um widget por path, e sem custo nenhum para quem não usa.

## Ler antes (só isto)

- `score_bridge/lib/src/hit_test.dart` (A04a).
- `score_bridge/lib/src/score_page_view.dart` (A01b) e `score_view.dart`
  (A03).
- Requisito 4 do [`CLAUDE.md`](../../CLAUDE.md).

## Contexto que você precisa (não vá procurar, está aqui)

- Uma página tem ~1 345 formas e ~1 000 elementos indexados (mediana do
  corpus). Materializar widget por elemento é inviável e desnecessário: o
  overlay é **opt-in por id**.
- Um `GestureDetector` para a página inteira + `idAt` resolve o toque; um
  detector por nota multiplicaria a árvore por mil.
- O overlay tem que acompanhar: mudança de tamanho do widget, virada de
  página (A03b) e rolagem (A03c). Se ele for construído a partir de
  `rectForId` a cada layout, isso sai de graça; se você memorizar posições em
  pixels, não sai.
- O cursor é o caso de uso real do zywny: uma barra ou retângulo sobre a nota
  corrente, acompanhando o playback (A05).

## O que fazer

1. No `ScorePageView`/`ScoreView`:

   ```dart
   final Iterable<String> overlayIds;                  // padrão: const []
   final Widget? Function(BuildContext, String id, Rect rect)? overlayBuilder;
   final void Function(String id)? onElementTap;
   final Set<String>? tapClasses;                      // padrão: {'note'}
   ```

   Só os ids de `overlayIds` viram `Positioned`; o padrão é lista vazia —
   custo zero.

2. `ScoreCursor`: um widget pronto que recebe um id e desenha um retângulo/
   barra sobre a bbox, com cor e espessura configuráveis. Serve de exemplo e
   de teste.

3. Documentar que o overlay fica **acima** de toda a partitura (é uma camada
   de widget), portanto não participa da ordem de pintura da cena.

## Fora de escopo

- Semântica de acessibilidade da partitura (passo próprio, se for pedido).
- Hit-test por geometria exata.

## Critérios de aceite

1. **Custo zero quando não se usa**: com `overlayIds` vazio, a árvore de
   widgets tem o mesmo número de elementos que antes deste passo (conte com
   `tester.allWidgets.length` antes e depois).
2. Teste de widget: um `overlayBuilder` que desenha borda vermelha sobre 5
   notas produz uma imagem em que as bordas coincidem com os retângulos
   desenhados diretamente pelo painter nas mesmas bboxes (compare as duas
   imagens).
3. `onElementTap` devolve o id certo ao tocar no centro de 20 elementos, e não
   dispara em área vazia.
4. O overlay continua alinhado depois de mudar a largura do widget (teste com
   duas larguras) e **durante** a virada de página de A03b (capture um frame
   no meio da transição).
5. `ScoreCursor` funciona com um id de cada uma de 3 peças diferentes;
   imagem anexada nas notas.
6. `flutter analyze` limpo, `flutter test` verde; widget-vs-harness (R05c)
   continua em 0 pixels **com `overlayIds` vazio**.

## Notas de execução

(a preencher por quem executar)
