# R04a — Fontes: carregar as TTFs e resolver `family`

**Depende de:** R02b · **Decisão necessária:** não

## Objetivo

Garantir que o Flutter desenhe texto com **exatamente** a mesma fonte que o
`resvg` usa para o SVG de referência, e que uma substituição silenciosa de
fonte seja impossível. Sem isso, toda medição de texto dos passos seguintes é
areia movediça.

## Ler antes (só isto)

- [Especificação](../formato/especificacao-v1.md), seção **5.4**.
- `compare/svg_render/src/main.rs` L100-L125 (como o PNG de referência
  resolve fonte: `load_system_fonts`, `load_font_file` e `set_serif_family`).
- `compare/scripts/compare-page.sh`, o array `FONTS` (a lista exata passada
  ao `svg_render`).

## Contexto que você precisa (não vá procurar, está aqui)

**O campo `family` do formato não é o nome de uma fonte instalável.** Medido
no corpus, `t.family` só assume dois valores:

| Valor | Ocorrências | De onde vem |
| --- | ---: | --- |
| `"Times"` | 294 | `FontInfo::GetFaceName()` — o nome da fonte de texto do Verovio |
| `"Times, serif"` | 123 | fallback do exportador quando a face está vazia (mesmo default do `font-family` da raiz `<svg class="definition-scale">`) |

E no SVG de referência **nenhum** `<text>` carrega `font-family`: todos
herdam `font-family="Times, serif"` da raiz (confirmado no SVG gerado da
Chopin Étude p.1 — 27 elementos `<text>`, zero atributos `font-family`). O
`svg_render` resolve o genérico `serif` com
`fontdb.set_serif_family("Liberation Serif")`, passado pelo script como
`--pin-serif-family "Liberation Serif"`.

**Conclusão operacional:** no renderizador Flutter, `"Times"` e
`"Times, serif"` significam **a mesma coisa** — a serifada do projeto,
Liberation Serif. Mapeie os dois (e qualquer valor desconhecido) para a
família carregada, com um ponto único de decisão, e registre nas notas que o
mapeamento é deliberado. Usar `family` cru como `fontFamily` do `TextStyle`
faz o Flutter procurar uma fonte chamada "Times", não achar, e cair no
fallback do sistema **sem avisar** — divergência garantida e difícil de
enxergar.

As TTFs estão em `verovio/data/text/`:
`LiberationSerif-{Regular,Italic,Bold,BoldItalic}.ttf` (as quatro, mais o
`LiberationSerif-OFL.txt` da licença).

## O que fazer

1. Copiar as 4 TTFs para `score_bridge/fonts/` e declará-las no
   `pubspec.yaml` do pacote:

   ```yaml
   flutter:
     fonts:
       - family: Liberation Serif
         fonts:
           - asset: fonts/LiberationSerif-Regular.ttf
           - asset: fonts/LiberationSerif-Italic.ttf
             style: italic
           - asset: fonts/LiberationSerif-Bold.ttf
             weight: 700
           - asset: fonts/LiberationSerif-BoldItalic.ttf
             weight: 700
             style: italic
   ```

   Copie também o arquivo de licença (OFL) para `score_bridge/fonts/` — é
   requisito da licença ao redistribuir a fonte dentro de um pacote.

2. Ponto único de resolução, em `score_bridge/lib/src/text_font.dart`:

   ```dart
   const kScoreTextFamily = 'Liberation Serif';
   const kScoreTextFamilyPackage = 'score_bridge';
   // "Times", "Times, serif" e desconhecidos -> kScoreTextFamily
   String resolveFamily(String vsbFamily);
   ```

3. Em teste/headless, as fontes do pacote **não** são carregadas
   automaticamente em todos os caminhos: carregue explicitamente com
   `FontLoader('Liberation Serif')` alimentado pelos bytes do asset, num
   helper de teste reaproveitável (`test/support/load_fonts.dart`), e chame-o
   também do `compare` quando ele for renderizar.

4. Detecção de substituição: meça a largura de uma string conhecida com o
   `TextPainter` e compare com a largura calculada a partir das métricas da
   própria TTF (`hmtx`/`head`). Se a fonte não estiver carregada, o número
   não bate — e o teste **falha alto**, em vez de o diff ficar 3% pior sem
   explicação.

## Fora de escopo

- Desenhar runs (R04b) e alinhamento (R04c).
- Caminho de render de SMuFL por TTF (o formato carrega os metadados, mas o
  canônico é contorno — ver `CLAUDE.md`).

## Critérios de aceite

1. `flutter analyze` limpo, `flutter test` verde.
2. Teste de mapeamento: `resolveFamily("Times")`,
   `resolveFamily("Times, serif")` e `resolveFamily("qualquer coisa")`
   devolvem todos `kScoreTextFamily`.
3. Teste antifallback: a largura de `"Allegro molto agitato."` a `size: 405`
   medida pelo `TextPainter` bate com a largura calculada pelas métricas da
   TTF carregada, com diferença **< 1%**. O teste tem que **falhar** se você
   remover o `FontLoader` (verifique isso na mão uma vez e registre nas
   notas).
4. Teste dos 4 arquivos: cada um dos 4 estilos produz larguras diferentes
   para a mesma string (guarda contra declarar 4 assets e o Flutter carregar
   só um).
5. A licença OFL acompanha as fontes dentro do pacote.

## Notas de execução

(a preencher por quem executar)
