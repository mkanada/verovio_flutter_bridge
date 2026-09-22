# E03a — Haste com página de destino (mecanismo)

**Depende de:** E02b · **Decisão necessária:** **sim — D-SALTO** (pare e
pergunte antes de escrever código; bloqueia também E03b)

## Objetivo

Hoje a página de trás da haste é sempre a seguinte (`A + 1`). Num salto de
repetição, a página seguinte na música pode ser uma **anterior** (ou a mesma,
ou uma mais à frente, num "To Coda"). Este passo entrega só o **mecanismo
visual**: a haste pode revelar uma página qualquer. **Quando** ela anda nos
saltos é do E03b, como A03b/A05b fizeram para as viradas normais.

## Decisão necessária — D-SALTO

**O que a vista faz quando a execução salta para outra página?**

- **(a) Haste generalizada (recomendado).** A mesma haste das viradas normais
  (entrada, estacionada, conclusão; decisão de 2026-09-21 em A03b), só que
  com a **página de destino do salto** atrás, em vez de `A + 1`. Mantém uma
  só linguagem visual: o leitor vê o destino à esquerda da haste antes de a
  música chegar lá. Limitação medida: a haste estaciona no início do último
  compasso antes do salto, e o compasso de destino pode estar mais à direita
  do que ela. Na Maple Leaf Rag, no salto 34 → 19, o destino (x = 5 174)
  aparece antes do salto, porque a haste estaciona em x = 12 910. No salto
  67 → 52, o destino (x = 10 846) só aparece na conclusão, porque a haste
  estaciona em x = 1 160 (unidades de viewBox, página de 21 000 de largura).
- **(b) Corte seco no instante do salto.** É o comportamento que E02b deixa.
  E03a/E03b se reduzem a documentar e gerar evidências.
- **(c) Deslizar para a página de destino no instante do salto**, como a
  trilha do `pagedSlide`, sem haste.

Salto **na mesma página** (Gymnopédie 39 → 1; Maple Leaf Rag 84 → 69): em
todas as opções, nada acontece na vista, porque a página já está à mostra.
Um aviso visual do salto é do host, fora deste passo.

O resto deste arquivo supõe a opção (a). Com (b) ou (c), reescreva o "O que
fazer" antes de executar.

## Ler antes (só isto)

- `score_bridge/lib/src/score_view.dart`: `SweepCurtain` (L61),
  `_activeCurtain` (L498), `_onCurtainChanged` (L515), `_buildSweep` (L782)
  e o cache de páginas de A03c.
- A03b, seções "Comportamento decidido com o usuário" e "Notas de execução".

## Contexto que você precisa (não vá procurar, está aqui)

- `_buildSweep` pinta `_centered(a + 1, box)` atrás de A. A conclusão chama
  `_setCurrent(c.pageIndex + 1)`. `_activeCurtain` recusa a última página
  (`c.pageIndex >= _pageCount - 1`), mas a Maple Leaf Rag salta **da última
  página** (2) para a 1, em 97 500 ms.
- A haste é dirigida só por `edgeX` (borda direita, em unidades de viewBox da
  página A). A regra de quando ela anda fica fora do widget.
- O cache de `Picture` de A03c mantém vivas a página corrente e as vizinhas.
  O destino de um salto pode não ser vizinho (D.C. numa peça longa), e as
  duas páginas precisam estar pintadas durante a haste.

## O que fazer

1. `SweepCurtain({required pageIndex, required edgeX, int? targetPageIndex})`:
   a página de trás é `targetPageIndex ?? pageIndex + 1`. Inclua o campo em
   `==`, `hashCode` e `toString`.
2. `_activeCurtain` aceita qualquer destino válido, diferente de A e dentro
   de `[0, pageCount)`. A última página só tem haste se houver destino
   explícito.
3. `_buildSweep` pinta o destino atrás, e a conclusão torna o destino a
   página corrente.
4. O cache de páginas mantém o destino vivo enquanto a haste está ativa.
5. `goToPage` animado (a haste "manual" de A03b) não muda.

## Fora de escopo

- A regra de tempo nos saltos e as evidências (E03b).
- `pagedSlide` e `continuousScroll` (o salto ali é o de E02b).

## Critérios de aceite

1. Teste de widget com `SweepCurtain(pageIndex: 1, edgeX: x,
   targetPageIndex: 0)`: um pixel à esquerda da haste vem da página 0 e um à
   direita vem da página 1 (sonda de cor com notas coloridas por página,
   como em A03b).
2. Haste na última página com destino anterior (2 → 1) é aceita. Sem
   destino, continua recusada.
3. Conclusão (`edgeX ≥ fim`) torna o destino a página corrente.
4. Sem `targetPageIndex`, os goldens e testes de A03b ficam **byte-idênticos**.
5. Salto para uma página não vizinha (sintético: página 5 → 0 numa peça de 7
   páginas) pinta as duas, e o contador de `Picture` de A03c volta ao patamar
   depois, sem vazamento.
6. `flutter analyze` limpo, `flutter test` verde.

## Notas de execução

**D-SALTO resolvida pelo usuário: (a) haste generalizada.**

**Código.** `SweepCurtain` ganha `targetPageIndex` (nullable, em `==`/
`hashCode`/`toString`). `ScoreViewState` ganha `_targetOf(c)` (
`c.targetPageIndex ?? c.pageIndex + 1`) e `_isValidCurtain(c)` (destino
dentro de `[0, pageCount)` e diferente da própria página — substitui o
antigo `c.pageIndex < _pageCount - 1`, que agora só bloquearia a última
página **sem** destino explícito). `_onCurtainChanged` usa `_targetOf(c)`
em vez de `c.pageIndex + 1` na conclusão. `_buildSweep` pinta
`_centered(_targetOf(curtain), box)` como fundo, em vez de
`_centered(a + 1, box)`.

**Cache de páginas (tarefa 4) não precisou de nenhuma linha nova.** Cada
página já é montada sob uma `GlobalKey` estável por índice (`_keyOf`,
A03c) — enquanto `_buildSweep` referenciar aquele índice em qualquer lugar
da árvore, o `ScorePageView`/`PageLayers` daquela página continua vivo;
quando deixa de ser referenciado (a haste termina e a página antiga não é
mais nem a corrente nem o destino de nada), o Flutter desmonta a
subárvore e o `dispose()` de sempre roda. Trocar `a + 1` por
`_targetOf(curtain)` foi suficiente para o destino (por mais distante que
esteja de A) entrar e sair do cache exatamente como A05b já fazia com
`A + 1`.

**`goToPage` animado (a haste manual de A03b) não mudou**: continua
sempre `SweepCurtain(pageIndex: _sweepPage, edgeX: …)`, sem
`targetPageIndex`, então cai no `?? pageIndex + 1` de sempre.

**Critérios de aceite** (`test/score_view_test.dart`, grupo "página de
destino (E03a)", 4 testes novos):

1. `SweepCurtain(pageIndex: 1, edgeX: midX(1), targetPageIndex: 0)`:
   verificado **estruturalmente**, não por sonda de pixel — o
   `ScorePageView` sob o `ClipRect` (a metade direita) tem `pageIndex ==
   1`, e o que não está sob nenhum `ClipRect` (o fundo, a metade
   esquerda) tem `pageIndex == 0`. Trocado o pixel-probing sugerido no
   passo por uma checagem direta dos parâmetros do widget: mais precisa
   (não depende de onde uma nota colorida cai) e não depende de nenhum
   fixture novo.
2. Página 6 (a última de 7, índice 0-based) sem `targetPageIndex`:
   recusada (`ClipRect` ausente, porque o destino implícito, 7, não
   existe). Com `targetPageIndex: 1`: aceita.
3. Conclusão (`edgeX >= sweepEndX(...)`) com `targetPageIndex: 1` a
   partir da página 6: `currentPage` e `onPageChanged` vão para 1, não
   para 7.
4. Nenhum teste de A03b mudou: os 239 testes da suíte (todos os arquivos)
   continuam batendo depois da mudança, incluindo os goldens/pixel-a-pixel
   de A03a e os 5 testes de haste normal de A03b — `SweepCurtain` sem
   `targetPageIndex` é byte-idêntico a antes (`==`/`hashCode` incluem o
   campo novo, mas comparam `null == null`).
5. Salto sintético 5 → 0 numa peça de 7 páginas (Nocturne): com a haste
   ativa, as duas páginas (5 e 0) aparecem como `ScorePageView` na
   árvore; na conclusão, só a 0 permanece e `PictureStats.live` volta a 0
   depois de desmontar a `ScoreView` — sem vazamento.

`flutter analyze` limpo, `flutter test` 239/239 (era 235; 4 testes
novos).
