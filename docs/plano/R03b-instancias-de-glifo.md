# R03b — Instâncias `u`: transformação, traço e herança

**Depende de:** R03a, R02c · **Decisão necessária:** não

## Objetivo

Desenhar cada ocorrência de glifo: o mesmo `ui.Path` do dicionário sob
`translate(x, y) scale(sx, sy)`, preenchido **e traçado** com a cor herdada.
É a maior parte da tinta de uma partitura.

## Ler antes (só isto)

- [Especificação](../formato/especificacao-v1.md), seção **5.3**.
- `verovio/src/svgdevicecontext.cpp` `DrawMusicText` L1174-L1214 — é o
  `<use>` que este passo reproduz.
- `score_bridge/lib/src/scene_painter.dart` (R02b/R02c) e
  `glyph_cache.dart` (R03a).

## Contexto que você precisa (não vá procurar, está aqui)

O SVG emite, para cada caractere SMuFL:

```xml
<use href="#E0A3-xxxx" transform="translate(4164, 2344) scale(0.72, 0.72)"/>
```

e o `<path>` referenciado, dentro de `<defs>`, cai sob a regra CSS global
`ellipse, path, polygon, polyline, rect {stroke:currentColor}` — ou seja,
**o glifo é preenchido e também traçado**, com largura 1 no espaço do
contorno. Isso foi validado no projeto anterior: sem o traço, os glifos saem
visivelmente mais finos que no SVG (é uma divergência de alguns por cento no
diff, não um detalhe).

Portanto:

```dart
canvas.save();
canvas.translate(use.x, use.y);
canvas.scale(use.sx, use.sy);
canvas.drawPath(glyphPath, fillPaint);                    // cor herdada
canvas.drawPath(glyphPath, strokePaint..strokeWidth = 1); // 1 em espaço de glifo
canvas.restore();
```

`strokeWidth: 1.0` **dentro** do `save/scale` equivale a `sy` em unidades de
viewBox — que é exatamente o que §5.3 documenta. Não faça a conta à mão fora
do `scale`: é a mesma coisa e uma fonte a menos de erro.

Fatos medidos no corpus (15 413 usos de glifo):

- **Nenhum** uso traz `fill`, `stroke` ou `strokeWidth` explícitos — 100%
  herdam. O caminho de override precisa existir (§5.3 permite), mas não tem
  caso de teste real: teste com um `SceneGlyphUse` sintético.
- `sx` e `sy` são iguais em todo o corpus (o `widthToHeightRatio` só difere
  de 1 em casos raros, como texto condensado); ainda assim use os dois
  separadamente — `scale(use.sx, use.sy)`, nunca `scale(use.sx)`.
- Valor típico de escala: 0,72 (cabeça de nota a `pointSize` padrão).
- `SceneGlyphUse` **estende `SceneShape`** no modelo de R01, então já carrega
  `fill`/`stroke`/`strokeWidth`/opacidades — reaproveite a mesma resolução de
  `Paint` de R02c em vez de escrever uma segunda.

## O que fazer

1. Ligar o ramo `SceneGlyphUse` do percurso de R02b ao `GlyphCache`.
2. Resolver `fill`/`stroke`: `ScenePaint.inherit` (o caso de 100% do corpus)
   → cor corrente; explícito → sobrepõe; `none` → não pinta aquele canal.
3. `strokeWidth` do uso: quando ausente (sempre, no corpus), **1,0 no espaço
   do glifo**. Quando presente, o valor está em unidades de viewBox — divida
   por `sy` antes de usar dentro do `scale`, e documente isso no código.
4. Reutilizar o mesmo `Paint` entre usos consecutivos com a mesma cor (evite
   alocar duas `Paint` por glifo; são 2 665 glifos numa página do Nocturne).

## Fora de escopo

- Texto comum (R04) — inclusive runs que "parecem" SMuFL: o exportador já os
  converteu em `u`.
- Medir paridade (R03c).

## Critérios de aceite

1. `flutter analyze` limpo, `flutter test` verde.
2. Teste de posicionamento: um `SceneGlyphUse` sintético de `Leipzig:E0A3`
   em `(4164, 2344)` com `sx = sy = 0.72` produz um `Path` transformado cujo
   `getBounds()` bate com a bbox convertida do dicionário (fórmula de R03a:
   `x + bbox/10 * s`, Y invertido) com tolerância de 1 unidade de viewBox.
3. Teste de traço: o `RecordingCanvas` mostra **dois** `drawPath` por uso
   (fill + stroke) e o `Paint` de traço tem `strokeWidth == 1.0` dentro do
   `scale` ativo.
4. Teste de herança: um uso dentro de um nó com `color: "#ff0000"` sai
   vermelho nos dois `drawPath`; um uso com `fill` explícito ignora a
   herança só no preenchimento.
5. Teste de contagem: renderizar a página inteira do fixture chama
   `GlyphCache.pathFor` 417 vezes (nº de usos) mas constrói 16 `Path`
   (nº de entradas do dicionário). Registre os dois números nas notas.

## Notas de execução

(a preencher por quem executar)
