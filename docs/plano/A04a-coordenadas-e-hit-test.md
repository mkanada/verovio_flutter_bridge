# A04a — Coordenadas e hit-test: `rectForId` e `idAt`

**Depende de:** A01b, S04, S08 · **Decisão necessária:** não

## Objetivo

A conversão de coordenadas, num lugar só e testada: da bbox exportada para a
posição na tela, e de um toque na tela para o `xml:id` do elemento. Tudo que
A04b e o app fazem por cima depende destas duas funções estarem certas.

## Ler antes (só isto)

- [Especificação](../formato/especificacao-v1.md), seções **3** (ajuste de
  página) e **5.5** (índice).
- [S08](S08-corrigir-bbox-de-glifo.md) — **este passo só é confiável depois
  dela**: antes da correção, a bbox de qualquer nó com glifo sai 10× maior.
- `score_bridge/lib/src/score_page_view.dart` (A01b).

## Contexto que você precisa (não vá procurar, está aqui)

- A bbox do formato está em **unidades de viewBox, no referencial de
  conteúdo** — isto é, **antes** do `translate(origin)` da página (registrado
  nas notas de S04). A conversão para pixels lógicos do widget é:

  ```dart
  Rect toWidget(Rect bbox, ScenePage p) => Rect.fromLTRB(
    (bbox.left   + p.origin.dx) * p.fit.scale + p.fit.tx,
    (bbox.top    + p.origin.dy) * p.fit.scale + p.fit.ty,
    (bbox.right  + p.origin.dx) * p.fit.scale + p.fit.tx,
    (bbox.bottom + p.origin.dy) * p.fit.scale + p.fit.ty,
  );
  ```

  E ainda falta a transformação da trilha/rolagem de A03, se o widget for o
  `ScoreView`. Deixe a conversão de página separada da conversão de câmera.

- O índice tem uma entrada por nó com `id`: 39 290 no corpus, com as classes
  mais frequentes sendo `note` (10 068), `stem` (7 792), `accid` (5 795),
  `chord` (1 686), `beam` (1 519), `layer` (1 518), `staff` (1 230),
  `measure` (615). Uma página mediana tem ~1 000 entradas.
- **Bboxes se sobrepõem por construção** (a nota está dentro do acorde, que
  está dentro da camada, que está dentro do compasso). Por isso `idAt`
  devolve a de **menor área** — a mais específica — e aceita um filtro de
  classes para o caso comum "quero a nota, não o compasso".
- ~1 000 entradas por página cabem numa varredura linear por toque sem
  problema. Não construa um R-tree antes de medir.
- Há entradas com bbox degenerada `[0,0,0,0]` (nós com `id` sem conteúdo
  desenhável — §5.5 prevê o caso): elas nunca podem ganhar o hit-test.

## O que fazer

1. `score_bridge/lib/src/hit_test.dart` (ou um `ScoreGeometry` no pacote):

   ```dart
   Rect? rectForId(String id);                               // px lógicos do widget
   String? idAt(Offset localPosition, {Set<String>? classes});
   Iterable<String> idsIn(Rect localRect, {Set<String>? classes});
   ```

2. Um mapa `id → (página, bbox, classe)` montado **uma vez** por documento.
3. Documentar (e testar) a regra de desempate por menor área e o descarte de
   bbox degenerada.

## Fora de escopo

- Widgets de overlay e gestos (A04b).
- Hit-test por geometria exata (só se um caso real pedir; a bbox basta para
  cursor e toque).

## Critérios de aceite

1. Ida e volta: para **20 ids sorteados de 3 peças**, `rectForId` convertido
   de volta para unidades de viewBox reproduz a bbox exportada (tolerância
   `1e-6`).
2. Escala: o mesmo id em duas larguras de widget diferentes produz retângulos
   coerentes com a razão entre as escalas.
3. `idAt` no centro da bbox de 20 elementos devolve o id certo; numa área
   vazia da página devolve `null`.
4. Desempate: um ponto dentro de uma cabeça de nota devolve o id da **nota**
   (menor área), não o do compasso; com `classes: {'measure'}`, devolve o do
   compasso.
5. Nenhum id com bbox `[0,0,0,0]` é devolvido por `idAt`.
6. Conferência visual: as bboxes de 5 notas desenhadas sobre o render caem
   em volta das cabeças de nota (anexe a imagem — e compare com a imagem
   equivalente de S04, `compare/out/s04-bbox-overlay-chopin-etude-p1.png`,
   refeita com as bboxes corrigidas em 2026-09-19).
7. `flutter analyze` limpo, `flutter test` verde.

## Notas de execução

(a preencher por quem executar)
