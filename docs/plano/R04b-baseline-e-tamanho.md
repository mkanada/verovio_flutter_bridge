# R04b — Desenho do run: linha de base, tamanho e cor

**Depende de:** R04a · **Decisão necessária:** não

## Objetivo

Desenhar um run de texto na posição certa. O formato dá a **linha de base**
(como o SVG); o `TextPainter` do Flutter pinta a partir do **topo**. Errar
essa conversão desloca todo o texto da página por alguns pixels — foi a
principal fonte de divergência do projeto anterior.

## Ler antes (só isto)

- [Especificação](../formato/especificacao-v1.md), seção **5.4**.
- `verovio/src/svgdevicecontext.cpp` `StartText` L1019-L1065 e `MoveTextTo`
  L1067+ (como o SVG posiciona: `x`/`y` são a âncora da linha de base).
- `score_bridge/lib/src/text_font.dart` (R04a).

## Contexto que você precisa (não vá procurar, está aqui)

- `SceneText` (R01) traz: `text`, `x`, `y`, `size`, `align`, `letterSpacing`,
  `bold`, `italic`, `family`, `color`. Tudo já **resolvido** pelo exportador —
  as regras CSS por classe (`g.tempo{bold}`, `g.dir,g.dynam,g.mNum{italic}`,
  `g.label{normal}`) foram aplicadas na exportação. O Flutter não interpreta
  CSS.
- `size` já está em **unidades de viewBox** (o mesmo espaço do resto da
  cena). Tamanhos reais no corpus: 405 (229 runs), 324 (175), 303 (8) e
  607 (5). Com `fit.scale = 0.1`, um `size: 405` é 40,5 px lógicos.
- `letterSpacing` é **0,0 em 100% dos runs do corpus** — o caminho existe no
  formato, mas só será exercitado por teste sintético (R04c).
- `color` explícito em run: **nenhuma ocorrência** no corpus; o texto herda a
  cor corrente, como qualquer forma.
- Conversão de linha de base:

  ```dart
  final painter = TextPainter(
    text: TextSpan(text: run.text, style: TextStyle(
      fontFamily: kScoreTextFamily,
      package: kScoreTextFamilyPackage,
      fontSize: run.size,
      letterSpacing: run.letterSpacing,
      fontWeight: run.bold ? FontWeight.w700 : FontWeight.w400,
      fontStyle: run.italic ? FontStyle.italic : FontStyle.normal,
      color: corCorrente,
      height: 1.0,                     // sem line-height extra
    )),
    textDirection: TextDirection.ltr,
    textScaler: TextScaler.noScaling,  // independente da acessibilidade do aparelho
  )..layout();

  final dy = painter.computeDistanceToActualBaseline(TextBaseline.alphabetic);
  painter.paint(canvas, Offset(xAlinhado, run.y - dy));
  ```

- **`textScaler: TextScaler.noScaling` não é opcional**: sem isso, o mesmo
  `.vsb` renderiza diferente em dois aparelhos com configurações de fonte
  distintas, e o teste que passa na sua máquina falha na do usuário.
- **`height: 1.0`** evita que o Flutter aplique o line-height da fonte; o SVG
  não aplica nada.
- Um `TextPainter` por run é aceitável neste passo (são 12 a 89 runs por
  peça). Se virar gargalo, o cache entra em A01, não aqui.

## O que fazer

1. Ligar o ramo `SceneText` do percurso de R02b: resolver cor (explícita ou
   herdada), montar o `TextPainter`, converter a linha de base e pintar.
2. Alinhamento: neste passo implemente **só** `left` (âncora = `x`); `center`
   e `right` são de R04c. Deixe um `TODO` explícito, não uma conta errada.
3. Extraia a construção do `TextPainter` para uma função testável
   (`TextPainter painterForRun(SceneText run, Color color)`), porque R04c e
   R04d vão testá-la direto, sem `Canvas`.

## Fora de escopo

- Alinhamento `center`/`right` e `letterSpacing` (R04c).
- Bold/italic combinados e paridade por peça (R04d).
- Runs inteiramente SMuFL: o exportador já os transformou em `u` (decisão
  D01-6 do projeto anterior). Se aparecer um, é bug de S03/S05 — registre e
  volte.

## Critérios de aceite

1. `flutter analyze` limpo, `flutter test` verde.
2. Teste de linha de base: para um run com `y = 1000` e `size = 405`, o topo
   da caixa pintada fica em `1000 - ascent`, com `ascent` calculado a partir
   das métricas da TTF carregada (tolerância **0,5 unidade de viewBox**).
3. Teste de escala: dobrar `size` dobra a largura medida (tolerância 1%) —
   guarda contra aplicar `fit.scale` ao `fontSize` por engano.
4. Teste de independência de ambiente: o mesmo run medido com
   `TextScaler.linear(2.0)` no ambiente de teste produz **a mesma** largura
   (prova de que `noScaling` está ativo).
5. Teste de cor: run dentro de um nó `color: "#ff0000"` sai vermelho; run com
   `color` próprio ignora a herança.
6. Render visual de uma peça com pouco texto (Gymnopédie): o título e a
   indicação de andamento aparecem no lugar certo, sem deslocamento vertical
   perceptível contra o SVG. Anexe o recorte nas notas.

## Notas de execução

(a preencher por quem executar)
