# R04 — Texto comum: TTF, alinhamento, bold/italic

**Depende de:** R02 · **Decisão necessária:** não

## Objetivo

Desenhar títulos, indicações de andamento, dedilhados, números de compasso e
letra com a **mesma** fonte que o `resvg` usa para renderizar o SVG de
referência (Liberation Serif, nos 4 estilos). Este foi historicamente o passo
mais difícil: no projeto anterior, quatro sub-passos sobre texto foram o que
levou o corpus de 0,36% para 0,13% de divergência.

## Ler antes (só isto)

- Especificação, seção 5.4.
- `verovio/src/svgdevicecontext.cpp` `StartText` L1019-L1065 (`text-anchor`,
  `font-family`, `font-style`, `font-weight`) e `MoveTextTo` L1067+.
- `../verovio_lottie/docs/plano/D01-texto-comum.md`, seções "Notas de execução"
  e "Pendências" — a lista de armadilhas já pagas (alinhamento, `letterSpacing`,
  bold+italic, run inteiramente SMuFL).
- `../verovio_lottie/compare/scripts/compare-page.sh` — a lista exata de fontes
  passada ao `svg_render` (é a mesma que o Flutter precisa carregar).

## O que fazer

1. Carregar as 4 TTFs como assets do pacote `score_bridge`
   (`fonts/LiberationSerif-{Regular,Italic,Bold,BoldItalic}.ttf`, copiadas de
   `verovio/data/text/`), declaradas no `pubspec.yaml` com família
   `"Liberation Serif"` e os `fontWeight`/`fontStyle` corretos. Em contexto de
   teste/headless, carregue com `FontLoader` explicitamente.

2. Desenhar um run:

   ```dart
   final painter = TextPainter(
     text: TextSpan(text: run.s, style: TextStyle(
       fontFamily: 'Liberation Serif',
       package: 'score_bridge',
       fontSize: run.size,                    // já em unidades de viewBox
       letterSpacing: run.letterSpacing,
       fontWeight: run.bold ? FontWeight.w700 : FontWeight.w400,
       fontStyle: run.italic ? FontStyle.italic : FontStyle.normal,
       color: currentColor,
       height: 1.0,
     )),
     textDirection: TextDirection.ltr,
   )..layout();
   ```

3. Posicionamento — é aqui que mora o erro fácil:
   - o `y` do formato é a **linha de base** (como no SVG); o `TextPainter`
     pinta a partir do topo. Desloque por
     `painter.computeDistanceToActualBaseline(TextBaseline.alphabetic)`.
   - `align`: `left` → `x`; `center` → `x - width/2`; `right` → `x - width`.
   - `letterSpacing` no SVG/`resvg` é aplicado **depois de cada glifo,
     inclusive o último**, o que afeta a largura usada pelo `text-anchor`. O
     Flutter faz o mesmo, mas **confirme com um teste** de texto centralizado
     com `letterSpacing != 0` (critério 3) — se divergir, compense a largura.
   - **não** habilite `textScaleFactor`/`textScaler` do ambiente: o render tem
     que ser independente das configurações de acessibilidade do dispositivo.

4. Sem fallback silencioso: se a família pedida não estiver carregada, o
   Flutter substitui por outra fonte sem avisar. Detecte isso em teste
   (renderize um caractere e compare com o golden) e falhe alto.

## Fora de escopo

- Runs cujos caracteres são todos SMuFL — o exportador já os converte em
  glifos (decisão D01-6 do projeto anterior). Se aparecer um caso não coberto,
  é bug de S03/S05, não deste passo.
- Letra com sílabas hifenizadas/extensores: são desenhados pelo Verovio como
  runs de texto e linhas comuns; nada especial aqui.

## Critérios de aceite

1. `flutter test` verde com testes de:
   - baseline: um run com `y` conhecido tem o topo do glifo `X` na posição
     esperada (compare com a métrica da fonte, tolerância 0,5 unidade);
   - os 3 alinhamentos, com e sem `letterSpacing`;
   - os 4 estilos (Regular/Italic/Bold/BoldItalic) produzem imagens
     **diferentes entre si** (guarda contra o bug de "bold italic virando só
     bold" que o projeto anterior encontrou em Clair de Lune).
2. Nenhuma substituição de fonte: teste que compara o `TextPainter.width` do
   run com a largura calculada pelas métricas da TTF carregada (diferença < 1%).
3. **Paridade visual por peça** (com R03 pronto, via harness de R05):
   registre a % de divergência da página 1 de Clair de Lune (a peça com mais
   texto do corpus) antes e depois deste passo. A expectativa, pelo histórico,
   é cair para a mesma ordem de grandeza das demais páginas; se ficar acima de
   **0,5%**, investigue antes de seguir e registre a causa.
4. Uma imagem de diff de Clair de Lune p.1 anexada nas notas de execução, com
   os pixels divergentes concentrados em bordas (antialiasing), não em
   deslocamento de linha inteira.

## Notas de execução

(a preencher por quem executar)
