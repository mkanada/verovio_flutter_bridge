# R03a — `GlyphCache`: `glyphId` → `ui.Path`

**Depende de:** R02a, S03 · **Decisão necessária:** não

## Objetivo

Transformar o dicionário de glifos em `ui.Path` reaproveitáveis: cada
`glyphId` é convertido **uma única vez** por documento, em unidades de fonte,
e compartilhado por todas as páginas e todas as ocorrências.

## Ler antes (só isto)

- [Especificação](../formato/especificacao-v1.md), seções **4** e **4.1**.
- `score_bridge/lib/src/model.dart`: `GlyphDef` (`font`, `codepoint`,
  `unitsPerEm`, `horizAdvX`, `bbox`, `paths`) e `VsbDocument.glyphs`.
- `score_bridge/lib/src/geometry.dart` (R02a) — a conversão já existe.

## Contexto que você precisa (não vá procurar, está aqui)

- A chave é `"<fonte>:<codepoint hex maiúsculo>"`, por exemplo
  `Leipzig:E050` (clave de sol), `Leipzig:E0A4` (cabeça de nota preta).
- Os contornos já vêm **no sistema de coordenadas de tela**: o
  `transform="scale(1,-1)"` do XML do Verovio foi aplicado pelo
  `svgpathparser` na exportação. Não inverta nada aqui. Se um glifo sair de
  cabeça para baixo, o bug é em S03, não neste passo.
- Tamanho real do dicionário, medido no corpus (`compare/out/s08/*.vsb`):

  | Peça | Glifos distintos | Usos (`u`) | Razão |
  | --- | ---: | ---: | ---: |
  | Gymnopédie No.1 | 16 | 417 | 26× |
  | Prelúdio BWV 846 | 16 | 835 | 52× |
  | Maple Leaf Rag | 21 | 2 045 | 97× |
  | Grieg Little bird | 23 | 1 109 | 48× |
  | Grieg Butterfly | 24 | 1 594 | 66× |
  | Scarlatti Sonata | 25 | 1 064 | 43× |
  | Chopin Mazurka | 30 | 1 434 | 48× |
  | Clair de Lune | 31 | 2 458 | 79× |
  | Chopin Étude | 34 | 1 792 | 53× |
  | Chopin Nocturne | 37 | 2 665 | 72× |

  Em todas as peças, **todo glifo do dicionário é usado** (dicionário e
  conjunto de usados coincidem). São 15 413 usos no corpus contra no máximo
  37 `Path` por peça — é esse fator ~50× que justifica o cache.
- Cada glifo tem de 1 a 4 subpaths, com 4 a 17 vértices cada: são `Path`
  baratos de construir, mas construí-los 2 665 vezes por peça não é.

**Armadilha confirmada: `GlyphDef.bbox` NÃO está na mesma escala dos
contornos.** `paths` vem do `d` do XML do glifo (escala `unitsPerEm / 10`,
eixo Y **para baixo**, com o `scale(1,-1)` já aplicado), enquanto `bbox` vem
de `Glyph::GetBoundingBox()`, que o Verovio guarda **multiplicado por 10**
(`Glyph::SetBoundingBox`, `verovio/src/glyph.cpp` L95-L101) e no eixo Y
**para cima** da convenção SMuFL, no formato `[x, y, largura, altura]` — não
`[x0, y0, x1, y1]`. Conferido nos 257 glifos do corpus: em todos, o intervalo
dos vértices é exatamente `bbox / 10` com Y invertido. A conversão correta,
para comparar com `Path.getBounds()` em unidades de contorno, é:

```dart
// bbox = [bx, by, bw, bh], unidades de fonte x10, Y para cima
final left   = bx / 10.0;
final right  = (bx + bw) / 10.0;
final top    = -(by + bh) / 10.0;   // Y invertido
final bottom = -by / 10.0;
```

Exemplo real (`Leipzig:E050`, clave de sol): `bbox = [-10, -6550, 6470,
17380]`; os vértices do contorno vão de x −1 a 646 e de y −1083 a 655 — que é
exatamente o resultado da fórmula acima.

**Consequência**: os dois lados foram corrigidos no S08: o C++ converte a bbox
para a escala/eixo dos contornos ao calcular a bbox dos nós, e o parser Dart
representa `glyphs[].bbox` com um tipo explícito `GlyphBBox(x, y, width,
height)` (nunca `Rect`). Neste passo, **não** altere o formato nem a IR: use
a conversão acima somente ao comparar com os contornos (via
`GlyphBBox.toContourRect()`).

## O que fazer

1. `score_bridge/lib/src/glyph_cache.dart`:

   ```dart
   class GlyphCache {
     GlyphCache(this.glyphs);
     final Map<String, GlyphDef> glyphs;
     ui.Path pathFor(String glyphId);       // lazy, memoizado
     int get builtCount;                    // instrumentação para o critério 3
   }
   ```

2. O cache vive **no `VsbDocument`** (uma instância por documento), não no
   painter: várias páginas e vários painters compartilham os mesmos glifos.
   Exponha-o como `document.glyphCache` (campo `late final`).

3. `glyphId` ausente do dicionário: lance `VsbFormatException` com o id no
   caminho (`pages[p].…u.g = "Leipzig:XXXX"`) — desenhar nada silenciosamente
   esconde um bug de exportação atrás de uma partitura quase certa.

## Fora de escopo

- Desenhar a instância, escala, traço (R03b).
- Caminho de render por TTF a partir de `font`/`codepoint`/`unitsPerEm` — o
  formato carrega os metadados de propósito, mas o caminho canônico é o de
  contorno (ver `CLAUDE.md`).

## Critérios de aceite

1. `flutter analyze` limpo, `flutter test` verde.
2. Teste de bbox: para pelo menos 3 glifos do fixture,
   `pathFor(id).getBounds()` bate com o `bbox` do dicionário **depois da
   conversão documentada acima** (÷10 e Y invertido), com tolerância de
   **2 unidades de contorno** (a bbox do Verovio inclui os extremos reais das
   curvas, que podem passar dos vértices — no corpus isso só acontece em
   `Leipzig:EAA9`). Se a diferença for um fator 10, você esqueceu a divisão;
   se for um espelhamento em Y, esqueceu a inversão.
3. Teste de memoização: `pathFor` chamado 100 vezes para o mesmo id devolve a
   **mesma instância** e `builtCount` continua 1.
4. Teste no fixture real (`erik-satie.vsb`): depois de percorrer a página
   inteira pedindo o `Path` de cada uso, `builtCount == 16` (nº de entradas do
   dicionário), nunca 417 (nº de usos). Registre o número nas notas.
5. Teste de erro: `pathFor("Leipzig:FFFF")` lança `VsbFormatException` com
   mensagem que cita o id.

## Notas de execução

(a preencher por quem executar)
