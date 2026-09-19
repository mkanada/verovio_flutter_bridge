# R02b — Percurso da árvore, ajuste de página e cor herdada

**Depende de:** R02a · **Decisão necessária:** não

## Objetivo

Montar o esqueleto do `ScenePainter`: aplicar a transformação de página,
percorrer a árvore em ordem de documento mantendo a **pilha de cor** e a
**rotação**, respeitar `hidden`, e pintar apenas o **preenchimento** das
formas. Traço, opacidade e tracejado ficam para R02c; glifos para R03; texto
para R04.

## Ler antes (só isto)

- [Especificação](../formato/especificacao-v1.md), seções **3** (unidades e
  ajuste de página), **5.1** (nó) e **6** (ordem de pintura e estado herdado).
- `score_bridge/lib/src/model.dart` (R01): `ScenePage`, `PageFit`, `SceneNode`,
  `SceneRotate`, `ScenePaint` (`ScenePaint.inherit`, `ScenePaint.none`,
  `ColorPaint(hex)`), `SceneChild` e suas subclasses.
- `score_bridge/lib/src/geometry.dart` (R02a).

## Contexto que você precisa (não vá procurar, está aqui)

**Transformação de página** — nesta ordem exata, uma vez por página, antes de
percorrer a árvore (§3):

```dart
canvas.translate(fit.tx, fit.ty);
canvas.scale(fit.scale);              // escala uniforme; não use scale(sx, sy)
canvas.translate(origin.dx, origin.dy);
```

Os valores vêm prontos do arquivo (`page.fit`, `page.origin`) — **não
recalcule**; o `fit` existe justamente para que C++ e Dart não divirjam por
arredondamento. Numa página A4 típica do corpus: `viewBox = [0,0,21000,29700]`,
`widthPx/heightPx = 2100/2970`, `fit = {scale: 0.1, tx: 0, ty: 0}`,
`origin = [500, 500]`.

**Cor herdada** (§6): a pilha começa em **preto opaco** (`0xFF000000`) — é o
`color="black"` do `<svg class="definition-scale">`. Um nó com `color`
(`#rrggbb`) empilha uma cor nova para toda a sua subárvore. Formas com
`fill`/`stroke` = `ScenePaint.inherit` usam a cor do topo da pilha.

**`hidden`**: nó invisível não desenha nada, **nem os filhos**. No corpus há
116 nós `hidden`, todos de classe `note` (é a opção `showHidden` desligada).

**`rotate`**: só existe quando o Verovio chamou `RotateGraphic`. No corpus são
**8 ocorrências, todas de classe `arpeg` com ângulo −90** (1 no Nocturne
Op.9 No.1, 7 no Clair de Lune). A convenção é a do SVG `rotate(a, ox, oy)` —
graus, sentido horário com o eixo Y para baixo — e foi validada no projeto
anterior (passo D04 do `verovio_lottie`):

```dart
canvas.save();
canvas.translate(r.origin.dx, r.origin.dy);
canvas.rotate(r.angle * math.pi / 180.0);
canvas.translate(-r.origin.dx, -r.origin.dy);
// ... filhos ...
canvas.restore();
```

**Ordem**: `children` está em ordem de documento; o último pinta por cima.
Não reordene por tipo, não agrupe por cor, não "otimize" juntando formas —
qualquer reordenação vira divergência visual onde há sobreposição.

**Forma da árvore no corpus**: profundidade máxima 9; os filhos da raiz são
`mdiv pageMilestone`, `score pageMilestone`, vários `system`, `pgHead`,
`pgFoot`. 50 544 nós no corpus inteiro, dos quais 39 290 têm `id`.

## O que fazer

1. `score_bridge/lib/src/scene_painter.dart`:

   ```dart
   class ScenePainter {
     ScenePainter(this.page, this.glyphs, {this.colorOverrides = const {}});

     final ScenePage page;
     final Map<String, GlyphDef> glyphs;
     final Map<String, Color> colorOverrides;   // por xml:id; comportamento em A02

     void paint(Canvas canvas);
   }
   ```

   `colorOverrides` já entra na assinatura e já participa da herança (um id
   presente no mapa substitui a cor daquele nó e da sua subárvore), mas a
   semântica de animação é de A02 — aqui basta existir e ser respeitada.

2. Percurso recursivo com a cor corrente passada por parâmetro (não um campo
   mutável: recursão com estado em campo é a origem clássica de bug de
   restauração). Converta `#rrggbb` → `Color` **uma vez por nó**, não por
   forma.

3. Neste passo, desenhe somente o preenchimento: para cada `ScenePath`,
   `SceneRect` e `SceneEllipse`, `canvas.drawPath(shape.path, fillPaint)`
   quando `fill` não for `ScenePaint.none`. Ignore `SceneGlyphUse` e
   `SceneText` por enquanto (sem `throw`: o passo seguinte os liga).

4. Um utilitário de teste `RecordingCanvas implements Canvas` que grava as
   chamadas relevantes (`drawPath`, `save`, `restore`, `transform`,
   `translate`, `scale`, `rotate`) com a `Paint` efetiva. Ele é usado pelos
   critérios 2-5 deste passo e pelos passos seguintes — deixe-o em
   `score_bridge/test/support/recording_canvas.dart`.

## Fora de escopo

- Traço, `fillOpacity`/`strokeOpacity`, `lineCap`/`lineJoin`, `dash` (R02c).
- Glifos (R03), texto (R04).
- Camadas, `Picture`, widget (A01).

## Critérios de aceite

1. `flutter analyze` limpo, `flutter test` verde.
2. Teste do ajuste de página: para a página 1 do fixture
   `score_bridge/test/fixtures/erik-satie.vsb`, o ponto `(0, 0)` em
   coordenadas de viewBox cai, depois da transformação, exatamente em
   `(fit.tx + origin.dx * fit.scale, fit.ty + origin.dy * fit.scale)`
   (calcule o valor esperado à mão no teste, não pela mesma fórmula do
   código), e o canto `(viewBox.right, viewBox.bottom)` cai dentro de
   `widthPx × heightPx`.
3. Teste de herança de cor: árvore sintética de 3 níveis com `color` no nível
   do meio — a forma do nível 1 sai preta, a do nível 2 e a do nível 3 saem
   com a cor declarada, e uma forma com `ColorPaint` explícito ignora a
   herança. Verificado pelas `Paint` gravadas no `RecordingCanvas`.
4. Teste de `hidden`: nó `hidden` com 3 formas filhas não gera **nenhuma**
   chamada de desenho.
5. Teste de rotação: nó com `rotate {angle: -90, origin: [100, 200]}` e uma
   forma filha em `(100, 200)` → o ponto continua em `(100, 200)` e um ponto
   em `(110, 200)` vai para `(100, 190)` (confirma o sinal; se der
   `(100, 210)`, o sinal está invertido).
6. Teste de ordem: numa árvore com 5 formas, a sequência de `drawPath`
   gravada é exatamente a ordem de `children`.
7. Teste com a página real do fixture: `paint` percorre sem exceção e o número
   de `drawPath` gravados é igual ao número de formas com `fill != none`
   contadas por um percurso independente no próprio teste.

## Notas de execução

Executado em 2026-09-19. Criado `score_bridge/lib/src/scene_painter.dart`
(`ScenePainter`: ajuste de página na ordem `translate→scale→translate` com
valores prontos do arquivo, cor corrente por parâmetro — uma conversão
`#rrggbb`→`Color` por nó —, `hidden` poda a subárvore, `rotate` com
`save/translate/rotate/translate/restore`, só preenchimento de `p`/`r`/`e`;
`u`/`t` ignorados sem `throw`) e `test/support/recording_canvas.dart`
(`RecordingCanvas implements Canvas`: grava `drawPath` com `Paint` efetiva
e snapshot da afim 2D composta por pós-multiplicação; resto no-op).
`flutter analyze` sem avisos, `dart format --set-exit-if-changed .` limpo,
`flutter test` 34/34 (7 novos em `test/scene_painter_test.dart`).
DESVIO MEDIDO no critério 2: o canto `(viewBox.right, viewBox.bottom)` da
página 1 do fixture (`viewBox=[0,0,21000,29700]`, `fit={0.1,0,0}`,
`origin=[500,500]`) cai em `(2150, 3020)` — 50px além de `widthPx×heightPx`
`(2100×2970)` — porque a margem `origin` é somada depois da escala (§3);
o teste fixa os valores exatos `(50,50)` e `(2150,3020)` calculados com
literais. O conteúdo real fica dentro (bbox mais à direita do corpus:
20008.5 → 2050.85px).
