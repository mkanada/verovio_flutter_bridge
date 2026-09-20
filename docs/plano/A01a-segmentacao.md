# A01a — Segmentação da página por ordem de documento

**Depende de:** R06c · **Decisão necessária:** não

## Objetivo

Dividir a árvore de uma página em segmentos alternados — estático, dinâmico,
estático, … — **preservando exatamente a ordem de pintura**. É o algoritmo
que torna a cor por nota barata sem mudar um pixel. Neste passo ele é só
lógica, testável sem `Canvas`.

## Ler antes (só isto)

- [Especificação](../formato/especificacao-v1.md), seção **6** (ordem de
  pintura).
- `score_bridge/lib/src/scene_painter.dart` (o percurso de R02b).
- Risco 3 do [README do plano](README.md).

## Contexto que você precisa (não vá procurar, está aqui)

**Por que a ordem importa**: a partitura é desenhada preto sobre branco, então
sobreposições entre elementos da mesma cor são invisíveis. Quando uma nota
fica **vermelha**, toda sobreposição vira visível: um feixe desenhado depois
da haste tem que continuar depois. Por isso a segmentação é por ordem de
documento, e não "notas numa camada, resto na outra".

**Números medidos no corpus** (34 páginas, ids dinâmicos = os que aparecem no
`timemap`):

| Medida | Mediana | Máximo | Mínimo |
| --- | ---: | ---: | ---: |
| Nós dinâmicos por página | 308 | 719 | 44 |
| **Segmentos alternados por página** | **196** | **545** | **29** |
| Formas desenhadas por página | 1 345 | 2 463 | — |

Repare que segmentos (196) < 2 × dinâmicos + 1 (618): notas consecutivas na
ordem de documento **se fundem num único segmento dinâmico**. Isso não é
detalhe de otimização — é o que mantém o número de `ui.Picture` estáticos por
página na casa da centena e não do milhar.

**Quem é dinâmico**: um nó cujo `id` está no conjunto `animatableIds` passado
ao widget. O padrão é o conjunto de ids que aparecem no `timemap` do próprio
documento. Fatos do corpus:

- Todos os ids do timemap que existem na cena são de classe `note` (10 068
  no corpus).
- **Nem todo id do timemap existe na cena**: Gymnopédie tem 180 ids a mais
  (todos com sufixo `-rend2`) e Maple Leaf Rag tem 883. São notas de
  repetição/expansão. O código **não pode** assumir que todo id do timemap
  está na página — ignorar o que não existe, sem erro.
- Um nó dinâmico pode conter subárvore (a nota contém cabeça, haste, pontos):
  ao encontrar um nó dinâmico, ele inteiro vira um segmento; não desça
  procurando outro dentro.

## O que fazer

1. `score_bridge/lib/src/segmentation.dart`:

   ```dart
   sealed class PageSegment {}
   // items/nodes sempre em ordem de documento; nodes são os ids animáveis
   class StaticSegment extends PageSegment { final List<SceneChild> items; }
   class DynamicSegment extends PageSegment { final List<SceneNode> nodes; }

   List<PageSegment> segmentPage(ScenePage page, Set<String> animatableIds);
   ```

   Cada item precisa carregar também o **estado herdado** no ponto em que
   aparece (cor corrente e transformação acumulada), senão o segmento não
   pode ser pintado isoladamente. Guarde isso no próprio item do segmento
   (ex.: `StaticItem(child, inheritedColor, transform)`), resolvido na
   segmentação — não recalculado na pintura.

2. O percurso é o **mesmo** de R02b. Se você acabar com dois percursos
   diferentes, eles vão divergir; extraia um percurso único parametrizado por
   um visitante.

3. Exponha `segmentCount` e a contagem por tipo, para a instrumentação de
   A01c e para os critérios abaixo.

## Fora de escopo

- `ui.Picture`, widget, repaint (A01b).
- Controller e cor (A01c), animação (A02).

## Critérios de aceite

1. `flutter analyze` limpo, `flutter test` verde.
2. Teste de ordem: numa árvore sintética com 10 elementos e 3 dinâmicos,
   concatenar os itens de todos os segmentos na ordem em que aparecem
   reproduz **exatamente** a ordem do percurso original (compare listas).
3. Teste de fusão: dois nós dinâmicos adjacentes viram **um** segmento
   dinâmico com 2 nós, não dois segmentos.
4. Teste de estado herdado: um elemento estático dentro de um nó com
   `color: "#ff0000"` carrega essa cor no item do segmento; um dentro de um
   nó `rotate` carrega a transformação.
5. Teste de robustez: `animatableIds` com ids que não existem na página
   (simule os `-rend2` da Gymnopédie) não lança e não cria segmentos vazios.
6. Teste no corpus: para as 34 páginas, registre nas notas a contagem de
   segmentos por página (mediana e máximo) e compare com os números desta
   página do plano (196 / 545). Uma diferença grande significa que a
   definição de "dinâmico" ficou diferente — explique nas notas.
7. `animatableIds` vazio produz exatamente **1** segmento estático por
   página.

## Notas de execução

Executado em 2026-09-20 (Flutter 3.47.4 / Dart 3.13.3). `flutter analyze`
limpo; `flutter test` 85/85 (66 anteriores + 19 novos em
`test/segmentation_test.dart`).

**O que foi feito**

- `lib/src/scene_walk.dart` (novo): `walkScene(root, initialColor, visitor,
  {colorOverrides})` e a interface `SceneVisitor` (`enterGroup` /
  `visitLeaf` / `exitGroup`). É o **percurso único** que o item 2 do passo
  pede: ordem de documento, `hidden` (poda a subárvore) e cor herdada
  (`color` do nó, com o override por `id` vencendo) vivem só ali.
  `parseCssColor` saiu do `scene_painter.dart` para lá (público no arquivo,
  fora do barril `score_bridge.dart`, que exporta só `SceneVisitor` e
  `walkScene`).
- `ScenePainter` virou um visitante desse percurso (`_CanvasVisitor`:
  `rotate` = `save/translate/rotate/translate` na entrada e `restore` na
  saída). A sequência de operações no `Canvas` é a mesma de antes — os testes
  de R02b/R02c/R03b/R04 e o widget-vs-harness (R05c, 0 px) passam sem
  alteração, e a varredura do corpus refeita depois da refatoração deu os
  102 PNGs byte-idênticos (ver abaixo).
- `lib/src/segmentation.dart` (novo): `segmentPage(page, animatableIds)` →
  `List<PageSegment>` (`StaticSegment` / `DynamicSegment`), mais
  `Transform2D` (afim 2D imutável: `rotation`, `compose`, `apply`,
  `toMatrix4` para `Canvas.transform`), `animatableIdsFromTimemap` e a
  extensão `PageSegmentStats` (`segmentCount`, `staticSegmentCount`,
  `dynamicSegmentCount`, `staticItemCount`, `dynamicNodeCount`).

**Desvios do esboço do passo**

- O esboço tinha `DynamicSegment.nodes: List<SceneNode>`; um nó dinâmico
  também precisa do estado herdado para ser pintado sozinho (a cor do pai e o
  `rotate` dos ancestrais), então o segmento guarda `List<DynamicItem>`
  (`node`, `inheritedColor`, `transform`) e `nodes` é um getter derivado. O
  estado herdado de um `DynamicItem` é o de **antes** do nó: o `color` e o
  `rotate` do próprio nó valem dentro dele, na pintura (A01b).
- `StaticItem.child` nunca é um `SceneNode`: os grupos estáticos são
  **achatados nas folhas** (forma, uso de glifo ou run de texto), cada uma
  com a cor herdada já resolvida. Grupos `hidden` somem da segmentação, como
  do pintor; um nó dinâmico `hidden` também não vira segmento.
- `transform` é `Transform2D?`, com `null` = identidade — é o caso da quase
  totalidade dos itens (no corpus há 8 nós `rotate`, em 4 das 34 páginas, no
  máximo 4 por página; a página com mais folhas sob `rotate` é Clair de Lune
  p2, com 116), e assim não aloca uma matriz por folha. É a composição só dos
  `rotate` dos ancestrais, **no espaço de conteúdo**: o `translate(fit)` /
  `scale` / `translate(origin)` da página é da camada (A01b), não do item.
- `animatableIdsFromTimemap` considera só `on`/`off`, não `restsOn`/
  `restsOff`. Com essa definição os números do corpus batem com o plano (ver
  critério 6); pausas não acendem.
- Dois nós dinâmicos se fundem mesmo com grupos vazios ou `hidden` entre eles
  na árvore (nada é pintado entre os dois, então a ordem de pintura é a
  mesma) — só uma **folha estática visível** os separa.

**Critérios**

1. `flutter analyze` sem avisos; `flutter test` 85/85.
2. Ordem: árvore sintética com 10 elementos e 3 dinâmicos; a concatenação
   dos itens de todos os segmentos é igual (`orderedEquals`, por identidade)
   a um percurso de referência escrito à mão no próprio teste.
3. Fusão: dois dinâmicos adjacentes → 1 `DynamicSegment` com 2 nós; também
   testado em grupos irmãos separados por grupo vazio/`hidden`, e o caso
   contrário (uma folha entre dois dinâmicos os separa).
4. Estado herdado: cor de grupo (`#ff0000`) chega às folhas e não vaza para o
   irmão; `rotate` produz `transform`. A matriz acumulada de **dois `rotate`
   aninhados** (ângulos e pivôs diferentes) foi conferida ponto a ponto contra
   o `RecordingCanvas` (oráculo que compõe `save/translate/rotate` como o
   `Canvas`), tanto por `apply` quanto por `toMatrix4` → `Canvas.transform`.
5. Robustez: ids inexistentes (`…-rend2`) não lançam nem criam segmento
   vazio; o resultado é idêntico ao sem eles. No fixture da Gymnopédie, os
   469 ids do timemap valem para a peça inteira e cada página só tem parte
   deles — exatamente esse caso.
6. Corpus (34 páginas, ids = `on` ∪ `off` do timemap do próprio `.vsb`):

   | Medida | Mediana | Máximo | Mínimo | Plano |
   | --- | ---: | ---: | ---: | --- |
   | Nós dinâmicos por página | 307,5 | 719 | 44 | 308 / 719 / 44 |
   | **Segmentos por página** | **196** | **545** | **29** | 196 / 545 / 29 |
   | Formas desenhadas por página | 1 345,5 | 2 463 | 229 | 1 345 / 2 463 / — |
   | ↳ segmentos estáticos | 98,5 | 273 | 15 | — |
   | ↳ segmentos dinâmicos | 97,5 | 272 | 14 | — |

   Bate com o plano: a definição de "dinâmico" é a mesma. Totais: 9 952 nós
   dinâmicos e 6 764 segmentos nas 34 páginas; os nós dinâmicos são de classe
   `note` em **34/34** páginas (nenhuma outra classe). Os ids que sobram: a
   Gymnopédie tem 469 ids no timemap e 245 + 44 nas páginas (180 a mais, os
   `-rend2`); a Maple Leaf Rag, 2 464 contra 518 + 719 + 344 (883 a mais) —
   os mesmos números do plano. Medido com uma medição descartável sobre os
   `.vsb` de `compare/corpus/` (não fica no repositório: esses arquivos são
   git-ignorados e regeneráveis).
7. `animatableIds` vazio: 1 segmento estático por página nas 2 páginas do
   fixture, com tantos itens quanto folhas visíveis (contadas por um percurso
   independente no teste) e `transform == null` em todos.

**Refatoração sem efeito visual (conferido):** depois de trocar o percurso do
pintor, `compare-corpus.sh 128` (backend Skia) refeito nas 34 páginas: os
**102 PNGs** (`-svg`, `-scene`, `-diff`) ficaram **byte-idênticos** aos
commitados (o git não vê mudança em nenhum) e as 34 porcentagens são as
mesmas. A única coluna que mudou no CSV foi `bytes_vsb` (até 169 bytes), que é
ruído de execução — o Verovio regenera `xml:id` aleatórios a cada rodada e o
tamanho do JSON acompanha; o CSV foi restaurado ao commitado.

**Afeta os passos seguintes**

- A01b pinta um `StaticSegment` percorrendo `items`: para cada um,
  `save`, `transform(item.transform.toMatrix4())` se não for `null`, pintar a
  folha com `item.inheritedColor`, `restore` — sem recalcular estado. Hoje as
  rotinas de desenho de folha (`_drawShape`, `_drawGlyphUse`, `_drawText`)
  são privadas do `ScenePainter`; A01b precisará expô-las (por exemplo um
  `paintLeaf(canvas, leaf, color)` público) em vez de duplicá-las.
- Para pintar um `DynamicItem`, A01b precisa de um "pintar este subnó com
  estas cor e transformação herdadas": é `walkScene(item.node,
  item.inheritedColor, …)` com o mesmo `_CanvasVisitor` e `colorOverrides`,
  depois de aplicar `item.transform`.
- `segmentPage` recalcula tudo a cada chamada e só depende de `(page,
  animatableIds)`: A01b deve chamá-la **uma vez por página** e guardar o
  resultado, não a cada frame.
