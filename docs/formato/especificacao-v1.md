# Formato `.vsb` (Verovio Score Bridge) — especificação v1

**Status:** normativo, fechado em S01. Os passos S02-S07 (C++) e R01-R06
(Dart) devem implementar exatamente este contrato. Uma divergência encontrada
durante a implementação é resolvida editando este documento primeiro e
registrando a mudança em [Histórico de revisões](#histórico-de-revisões).

## 1. Princípios

1. O formato descreve **uma cena estática por página**, mais a identidade
   (`xml:id` e classe) de cada elemento desenhado. Não descreve animação:
   animação é responsabilidade do renderizador Flutter.
2. O formato é uma transcrição fiel do que o `View` do Verovio manda para o
   `DeviceContext` — o mesmo fluxo que gera o SVG. Nada é reinterpretado.
3. Estilo (bold/italic por classe CSS, `stroke:currentColor`) é **resolvido na
   exportação**. O leitor não interpreta CSS.
4. Cor é **herdada**, como no SVG: um nó pode declarar `color`; formas sem
   `fill`/`stroke` explícitos usam a cor herdada do ancestral mais próximo.
   Trocar a cor de uma nota em runtime = trocar uma cor só, no nó da nota.
5. Geometria repetida (glifos) aparece **uma vez** num dicionário; cada uso é
   uma referência com posição e escala.
6. As coordenadas são unidades de viewBox do Verovio (`DEFINITION_FACTOR = 10`
   por px lógico), com o eixo Y apontando para baixo.

## 2. Empacotamento e documentos JSON

O nome do formato é **Verovio Score Bridge**, a extensão é **`.vsb`**, e as
flags de saída são:

- `-t vsb`: pacote zip com extensão `.vsb`;
- `-t vsb-json`: um único JSON com extensão `.json`, destinado à depuração e a
  diffs.

| Formato de saída | Arquivo | Conteúdo |
| --- | --- | --- |
| `-t vsb` | `<nome>.vsb` (zip) | `manifest.json`, `scene.json`, `glyphs.json` e, quando disponível, `timemap.json` |
| `-t vsb-json` | `<nome>.json` | um objeto JSON com `manifest`, `glyphs`, `scene` e, quando disponível, `timemap` |

O `timemap.json` é **embutido no pacote** quando o Verovio produz um timemap
não vazio. Se a peça não produzir timemap, o arquivo e a entrada correspondente
no manifest são omitidos; nunca é gravado um timemap vazio. No JSON único, o
mesmo array é colocado na propriedade `timemap`.

### 2.1 `manifest.json`

```json
{
  "format": "vsb",
  "version": 1,
  "generator": "verovio 6.3.0 / bridge 1",
  "pageCount": 4,
  "files": {
    "scene": "scene.json",
    "glyphs": "glyphs.json",
    "timemap": "timemap.json"
  }
}
```

- `format` é sempre `"vsb"`.
- `version` é o inteiro `1`.
- `generator` identifica a versão do Verovio e do bridge que produziu o
  documento.
- `pageCount` é o número de páginas em `scene.pages`.
- `files.scene` e `files.glyphs` são obrigatórios. `files.timemap` existe somente
  quando o pacote contém `timemap.json`.
- No JSON único, `manifest.files` mantém os nomes lógicos acima mesmo sem
  arquivos físicos separados.

### 2.2 JSON único

A raiz de `-t vsb-json` é:

```json
{
  "manifest": { "...": "manifest.json" },
  "glyphs": { "...": "dicionário de glifos" },
  "scene": { "pages": [] },
  "timemap": []
}
```

`timemap` é opcional e segue exatamente o conteúdo de `timemap.json`. O parser
deve aceitar tanto a raiz única quanto os documentos individuais `scene.json`,
`glyphs.json`, `manifest.json` e `timemap.json`.

## 3. Unidades e ajuste de página

Todas as coordenadas de desenho estão em **unidades de viewBox** — exatamente
o que o `DeviceContext` recebe (unidades de definição do Verovio,
`DEFINITION_FACTOR = 10` por px lógico), com o eixo Y apontando para baixo.
Nenhum arredondamento adicional é aplicado; a serialização canônica limita os
números a no máximo 6 dígitos significativos.

Cada página carrega o ajuste já calculado, reproduzindo a semântica do
`<svg class="definition-scale">` do Verovio
(`preserveAspectRatio="xMidYMid meet"`, ver `src/svgdevicecontext.cpp`
`SvgDeviceContext::StartPage`):

```text
vw = width * viewBoxFactor
vh = contentHeight * viewBoxFactor
widthPx  = baseWidth  ou ceil(width  * userScaleX)
heightPx = baseHeight ou ceil(height * userScaleY)
scale = min(widthPx / vw, heightPx / vh)
tx = (widthPx  - vw * scale) / 2
ty = (heightPx - vh * scale) / 2
```

Em modo fac-símile, o `viewBox` do SVG usa `[0, 0, width, height]`; nos demais
modos usa `[0, 0, width * viewBoxFactor, contentHeight * viewBoxFactor]`. O
cálculo de `fit` usa as dimensões gravadas em `viewBox`, reproduzindo exatamente
essa escolha do `StartPage`.

O renderizador aplica `translate(tx, ty)`, `scale(scale)` e depois
`translate(origin)` uma vez por página, antes de percorrer a árvore. Os valores
de `fit` vão prontos no arquivo para que C++ e Dart nunca divirjam por
arredondamento.

## 4. `glyphs.json` — dicionário de glifos

```json
{
  "Leipzig:E0A4": {
    "font": "Leipzig",
    "codepoint": "E0A4",
    "unitsPerEm": 2048,
    "horizAdvX": 656,
    "bbox": [-10, -262, 552, 262],
    "paths": [
      {
        "closed": true,
        "v": [x0, y0, x1, y1],
        "i": [0, 0, 0, 0],
        "o": [0, 0, 0, 0]
      }
    ]
  }
}
```

- A chave é `"<fonte>:<codepoint hex maiúsculo>"`.
- `paths` está em **unidades de fonte**, já com o `transform="scale(1,-1)"` do
  XML do Verovio aplicado (é o que o `svgpathparser` faz hoje). O contorno já
  está no sistema de coordenadas de tela, bastando escalá-lo.
- `v`/`i`/`o` são arrays **planos** de números (pares x,y): `v` = vértices,
  `i` = tangente de entrada relativa ao vértice, `o` = tangente de saída
  relativa ao vértice. Os três arrays têm o mesmo comprimento e cada um tem
  comprimento par.
- `font`, `codepoint`, `unitsPerEm`, `horizAdvX` e `bbox` vêm dos metadados do
  `Glyph` do Verovio. Eles permitem um segundo caminho de render por TTF no
  futuro. O caminho canônico — e o único que precisa bater a paridade — é o dos
  contornos.

### 4.1 Conversão para `Path` (normativo)

```text
moveTo(v[0])
para k de 0 até n-2:
    cubicTo(v[k] + o[k], v[k+1] + i[k+1], v[k+1])
se closed:
    cubicTo(v[n-1] + o[n-1], v[0] + i[0], v[0]); close()
```

## 5. `scene.json` — páginas e árvore

```json
{
  "pages": [
    {
      "index": 0,
      "width": 2100,
      "height": 2970,
      "contentHeight": 2970,
      "viewBoxFactor": 10.0,
      "viewBox": [0, 0, 21000, 29700],
      "baseWidth": 2100,
      "baseHeight": 2970,
      "userScaleX": 1.0,
      "userScaleY": 1.0,
      "widthPx": 2100,
      "heightPx": 2970,
      "fit": { "scale": 0.1, "tx": 0.0, "ty": 0.0 },
      "origin": [500, 500],
      "root": { "...": "nó" }
    }
  ]
}
```

Todos os campos vindos de `LottiePage` são serializados. `viewBox`,
`widthPx`/`heightPx` e `fit` são derivados, mas também são gravados para que o
leitor não refaça a métrica da página.

### 5.1 Nó (grupo)

```json
{
  "t": "g",
  "id": "note-0000001386",
  "class": "note",
  "color": "#ff0000",
  "hidden": false,
  "rotate": { "angle": -45.0, "origin": [1200, 3400] },
  "bbox": [x0, y0, x1, y1],
  "children": []
}
```

- `id` — o `xml:id` do objeto (ausente quando o Verovio não emite um id
  primário). É a chave usada pelo host para colorir/animar.
- `class` — `Object::GetClassName()` (+ classes extras) ou o nome do grupo
  customizado, como no `class=` do SVG.
- `color` — cor CSS resolvida (`@color` ou `SetCustomGraphicColor`), normalizada
  para `#rrggbb` minúsculo. Ausente = herda do ancestral.
- `hidden` — `true` quando o grupo está invisível (`g.CSS_SHOW_HIDDEN` / opção
  `showHidden` desligada); o renderizador não desenha e não conta na bbox.
- `rotate` — presente somente quando `RotateGraphic` foi chamado; ângulo em
  graus e pivô em unidades de viewBox, na convenção do SVG
  `rotate(a, ox, oy)`.
- `bbox` — união das bboxes dos filhos em unidades de viewBox, depois das
  transformações locais. É emitida para todo nó com `id` e para nós de classe
  `measure`, `staff`, `system` e `page`; é opcional nos demais.
- `children` — ordem de documento: o último pinta por cima.

### 5.2 Formas

Todas aceitam os campos de estilo comuns `fill`, `fillOpacity`, `stroke`,
`strokeWidth`, `strokeOpacity`, `lineCap`, `lineJoin` e `dash` (`[traço,
intervalo]`).

- `fill`/`stroke` ausentes significam **herdar** a cor corrente.
- `"none"` significa não pintar aquele canal.
- `fillOpacity`/`strokeOpacity` ficam no intervalo `[0, 1]`.
- `lineCap` usa `default`, `butt`, `round` ou `square`.
- `lineJoin` usa `default`, `arcs`, `bevel`, `miter`, `miter-clip` ou `round`.
- `dash` é omitido quando não há tracejado; quando presente, seus dois números
  são `dashLength` e `gapLength`.
- Por padrão o Verovio aplica `stroke:currentColor` a `path`, `polygon`,
  `polyline`, `rect` e `ellipse` (regra CSS global do SVG). O exportador resolve
  isso em `stroke` + `strokeWidth`.

```json
{ "t": "p", "paths": [{ "closed": true, "v": [], "i": [], "o": [] }] }
{ "t": "r", "x": 0, "y": 0, "w": 100, "h": 20, "rx": 0 }
{ "t": "e", "cx": 0, "cy": 0, "rx": 50, "ry": 50 }
```

`LottieShape.hasFill` e `hasStroke` controlam a presença de `fill` e `stroke`:
`false` vira `"none"`; `true` com cor `COLOR_NONE` omite o campo (herança);
`true` com cor explícita vira `#rrggbb`. `fillOpacity` e `strokeOpacity` são
omitidos quando valem `1.0`.

### 5.3 Uso de glifo

```json
{ "t": "u", "g": "Leipzig:E0A4", "x": 12000, "y": 4300, "sx": 3.2, "sy": 3.2 }
```

- `sx`/`sy` = `pointSize / unitsPerEm * DEFINITION_FACTOR`, com
  `widthToHeightRatio` aplicado em `sx` quando diferente de 1, exatamente como
  `MakeGlyphShape` calcula hoje.
- A largura de traço herdada do SVG para glifos é `strokeWidth = sy`; `fill` e
  `stroke` herdam a cor corrente. Um `fill`/`stroke` explícito no objeto
  sobrepõe.
- `u` substitui o baking de contorno no formato final: os contornos ficam no
  dicionário e cada ocorrência é uma referência.

### 5.4 Run de texto comum

```json
{
  "t": "t",
  "s": "Andante",
  "x": 8000,
  "y": 2100,
  "size": 360.0,
  "align": "left",
  "letterSpacing": 0.0,
  "bold": false,
  "italic": true,
  "family": "Liberation Serif"
}
```

- `s` vem de `LottieTextRun.text`.
- `x`/`y` vêm de `origin`, antes do deslocamento de alinhamento.
- `align` usa `left`, `center` ou `right`, mapeados respectivamente para
  `text-anchor=start`, `middle` e `end`. `none` e `justify` são normalizados para
  `left` pelo exportador.
- `size` já está em unidades de viewBox.
- `letterSpacing` vem de `letterSpacing` e é `0.0` quando ausente no font state.
- `bold` e `italic` são o resultado final: `FONTWEIGHT_bold` vira `bold: true`,
  `FONTSTYLE_italic`/`oblique` vira `italic: true`, e as regras CSS por classe
  dos ancestrais já foram aplicadas.
- `family` vem do `FontInfo` ativo no momento do run; não é inventada pelo
  leitor. O valor é o nome da família/TTF que o renderizador deve usar.
- `color` segue a mesma regra de herança dos nós.
- Runs cujos caracteres são todos codepoints SMuFL cobertos pelas fontes do
  projeto não viram `t`: viram usos de glifo (`u`).

## 6. Ordem de pintura e estado herdado

O renderizador percorre a árvore em profundidade, na ordem de `children`,
mantendo uma pilha de:

- **cor corrente** (inicial: preto, `#000000` — o `color="black"` do
  `<svg class="definition-scale">`);
- **transformação** (só `rotate` altera; não há outras transformações de nó).

Nenhum outro estado é herdado. Não há clipping, máscara, gradiente ou filtro
no formato v1 (o Verovio não emite nenhum deles nas saídas do corpus).

## 7. Serialização canônica

Para que duas exportações da mesma peça sejam comparáveis:

- números usam no máximo 6 dígitos significativos, separador decimal `.` e
  não usam notação científica; inteiros são gravados sem `.0`, e `-0` vira `0`;
- cores explícitas usam `#rrggbb` minúsculo;
- `COLOR_NONE` remove o campo de cor correspondente;
- a ordem das chaves é a ordem apresentada nesta especificação;
- dicionários de glifos são ordenados por `glyphId`;
- `timemap` é omitido quando indisponível, em vez de receber um valor vazio.

## 8. Correspondência IR ↔ formato

A tabela abaixo cobre campo a campo a IR de
[`lottiegeometry.h`](../../verovio/include/vrv/lottiegeometry.h). Os campos
derivados ou vindos de estruturas auxiliares (`Glyph`, `FontInfo`, S03/S04 e
empacotamento) estão indicados explicitamente.

| Tipo/campo da IR | Campo JSON | Regra de correspondência |
| --- | --- | --- |
| `LottieVec.x` | pares x em `v`/`i`/`o`, `origin`, `bbox`, `fit`, `viewBox` etc. | coordenada horizontal em unidades de viewBox ou de fonte, conforme o objeto |
| `LottieVec.y` | pares y nos mesmos arrays/objetos | coordenada vertical; eixo Y para baixo |
| `LottieBezier.v` | `paths[].v` | vértices em array plano de pares |
| `LottieBezier.i` | `paths[].i` | tangentes de entrada relativas ao vértice |
| `LottieBezier.o` | `paths[].o` | tangentes de saída relativas ao vértice |
| `LottieBezier.closed` | `paths[].closed` | booleano de fechamento do subpath |
| `LottieShape.kind` | `t` da forma (`p`, `r` ou `e`) | `Path` → `p`, `Rect` → `r`, `Ellipse` → `e` |
| `LottieShape.paths` | `p.paths` | subpaths compartilhando o mesmo fill |
| `LottieShape.center` | `r.x/y/w/h` ou `e.cx/cy` | centro convertido para canto superior esquerdo no retângulo; centro direto na elipse |
| `LottieShape.size` | `r.w/h` ou `e.rx/ry` | tamanho direto no retângulo; metade do tamanho nos raios da elipse |
| `LottieShape.radius` | `r.rx` | raio dos cantos; `0` quando não arredondado |
| `LottieShape.hasFill` | presença/valor de `fill` | `false` → `"none"`; `true` + `COLOR_NONE` → ausente; `true` + cor → hex |
| `LottieShape.fillColor` | `fill` | cor resolvida em `#rrggbb`, ou ausente para herança |
| `LottieShape.fillOpacity` | `fillOpacity` | omitido quando `1.0` |
| `LottieShape.hasStroke` | presença/valor de `stroke` | `false` → `"none"`; `true` + `COLOR_NONE` → ausente; `true` + cor → hex |
| `LottieShape.strokeWidth` | `strokeWidth` | largura em unidades de viewBox; padrão IR `1.0` |
| `LottieShape.strokeColor` | `stroke` | cor resolvida em `#rrggbb`, ou ausente para herança |
| `LottieShape.strokeOpacity` | `strokeOpacity` | omitido quando `1.0` |
| `LottieShape.lineCap` | `lineCap` | enum normalizado para `default`, `butt`, `round` ou `square` |
| `LottieShape.lineJoin` | `lineJoin` | enum normalizado para `default`, `arcs`, `bevel`, `miter`, `miter-clip` ou `round` |
| `LottieShape.dashLength` | `dash[0]` | presente somente quando maior que zero |
| `LottieShape.gapLength` | `dash[1]` | intervalo correspondente; usa o valor resolvido da IR |
| `LottieTextRun.text` | `t.s` | string UTF-8/JSON do run comum |
| `LottieTextRun.origin` | `t.x`, `t.y` | âncora antes do offset de alinhamento |
| `LottieTextRun.alignment` | `t.align` | `left`/`center`/`right`; `none` e `justify` normalizados para `left` |
| `LottieTextRun.pointSize` | `t.size` | tamanho já convertido para unidades de viewBox |
| `LottieTextRun.letterSpacing` | `t.letterSpacing` | espaçamento entre caracteres; `0.0` quando não usado |
| `LottieTextRun.style` | `t.italic` | `italic`/`oblique` → `true`; `normal`/`none` → `false`, após CSS |
| `LottieTextRun.weight` | `t.bold` | `bold` → `true`; `normal`/`none` → `false`, após CSS |
| `LottieTextRun.color` | `t.color` | cor explícita ou ausente para `COLOR_NONE` (herança) |
| `LottieChild.group` | item `children[]` com `t: "g"` | subgrupo; os campos do `LottieNode` entram no mesmo objeto |
| `LottieChild.text` | item `children[]` com `t: "t"` | run de texto comum |
| `LottieChild.shape` | item `children[]` com `t: "p"`, `"r"` ou `"e"` | forma; o discriminante vem de `kind` |
| `LottieNode.id` | `g.id` | `xml:id` primário; ausente quando vazio |
| `LottieNode.className` | `g.class` | classes/nome do grupo |
| `LottieNode.colorCss` | `g.color` | CSS color resolvido e normalizado; ausente quando vazio |
| `LottieNode.hidden` | `g.hidden` | booleano de visibilidade |
| `LottieNode.hasRotation` | presença de `g.rotate` | `false` → campo ausente; `true` → objeto presente |
| `LottieNode.rotation` | `g.rotate.angle` | ângulo em graus |
| `LottieNode.rotationOrigin` | `g.rotate.origin` | pivô `[x, y]` |
| `LottieNode.children` | `g.children` | ordem de documento; o último filho pinta por cima |
| `LottiePage.root` | `pages[].root` | raiz da árvore da página |
| `LottiePage.width` | `pages[].width` | largura lógica da página |
| `LottiePage.height` | `pages[].height` | altura lógica da página |
| `LottiePage.contentHeight` | `pages[].contentHeight` | altura usada no viewBox vertical |
| `LottiePage.baseWidth` | `pages[].baseWidth` | largura base usada por `ComputePageMetrics` |
| `LottiePage.baseHeight` | `pages[].baseHeight` | altura base usada por `ComputePageMetrics` |
| `LottiePage.userScaleX` | `pages[].userScaleX` | escala horizontal de entrada |
| `LottiePage.userScaleY` | `pages[].userScaleY` | escala vertical de entrada |
| `LottiePage.viewBoxFactor` | `pages[].viewBoxFactor` | fator de conversão para o viewBox |
| `LottiePage.originX` | `pages[].origin[0]` | translação `page-margin` em X |
| `LottiePage.originY` | `pages[].origin[1]` | translação `page-margin` em Y |
| derivado de `width/contentHeight/viewBoxFactor` | `pages[].viewBox` | `[0, 0, width * factor, contentHeight * factor]` |
| derivado de `baseWidth/baseHeight/userScale*` | `pages[].widthPx`, `heightPx` | tamanho de saída da página |
| derivado de todos os campos acima | `pages[].fit` | `scale`, `tx`, `ty` pré-computados |
| metadados de `Glyph` (fora da IR de cena) | `glyphs[...].font/codepoint/unitsPerEm/horizAdvX/bbox` | dicionário de contornos e futuro caminho TTF |
| `FontInfo` ativo (fora de `LottieTextRun`) | `t.family` | família/TTF do texto comum |
| S03 | `t: "u"` e `glyphs` | substitui contornos assados por referência ao dicionário |
| S04 | `bbox` e índice por `id` | bounding boxes exportadas para overlay/navegação |
| empacotamento | `manifest`, `timemap` | nomes, versão, páginas e timemap embutido |

## 9. Compatibilidade

- `version` é inteiro. Um leitor que encontre `version` maior que o que conhece
  deve falhar com mensagem clara, nunca renderizar parcialmente.
- Chaves desconhecidas em nós/formas devem ser ignoradas pelo leitor (para
  permitir campos novos aditivos sem quebrar versões antigas).
- O schema JSON Schema draft 2020-12 que acompanha esta especificação é o
  critério mecânico de forma para o fixture e para as saídas dos passos
  seguintes.

## Histórico de revisões

| Data | Mudança |
| --- | --- |
| 2026-09-17 | S01: formato nomeado Verovio Score Bridge (`.vsb`), flags `-t vsb`/`-t vsb-json`, timemap embutido quando disponível, exemplo mínimo, schema v1 e correspondência completa da IR. |
