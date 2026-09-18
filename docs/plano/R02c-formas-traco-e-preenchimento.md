# R02c — Formas: traço, opacidade, `lineCap`/`lineJoin` e tracejado

**Depende de:** R02b · **Decisão necessária:** não

## Objetivo

Completar a pintura das formas geométricas: traço com a largura resolvida
pelo exportador, `fill`/`stroke` explícitos, opacidades, pontas e junções de
linha, e tracejado. Ao fim deste passo a página já tem pentagramas, hastes,
barras de compasso, ligaduras, feixes e colchetes — tudo menos glifos e texto.

## Ler antes (só isto)

- [Especificação](../formato/especificacao-v1.md), seção **5.2** (campos de
  estilo e a regra de `fill`/`stroke` ausente) e a tabela de §8 nas linhas
  `BridgeShape.*`.
- `verovio/src/svgdevicecontext.cpp`, primitivas L686-L1017, só se houver
  dúvida de semântica.
- `score_bridge/lib/src/scene_painter.dart` (R02b).

## Contexto que você precisa (não vá procurar, está aqui)

**A regra de ouro** (§5.2): `fill`/`stroke` ausentes no JSON significam
**herdar** a cor corrente; `"none"` significa não pintar aquele canal. O
parser de R01 já traduziu isso em `ScenePaint.inherit` / `ScenePaint.none` /
`ColorPaint(hex)` — você não precisa olhar strings.

**O Verovio traça quase tudo.** A regra CSS global do SVG
(`ellipse, path, polygon, polyline, rect {stroke:currentColor}`) é resolvida
na exportação. Medido no corpus (28 781 formas `p`/`r`/`e`):

| Fato medido | Valor |
| --- | --- |
| Formas com `strokeWidth` presente | **28 781 — todas** |
| Formas com `stroke` explícito | **nenhuma** — 100% herdam a cor corrente |
| Formas com `fill: "none"` | 20 440 (as retas: hastes, linhas de pentagrama) |
| Formas com `fill` explícito (`#000000`) | 58 |
| Formas com `fill` herdado | o restante (~8 283), incluindo **todos** os `r` e `e` |
| `fillOpacity` / `strokeOpacity` presentes | **nenhuma ocorrência** |
| `lineCap` | `default` 27 285 · `round` 1 331 · `square` 165 |
| `lineJoin` | `default` 27 322 · `round` 1 331 · `miter` 128 |
| `dash` | **8 ocorrências**, todas `[36, 72]`, todas em nós de classe `octave` (5 no Chopin Étude Op.10 No.9, 3 no Clair de Lune) |
| `strokeWidth` mais comuns | 18 (8 239×), 13 (6 179×), 1 (4 292×), 22 (4 207×), 27 (2 021×), 9 (1 027×) — unidades de viewBox |

Ou seja: **`r` e `e` são preenchidos com a cor herdada _e_ traçados com
largura 1**, e a maior parte dos `p` é só traço sobre `fill: none`.

**`strokeWidth` ausente**: R01 deixou o campo como `double?` cru de
propósito, porque o default efetivo difere por tipo (§8 documenta "padrão IR
1.0" para formas; §5.3 diz `sy` para glifo). Para `p`/`r`/`e` deste passo, o
default quando ausente é **`1.0`**. Registre nas notas que no corpus atual o
campo nunca falta, então esse ramo não tem caso de teste real.

**Tracejado**: o Flutter não tem traço tracejado nativo. Implemente um
utilitário sobre `PathMetrics` (`extractPath(start, end)` alternando traço e
intervalo, por subpath, respeitando o comprimento total). Com `[36, 72]` em
unidades de viewBox e `fit.scale = 0.1`, cada traço tem 3,6 px lógicos —
erro de fase aqui aparece no diff como uma linha pontilhada deslocada.

**Dois `drawPath`, nunca um `Paint` híbrido**: preencha primeiro, trace
depois (é a ordem do SVG), com duas `Paint` separadas, ambas
`isAntiAlias: true`.

## O que fazer

1. Resolver cor de cada canal:
   - `ScenePaint.none` → não pinta;
   - `ScenePaint.inherit` → cor corrente da pilha (R02b);
   - `ColorPaint(hex)` → cor explícita;
   - alfa final = alfa da cor × `fillOpacity` (ou `strokeOpacity`).
2. `Paint` de traço: `strokeWidth` (default 1.0), `strokeCap` e `strokeJoin`
   mapeados de `SceneLineCap`/`SceneLineJoin`. `defaultCap`/`defaultJoin` do
   modelo significam "o exportador não pediu nada" → use o default do SVG:
   `StrokeCap.butt` e `StrokeJoin.miter` (é o que o `resvg` aplica quando o
   atributo não está presente). Os valores `arcs` e `miter-clip` não existem
   no Flutter: mapeie para `StrokeJoin.miter` e registre nas notas (não
   ocorrem no corpus).
3. Tracejado em `score_bridge/lib/src/dash.dart`, com teste próprio.
4. `SceneRect`/`SceneEllipse` usam o mesmo caminho de estilo dos `ScenePath` —
   não duplique a lógica de `Paint` em três lugares.

## Fora de escopo

- Glifos (R03) e texto (R04) — mesmo que a assinatura já os aceite.
- Qualquer comparação de PNG (R02d).

## Critérios de aceite

1. `flutter analyze` limpo, `flutter test` verde.
2. Teste de canal: para as 9 combinações de `fill` × `stroke`
   (`inherit`/`none`/explícito), o `RecordingCanvas` mostra o número certo de
   `drawPath` (0, 1 ou 2) e a cor certa em cada um.
3. Teste de largura: forma com `strokeWidth: 18` produz `Paint.strokeWidth ==
   18.0` **em unidades de viewBox** (a escala da página é do `Canvas`, não da
   `Paint` — se você multiplicar por `fit.scale` em algum lugar, o traço sai
   10× fino).
4. Teste de opacidade: `fillOpacity: 0.5` sobre `#ff0000` produz alfa 127/128
   (documente qual arredondamento você usou).
5. Teste de tracejado: uma reta de 1 000 unidades com `dash: [36, 72]` produz
   um `Path` cujo comprimento total medido por `computeMetrics` é
   `ceil/floor` do esperado (calcule no teste: 9 traços completos de 36 + o
   resto), e o primeiro traço começa exatamente no ponto inicial.
6. Teste com o caso real: renderize o nó de classe `octave` do Chopin Étude
   Op.10 No.9 (é o único tracejado do corpus) e confirme que o número de
   subtraços gerados é o esperado para o comprimento daquela linha.
7. Teste de `default`: forma sem `lineCap`/`lineJoin` vira `StrokeCap.butt` /
   `StrokeJoin.miter`.

## Notas de execução

(a preencher por quem executar)
