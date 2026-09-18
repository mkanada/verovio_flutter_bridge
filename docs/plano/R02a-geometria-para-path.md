# R02a — Geometria: `v`/`i`/`o` → `ui.Path`

**Depende de:** R01 · **Decisão necessária:** não

## Objetivo

Converter a geometria do formato em `ui.Path`, **sem tocar em `Canvas`**:
subpaths de Bézier (`p` e glifos), retângulo (`r`) e elipse (`e`). É a função
mais usada do renderizador inteiro e a mais fácil de testar isoladamente —
por isso vem sozinha, antes de qualquer pintura.

## Ler antes (só isto)

- [Especificação](../formato/especificacao-v1.md), seção **4.1** (conversão
  normativa) e seção **5.2** (formas).
- `score_bridge/lib/src/model.dart`: classes `BezierPath`, `ScenePath`,
  `SceneRect`, `SceneEllipse` (já existem, vindas de R01).

## Contexto que você precisa (não vá procurar, está aqui)

A conversão normativa (§4.1), com `n = v.length / 2` vértices:

```text
moveTo(v[0])
para k de 0 até n-2:
    cubicTo(v[k] + o[k], v[k+1] + i[k+1], v[k+1])
se closed:
    cubicTo(v[n-1] + o[n-1], v[0] + i[0], v[0]); close()
```

`v`, `i` e `o` são `Float64List` **planos** de pares `(x, y)`: o vértice `k`
está em `v[2k]`, `v[2k+1]`. `i`/`o` são tangentes **relativas ao vértice**
(somam-se a ele). Os três arrays têm sempre o mesmo comprimento (R01 já
valida isso no parser e lança `VsbFormatException` caso contrário).

Medido no corpus real de 10 peças (34 páginas, `compare/out/s07/*.vsb`) —
serve para você saber o que é caso comum e o que é caso raro:

| Fato | Valor |
| --- | --- |
| Formas `p` | 26 469 · `r` 1 401 · `e` 911 |
| Subpaths por forma `p` | 1 em 26 237 dos casos; máximo observado 11 |
| Vértices por subpath | **2 em 20 356 subpaths** (reta: haste, linha de pentagrama, barra), 4 em 4 408, 3 em 1 444; cauda até ~26 |
| Subpath fechado (`closed: true`) | 6 667 de 27 107 |
| Subpath com menos de 2 vértices | **nenhum** |
| `r` com `rx` > 0 (canto arredondado) | **nenhum** no corpus — implemente mesmo assim |
| `e` com `rx`/`ry` > 0 | todas as 911 |
| Glifos (dicionário) | 1 a 4 subpaths por glifo; 4 a 17 vértices por subpath |

O caso dominante é, portanto, **um subpath aberto de 2 vértices com tangentes
zero** — uma reta. A conversão acima já produz a reta correta (`cubicTo` com
pontos de controle iguais aos extremos), mas vale um teste dedicado porque é
90% da tinta da página.

## O que fazer

1. Criar `score_bridge/lib/src/geometry.dart` com funções puras:

   ```dart
   ui.Path pathFromBeziers(List<BezierPath> subpaths);   // p e glifos
   ui.Path pathForRect(SceneRect r);                     // usa RRect quando rx > 0
   ui.Path pathForEllipse(SceneEllipse e);               // addOval(fromCenter)
   ```

   `pathFromBeziers` percorre os `Float64List` **sem** criar `Offset`
   intermediários (é o laço mais quente do render; alocar 2 objetos por
   vértice multiplica por ~27 000 por página).

2. Cache por objeto, lazy: acrescente ao `ScenePath`/`SceneRect`/
   `SceneEllipse`/`GlyphDef` um campo privado `ui.Path? _cached` e um getter
   `ui.Path get path`. A camada dinâmica de A01 repinta a mesma forma dezenas
   de vezes por segundo; converter de novo a cada frame é desperdício puro.
   Como o modelo de R01 é imutável e `const` em vários pontos, o cache
   **não** pode ficar num campo `final` — use uma classe auxiliar
   (`PathCache`, `Expando`, ou remova o `const` desses três construtores,
   registrando a escolha nas notas).

3. `rx` de `SceneRect` maior que zero → `RRect.fromRectXY(rect, rx, rx)`
   (o formato só carrega um raio; §8 diz `BridgeShape.radius` → `r.rx`).

## Fora de escopo

- `Canvas`, `Paint`, cor, traço (R02c).
- Percurso da árvore e transformação de página (R02b).
- Escala de glifo (R03b) — aqui o glifo só vira `Path` em **unidades de
  fonte**, sem transformação alguma.

## Critérios de aceite

1. `cd score_bridge && flutter analyze` sem avisos e
   `dart format --set-exit-if-changed .` limpo.
2. Teste de reta: subpath aberto `v = [0,0, 100,0]`, `i`/`o` zerados →
   `path.computeMetrics().first.length == 100.0` (tolerância `1e-9`) e
   `getBounds() == Rect.fromLTRB(0, 0, 100, 0)`.
3. Teste de Bézier conhecido: um subpath de 2 vértices com `o[0]`/`i[1]` não
   nulos, comparado contra 10 pontos calculados à mão pela fórmula cúbica
   (tolerância `1e-6`), usando `PathMetric.getTangentForOffset`.
4. Teste de fechamento: o mesmo subpath com `closed: true` tem comprimento
   **maior** que a versão aberta e `path.contains()` verdadeiro para um ponto
   interno.
5. Teste de forma real do corpus: pegue a primeira `ScenePath` do fixture
   `score_bridge/test/fixtures/erik-satie.vsb`, converta e confira
   `getBounds()` contra a `bbox` do nó pai (tolerância: metade do
   `strokeWidth`, porque a bbox do exportador inclui o traço).
6. Teste de rect e elipse: `getBounds()` bate exatamente com `x,y,w,h` e com
   `cx±rx, cy±ry`; um `rx > 0` sintético produz cantos arredondados
   (`path.contains` falso no canto exato, verdadeiro no centro da aresta).
7. Teste de cache: chamar o getter `path` duas vezes devolve a **mesma
   instância** (`identical`).

## Notas de execução

(a preencher por quem executar)
