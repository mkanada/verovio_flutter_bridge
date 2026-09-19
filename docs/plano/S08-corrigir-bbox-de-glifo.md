# S08 — Corrigir a escala e o eixo da bbox de glifo

**Depende de:** S04, S07 · **Decisão necessária:** não

## Objetivo

Consertar um defeito encontrado ao planejar a fase R: a bbox de todo nó que
contém glifo sai **10× maior** do que o desenho real e com o eixo Y
invertido. Como glifo é a maior parte do conteúdo visual (15 413 usos no
corpus), isso contamina a bbox de quase todo nó com `id` — e a bbox é o que
A03 (`scrollToId`) e A04 (overlays, hit-test) usam.

## Ler antes (só isto)

- `verovio/src/bridgedevicecontext.cpp`, função `GlyphBBox` no namespace
  anônimo (por volta da L221) e `CalculateNodeBBox`/`ShapeBBox` logo abaixo.
- `verovio/src/glyph.cpp` L95-L110 (`SetBoundingBox`/`GetBoundingBox`).
- `verovio/src/svgdevicecontext.cpp` `DrawMusicText` L1174-L1214 (como o
  `<use>` do SVG posiciona e escala o glifo — é a referência de verdade).
- Notas de execução de [S04](S04-bboxes-e-indice.md) (a "correção" descrita
  ali é justamente o que este passo desfaz, com a medição que faltou).

## O defeito, com a prova

`Glyph::SetBoundingBox` guarda a caixa **multiplicada por 10**:

```cpp
m_x = (int)(10.0 * x);  m_y = (int)(10.0 * y);
m_width = (int)(10.0 * w);  m_height = (int)(10.0 * h);
```

Os contornos, por outro lado, vêm do atributo `d` do XML do glifo, na escala
crua do `viewBox` daquele XML (= `unitsPerEm / 10`), e com `scale(1,-1)` já
aplicado pelo `svgpathparser` (Y para baixo). O `<use>` do SVG aplica
`scale(sx, sy)` sobre **essa** escala de contorno. Logo, a bbox e o contorno
**não estão no mesmo sistema**, e a bbox ainda está com Y para cima.

Medição que fecha o caso (257 glifos do corpus, `compare/out/s07/*.vsb`): em
todos eles o intervalo dos vértices do contorno é exatamente `bbox / 10` com
Y invertido. Exemplo `Leipzig:E050` (clave de sol): `bbox = [-10, -6550,
6470, 17380]`, vértices em x −1..646 e y −1083..655.

Efeito medido no arquivo gerado: na Gymnopédie p.1, o nó `notehead` da
primeira nota tem `bbox = [4164, 1393.6, 6424.8, 3337.6]` — 2 260 × 1 944
unidades de viewBox (226 × 194 px), quando a cabeça de nota desenhada mede
226 × 194 **unidades** (22,6 × 19,4 px). Dez vezes maior em cada eixo.

## O que fazer

1. Em `GlyphBBox`, converter a bbox do glifo para a escala do contorno e
   inverter o eixo Y antes de aplicar `use.sx`/`use.sy`:

   ```cpp
   const double bx = glyphBBox[0] / (double)DEFINITION_FACTOR;
   const double by = glyphBBox[1] / (double)DEFINITION_FACTOR;
   const double bw = glyphBBox[2] / (double)DEFINITION_FACTOR;
   const double bh = glyphBBox[3] / (double)DEFINITION_FACTOR;
   const double x0 = use.x + bx * use.sx;
   const double x1 = use.x + (bx + bw) * use.sx;
   const double y0 = use.y - (by + bh) * use.sy;   // Y do glifo aponta para cima
   const double y1 = use.y - by * use.sy;
   ```

   Substitua o comentário atual (que afirma que nenhuma divisão é
   necessária) pela explicação real, citando `Glyph::SetBoundingBox`.

2. Regerar o corpus (`-t vsb` nas 10 peças) e regravar os artefatos de
   conferência de S04 em `compare/out/` — os antigos estão errados.

3. Atualizar a [especificação](../formato/especificacao-v1.md): §4 precisa
   dizer explicitamente que `glyphs[].bbox` é `[x, y, largura, altura]`, na
   escala de `unitsPerEm` (10× a escala dos contornos) e com o eixo Y para
   cima — hoje diz só "bbox do glifo em unidades de fonte", que é o que
   induziu o erro. Acrescente uma linha ao "Histórico de revisões".

4. Corrigir o lado Dart (R01): `GlyphDef.bbox` é lido com `_asRect`
   (`Rect.fromLTRB`), o que é errado para este campo. Troque por um tipo
   próprio (`GlyphBBox(x, y, w, h)`) ou por um `Rect` já convertido para a
   escala/eixo do contorno — e diga no doc-comment qual das duas escalas o
   campo carrega.

## Fora de escopo

- Extremos exatos de Bézier na bbox (a política conservadora de S04
  continua valendo).
- Qualquer mudança na geometria desenhada — este passo **não** muda um
  pixel do render; só a bbox.

## Critérios de aceite

1. `cd verovio/tools && cmake ../cmake && make -j4` sem avisos novos.
2. Regerado o corpus, a bbox do nó `notehead` da primeira nota da Gymnopédie
   p.1 mede ~226 × 194 unidades de viewBox (e não ~2 260 × 1 944).
3. Para 20 usos de glifo sorteados em 3 peças, a bbox do nó que contém **só**
   aquele glifo bate com `x + bbox/10 * s` calculado à mão no teste
   (tolerância `1e-6`).
4. Contenção pai ⊇ filho continua sem violações em todas as páginas do
   corpus (o mesmo teste de sanidade do critério 2 de S04).
5. A ressalva do critério 2 de S04 ("bbox da raiz estoura o viewBox em 5-15%
   das páginas") é **reavaliada** com a bbox corrigida e o resultado
   registrado: se ela desaparecer, a causa era esta; se continuar, registre a
   nova margem.
6. Os PNGs do corpus continuam **byte-idênticos** aos de antes da mudança
   (prova de que a bbox não afeta o desenho) — compare com `cmp` num par de
   páginas.
7. Especificação e parser Dart atualizados; §4 e o histórico de revisões
   refletem o campo real.

## Notas de execução

- 2026-09-18: `GlyphBBox` passou a dividir os quatro valores por `DEFINITION_FACTOR`
  e inverter Y antes de aplicar `use.sx`/`use.sy`. O parser Dart passou a representar
  `glyphs[].bbox` com `GlyphBBox(x, y, width, height)` e a especificação foi atualizada
  com a escala e a conversão para o sistema dos contornos.
- **Critério 1**: `cmake ../cmake && make -j4` concluiu sem avisos na unidade alterada.
  O rebuild completo mantém avisos `-Warray-bounds` em `iohumdrum.cpp:16475`; a worktree
  S07 usada na prova visual emitiu os mesmos avisos, portanto não são novos neste passo.
- **Corpus**: regenerados 10 pacotes (`-t vsb -a -x 42`), 34 páginas; `unzip -t`
  10/10 e os 40 membros JSON dos pacotes foram parseados com sucesso. Os manifestos
  batem com as páginas e os membros dos zips.
- **Critério 2**: na Gymnopédie p.1, o primeiro `notehead` mudou de
  `[4164, 1393.6, 6424.8, 3337.6]` (2260.8 × 1944) para
  `[4164, 2244.64, 4390.08, 2439.04]` (226.08 × 194.4 unidades de viewBox).
- **Critério 3**: 20 nós com um único uso de glifo, sorteados deterministicamente em
  Gymnopédie, Chopin Étude e Maple Leaf Rag (7/7/6), batem com a fórmula do passo com
  erro máximo `0` na tolerância `1e-6`.
- **Critério 4**: nas 34 páginas, 50.544 nós e 44.859 bboxes, a contenção
  pai ⊇ filho teve **0 violações**.
- **Critério 5**: a ressalva da bbox da raiz continua: 2/34 páginas estão contidas no
  `viewBox`; 32/34 ainda estouram, tipicamente 441 unidades à esquerda e cerca de 990
  à direita, com Y normalmente em 0/-0,5 e máximo estouro vertical de 181,5. A causa
  não era apenas a escala do glifo.
- **Critério 6**: os 10 `scene.json` são idênticos entre S07 e S08 ao remover apenas os
  campos `bbox`, confirmando que a geometria desenhada não mudou. Renderizei as páginas 1
  da Chopin Étude e da Gymnopédie com o binário S07 em uma worktree temporária e comparei
  os PNGs com a saída atual via `cmp`: ambos são byte-idênticos
  (`sha256 2bac18dca1cdfd287c61001528d2c49833d4abcd73efefcdf8cc5ecf3da813cb` e
  `sha256 b398b037881949930cb7a368884adbeb8c79c2750f908d8767e4e6e28a916476`,
  respectivamente).
- **Dart**: `dart format`, `flutter analyze` e `flutter test` passaram; 21 testes
  verdes. O fixture real foi regenerado a partir do corpus S08.
- Bloqueios: nenhum.
