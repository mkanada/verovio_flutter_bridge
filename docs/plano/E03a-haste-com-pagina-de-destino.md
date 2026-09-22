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

Salto **na mesma página** (Gymnopédie 39 → 1; Maple Leaf Rag 83 → 69): em
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

_(preencher ao executar)_
