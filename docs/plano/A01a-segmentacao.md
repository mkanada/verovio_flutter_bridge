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

(a preencher por quem executar)
