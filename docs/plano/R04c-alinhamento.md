# R04c — Alinhamento e `letterSpacing`

**Depende de:** R04b · **Decisão necessária:** não

## Objetivo

Implementar os três alinhamentos (`left`, `center`, `right`) com a mesma
semântica do `text-anchor` do SVG, incluindo a interação com `letterSpacing`
— a armadilha que o projeto anterior levou um sub-passo inteiro para fechar.

## Ler antes (só isto)

- [Especificação](../formato/especificacao-v1.md), seção **5.4** (o mapa
  `align` ↔ `text-anchor`).
- `verovio/src/svgdevicecontext.cpp` `StartText` L1019-L1040 (`anchor`) e
  `MoveTextTo` (o `text-anchor` pode mudar no meio do texto).
- `score_bridge/lib/src/scene_painter.dart` (R04b).

## Contexto que você precisa (não vá procurar, está aqui)

- Mapa normativo: `left` → `text-anchor=start`, `center` → `middle`,
  `right` → `end`. `none` e `justify` já foram normalizados para `left` pelo
  exportador — não os trate aqui.
- Distribuição medida no corpus (417 runs): `center` 195, `left` 191,
  `right` 31. Ou seja, **`center` é o caso mais comum** (dedilhados, números
  de compasso, dinâmicas centradas sobre a nota) — não é um caso de borda.
- Deslocamento:

  ```dart
  final w = painter.width;
  final dx = switch (run.align) {
    SceneTextAlign.left   => 0.0,
    SceneTextAlign.center => -w / 2,
    SceneTextAlign.right  => -w,
  };
  painter.paint(canvas, Offset(run.x + dx, run.y - baseline));
  ```

- **A armadilha do `letterSpacing`**: no SVG/`resvg`, o espaçamento é aplicado
  **depois de cada glifo, inclusive o último**, então a largura usada pelo
  `text-anchor` inclui um espaço final. O Flutter faz o mesmo em
  `TextPainter.width`, mas isso **precisa ser confirmado por teste** — se
  divergir, compense subtraindo `letterSpacing` da largura antes de aplicar
  `center`/`right` (e só nesses dois: em `left` o erro não aparece, que é
  justamente por que ele passa despercebido).
- No corpus, `letterSpacing` é **sempre 0,0**: este passo é a única prova que
  o caminho vai receber. Construa os casos sintéticos com cuidado — eles são
  o teste de regressão de um comportamento que ninguém mais vai exercitar.
- `painter.width` depende de `layout()` ter sido chamado; um `width`
  consultado antes do layout é 0 e alinha tudo à esquerda silenciosamente.

## O que fazer

1. Implementar os três alinhamentos no ponto único de R04b.
2. Escrever o teste de `letterSpacing` **antes** de decidir se precisa de
   compensação; registre o resultado nas notas de execução, porque ele
   documenta o comportamento de uma versão específica do Flutter.
3. Se a compensação for necessária, isole-a numa função nomeada
   (`double anchorWidth(TextPainter p, SceneText run)`) com o comentário
   explicando de onde veio — sem isso, o próximo leitor a "simplifica".

## Fora de escopo

- Estilos bold/italic (R04d).
- Quebra de linha: o formato não tem runs multilinha (cada `t` é uma linha
  única; o Verovio já quebrou o texto).

## Critérios de aceite

1. `flutter analyze` limpo, `flutter test` verde.
2. Teste dos 3 alinhamentos, sem `letterSpacing`: para uma string de largura
   conhecida, o x pintado é `x`, `x - w/2` e `x - w` (tolerância `1e-6`).
3. Teste dos 3 alinhamentos **com** `letterSpacing: 40`: o resultado é
   comparado contra a largura esperada calculada à mão
   (`soma dos avanços + n * letterSpacing`), e a conclusão — "o Flutter
   inclui o espaçamento final" ou "não inclui, compensei" — fica registrada
   nas notas.
4. Teste com run real do corpus: um dedilhado (`size: 303`, `align: center`)
   da Chopin Étude p.1 cai com o centro sobre a posição `x` do formato
   (tolerância 0,5 unidade de viewBox).
5. Conferência visual: os números de dedilhado aparecem centrados sobre as
   notas, como no SVG. Anexe um recorte lado a lado nas notas.

## Notas de execução

Executado em 2026-09-19. Deslocamento `dx` no `_drawText` (`0`, `-w/2`,
`-w` sobre `painter.width`, com `layout()` já feito no `painterForRun`).
**Sem compensação e sem `anchorWidth`**: a sonda (Flutter 3.47.4) mediu
`width` = soma dos avanços + n×`letterSpacing` exatos ('ab'+40: 462,258;
'Lent'+40: 902,170; '5'+40: 242,5) — o Flutter INCLUI o espaçamento final,
como o `resvg`; o teste com `letterSpacing: 40` trava esse comportamento
(quebra se o motor mudar). `flutter analyze` limpo, `dart format` limpo,
`flutter test` 63/63 (3 novos em `test/text_run_test.dart`: 3 aligns sem
ls a `1e-6`, 3 aligns com ls 40 contra largura à mão, dedilhado real).

Visual (Chopin Étude p1, `compare/out/r04b/`, Impeller): diff tol 32 (tolerância da época) =
**0,4978%** (31 046 px). Recorte `etude-p1-fingering-side.png` (SVG ×
cena, 2×): o '5' `303/center/bold` cai centrado sobre a haste nos dois;
centroides da região a 0,03 px em x e 0,12 px em y (1322 vs 1324 px de
tinta — 1 px de AA). Critério 4 (centro sobre `x` a 0,5 viewBox) medido
no mesmo run.
