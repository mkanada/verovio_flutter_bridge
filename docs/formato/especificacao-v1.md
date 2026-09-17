# Formato `.vsb` (Verovio Score Bridge) — especificação v1

**Status:** rascunho normativo. O passo [S01](../plano/S01-especificacao-do-formato.md)
confirma nomes/extensão com o usuário e transforma este documento na versão
final; os passos S02-S07 (exportador C++) e R01-R06 (leitor Flutter) devem
implementar **exatamente** o que está aqui. Qualquer divergência encontrada
durante a implementação se resolve **editando este documento primeiro** e
registrando a mudança em "Histórico de revisões", no fim.

## 1. Princípios

1. O formato descreve **uma cena estática por página**, mais a **identidade**
   (`xml:id` e classe) de cada elemento desenhado. **Não** descreve animação:
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

## 2. Empacotamento

| Formato de saída | Arquivo | Conteúdo |
| --- | --- | --- |
| `-t vsb` | `<nome>.vsb` (zip) | `manifest.json`, `scene.json`, `glyphs.json`, `timemap.json` (se disponível) |
| `-t vsb-json` | `<nome>.json` | um único JSON com `manifest`, `glyphs` e `scene` embutidos (depuração; diffável) |

`manifest.json`:

```json
{
  "format": "vsb",
  "version": 1,
  "generator": "verovio 6.3.0 / bridge 1",
  "pageCount": 4,
  "files": { "scene": "scene.json", "glyphs": "glyphs.json", "timemap": "timemap.json" }
}
```

## 3. Unidades e ajuste de página

Todas as coordenadas de desenho estão em **unidades de viewBox** — exatamente
o que o `DeviceContext` recebe (unidades de definição do Verovio,
`DEFINITION_FACTOR = 10` por px lógico), com o eixo Y apontando para baixo.
Nada é arredondado na exportação.

Cada página carrega o ajuste já calculado, reproduzindo a semântica do
`<svg class="definition-scale">` do Verovio
(`preserveAspectRatio="xMidYMid meet"`, ver `src/svgdevicecontext.cpp`
`SvgDeviceContext::StartPage`):

```
vw = width * viewBoxFactor
vh = contentHeight * viewBoxFactor
widthPx  = baseWidth  ou ceil(width  * userScaleX)
heightPx = baseHeight ou ceil(height * userScaleY)
scale = min(widthPx / vw, heightPx / vh)
tx = (widthPx  - vw * scale) / 2
ty = (heightPx - vh * scale) / 2
```

O renderizador aplica `translate(tx, ty)` e `scale(scale)` uma vez por página,
e depois `translate(origin)` (a translação `page-margin` do SVG) antes de
desenhar a árvore. **Esses valores vão prontos no arquivo** (`fit`), para que
C++ e Dart nunca divirjam por arredondamento.

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
      { "closed": true,
        "v": [x0,y0, x1,y1, ...],
        "i": [x0,y0, x1,y1, ...],
        "o": [x0,y0, x1,y1, ...] }
    ]
  }
}
```

- A chave é `"<fonte>:<codepoint hex maiúsculo>"`.
- `paths` está em **unidades de fonte**, já com o `transform="scale(1,-1)"` do
  XML do Verovio aplicado (é o que o `svgpathparser` faz hoje) — ou seja, o
  contorno já está no sistema de coordenadas de tela, bastando escalar.
- `v`/`i`/`o` são arrays **planos** de números (pares x,y): `v` = vértices,
  `i` = tangente de entrada **relativa ao vértice**, `o` = tangente de saída
  relativa ao vértice (mesma convenção do Lottie e da IR existente). Os três
  arrays têm o mesmo comprimento.
- `font`, `codepoint`, `unitsPerEm` e `horizAdvX` existem para permitir um
  segundo caminho de render por TTF no futuro. O caminho **canônico** — e o
  único que precisa bater a paridade — é o dos contornos.

### 4.1 Conversão para `Path` (normativo)

```
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
      "width": 2100, "height": 2970, "contentHeight": 2970,
      "viewBoxFactor": 10.0,
      "viewBox": [0, 0, 21000, 29700],
      "widthPx": 2100, "heightPx": 2970,
      "fit": { "scale": 0.1, "tx": 0.0, "ty": 0.0 },
      "origin": [500, 500],
      "root": { ... nó ... }
    }
  ]
}
```

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
  "children": [ ... ]
}
```

- `id` — o `xml:id` do objeto (ausente quando o Verovio não emite um id
  primário). É a chave usada pelo host para colorir/animar.
- `class` — `Object::GetClassName()` (+ classes extras) ou o nome do grupo
  customizado, como no `class=` do SVG.
- `color` — cor CSS resolvida (`@color` do MEI ou `SetCustomGraphicColor`).
  Ausente = herda do ancestral.
- `hidden` — `true` quando o grupo está invisível (`g.CSS_SHOW_HIDDEN` / opção
  `showHidden` desligada); o renderizador **não desenha** e não conta na bbox.
- `rotate` — presente só quando `RotateGraphic` foi chamado; ângulo em graus,
  pivô em unidades de viewBox, mesma convenção do SVG (`rotate(a, ox, oy)`).
- `bbox` — união das bboxes dos filhos, em unidades de viewBox, **depois** de
  transformações locais. Emitida para todo nó com `id` e para nós de classe
  `measure`, `staff`, `system` e `page` (ver S04); opcional nos demais.
- `children` — ordem de documento: o **último pinta por cima**.

### 5.2 Formas

Todas aceitam `fill`, `fillOpacity`, `stroke`, `strokeWidth`, `strokeOpacity`,
`lineCap`, `lineJoin`, `dash` (`[traço, intervalo]`). `fill`/`stroke` ausentes
significam **herdar** a cor corrente; `"none"` significa não pintar aquele
canal. Por padrão o Verovio aplica `stroke:currentColor` a `path`, `polygon`,
`polyline`, `rect` e `ellipse` (regra CSS global do SVG) — o exportador já
resolve isso em `stroke` + `strokeWidth`.

```json
{ "t": "p", "paths": [ { "closed": true, "v": [...], "i": [...], "o": [...] } ] }
{ "t": "r", "x": 0, "y": 0, "w": 100, "h": 20, "rx": 0 }
{ "t": "e", "cx": 0, "cy": 0, "rx": 50, "ry": 50 }
```

### 5.3 Uso de glifo

```json
{ "t": "u", "g": "Leipzig:E0A4", "x": 12000, "y": 4300, "sx": 3.2, "sy": 3.2 }
```

- `sx`/`sy` = `pointSize / unitsPerEm * DEFINITION_FACTOR` (com
  `widthToHeightRatio` aplicado em `sx` quando != 1), exatamente como
  `MakeGlyphShape` calcula hoje.
- A largura de traço herdada do SVG para glifos é `strokeWidth = sy`, e
  `fill`/`stroke` herdam a cor corrente — o renderizador aplica isso por
  padrão; um `fill`/`stroke` explícito no objeto sobrepõe.

### 5.4 Run de texto comum

```json
{ "t": "t", "s": "Andante", "x": 8000, "y": 2100,
  "size": 360.0, "align": "left|center|right",
  "letterSpacing": 0.0, "bold": false, "italic": true,
  "family": "Liberation Serif" }
```

- `size` já está em unidades de viewBox (mesma escala da geometria).
- `align` reproduz o `text-anchor` do SVG (`start`/`middle`/`end`).
- `bold`/`italic` são o resultado **final** (atributo do `FontInfo` **ou** regra
  CSS por classe do ancestral), resolvido na exportação.
- Runs cujos caracteres são todos codepoints SMuFL cobertos pelas fontes do
  projeto **não** viram `t`: viram usos de glifo (`u`), como decidido em D01-6
  do projeto anterior.

## 6. Ordem de pintura e estado herdado

O renderizador percorre a árvore em profundidade, na ordem de `children`,
mantendo uma pilha de:

- **cor corrente** (inicial: preto, `#000000` — o `color="black"` do
  `<svg class="definition-scale">`);
- **transformação** (só `rotate` altera; não há outras transformações de nó).

Nenhum outro estado é herdado. Não há clipping, máscara, gradiente ou filtro
no formato v1 (o Verovio não emite nenhum deles nas saídas do corpus).

## 7. Compatibilidade

- `version` inteiro. Um leitor que encontre `version` maior que o que conhece
  deve falhar com mensagem clara, nunca renderizar parcialmente.
- Chaves desconhecidas em nós/formas devem ser **ignoradas** pelo leitor (para
  permitir campos novos aditivos sem quebrar versões antigas).

## Histórico de revisões

| Data | Mudança |
| --- | --- |
| (a preencher em S01) | versão inicial |
