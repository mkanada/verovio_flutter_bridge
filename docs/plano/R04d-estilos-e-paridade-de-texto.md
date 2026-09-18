# R04d — Bold, itálico, bold+itálico e paridade do texto

**Depende de:** R04c, R03c · **Decisão necessária:** não

## Objetivo

Fechar o texto comum: os quatro estilos desenhando com a TTF certa (não com
itálico ou negrito **sintético**), e a medição de paridade na peça com mais
texto do corpus. Historicamente este é o passo que decide se o projeto bate o
requisito de 99,9%.

## Ler antes (só isto)

- `../verovio_lottie/docs/plano/D01-5-bold-italico-tempo.md` e
  `../verovio_lottie/docs/plano/D01-4-italico-sintetico-thorvg.md` — as duas
  armadilhas já pagas com dinheiro do projeto anterior.
- `score_bridge/lib/src/text_font.dart` (R04a) e `scene_painter.dart` (R04c).

## Contexto que você precisa (não vá procurar, está aqui)

- Distribuição de estilos medida no corpus (417 runs): 268 itálicos, 122
  negritos, e **50 runs bold+italic, todos no Clair de Lune**. Foi exatamente
  nessa peça que o projeto anterior descobriu o bug de "bold italic virando
  só bold".
- Por peça (`Times`/`Times, serif` somados):

  | Peça | Runs | Observação |
  | --- | ---: | --- |
  | Clair de Lune | 88 | 50 bold+italic — o caso difícil |
  | Chopin Nocturne | 89 | 55 itálicos, 30 negritos |
  | Chopin Étude | 64 | mistura de `Times` e `Times, serif` |
  | Maple Leaf Rag | 46 | 16 sem estilo |
  | as demais | 12 a 34 | pouco texto |

- **Itálico sintético é o inimigo.** Se o `TextStyle` pedir
  `FontStyle.italic` e a TTF itálica não estiver registrada para aquela
  combinação peso+estilo, o motor inclina a fonte regular por conta própria.
  O resultado é *quase* igual — e some no meio do diff como "ruído de
  antialiasing". A guarda é o critério 2: as quatro combinações têm que
  produzir imagens **diferentes entre si**, e a bold+italic tem que diferir
  tanto da bold quanto da italic.
- O `resvg` do lado de referência recebe as 4 TTFs explicitamente (ver o
  array `FONTS` em `compare/scripts/compare-page.sh`) e resolve estilo por
  `font-weight`/`font-style` do `<text>`, que o Verovio emite a partir do
  mesmo `FontInfo` que virou `bold`/`italic` no `.vsb`. Os dois lados
  **partem do mesmo estado** — qualquer divergência de estilo é erro de
  registro de fonte no Flutter, não do formato.
- Meta numérica: o projeto anterior fechou o corpus em **0,0135% – 0,3946%,
  média 0,1251%** com texto pronto. Aqui o alvo é média **< 0,1%** (R06c).
  Se Clair de Lune p.1 ficar acima de **0,5%** depois deste passo,
  investigue antes de seguir.

## O que fazer

1. Conferir que os 4 assets estão declarados com os pares
   `weight`/`style` corretos (R04a) e que o `TextStyle` pede
   `FontWeight.w700` (não `FontWeight.bold`, que é o mesmo valor mas some em
   busca textual) e `FontStyle.italic`.
2. Medir Clair de Lune p.1 **antes** de qualquer ajuste deste passo e depois
   — os dois números vão para as notas. É o único jeito de saber se o passo
   fez efeito.
3. Medir também p.1 de Nocturne e de Chopin Étude (as outras duas com muito
   texto).
4. Para cada página medida, abrir o diff e classificar o resíduo: borda de
   glifo (aceitável) × linha inteira deslocada (bug de baseline, R04b) ×
   bloco inteiro divergente (estilo ou fonte errada).

## Fora de escopo

- Varredura completa do corpus (R06a) — aqui são 3 páginas escolhidas.
- Hifenização/extensores de letra: o Verovio já os desenha como runs de texto
  e linhas comuns; nada de especial.

## Critérios de aceite

1. `flutter analyze` limpo, `flutter test` verde.
2. Teste dos 4 estilos: renderizadas as 4 combinações da mesma string, as 4
   imagens são **duas a duas diferentes** (compare os bytes; uma igualdade
   significa que uma das TTFs não foi usada).
3. Teste de largura por estilo: a largura de cada estilo bate com as métricas
   da TTF **daquele arquivo** (diferença < 1%) — pega itálico sintético, que
   preserva a largura da regular.
4. **Paridade**: Clair de Lune p.1 medida antes e depois, com os dois números
   e a imagem de diff nas notas. Depois do passo, abaixo de **0,5%**; se
   ficar acima, a causa investigada e registrada.
5. Nocturne p.1 e Chopin Étude p.1 medidas e registradas.
6. Na inspeção dos diffs, o resíduo de texto está em **bordas**, não em
   deslocamento de linha inteira nem em bloco sólido.

## Notas de execução

(a preencher por quem executar)
