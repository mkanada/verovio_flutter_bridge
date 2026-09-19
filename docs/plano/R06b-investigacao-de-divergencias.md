# R06b — Investigação e correção das páginas acima de 0,1%

**Depende de:** R06a · **Decisão necessária:** não

## Objetivo

Olhar cada página que passou de 0,1% e descobrir **por quê**, corrigindo no
passo de origem. É o trabalho que transforma um número ruim em um número bom
— e o único jeito honesto de chegar aos 99,9%.

## Ler antes (só isto)

- `compare/out/corpus/resultado.csv` (R06a).
- `../verovio_lottie/docs/plano/relatorio-paridade.md`, seção "Divergências
  categorizadas" — as categorias que já foram identificadas uma vez.

## Contexto que você precisa (não vá procurar, está aqui)

Catálogo de causas conhecidas, com o passo onde se conserta:

| Sintoma no diff | Causa provável | Onde consertar |
| --- | --- | --- |
| Halo fino em toda borda de glifo | antialiasing (`tiny-skia` × Impeller/Skia) | ninguém — é o piso de ruído |
| Linha de texto inteira deslocada em Y | linha de base | R04b |
| Texto centrado deslocado em X | largura/âncora, `letterSpacing` | R04c |
| Bloco de texto com peso/inclinação errada | fonte não registrada, itálico sintético | R04a/R04d |
| Glifo mais fino que o do SVG | traço do glifo ausente | R03b |
| Linha tracejada fora de fase | utilitário de dash | R02c |
| Elemento com rotação no lugar errado | sinal do ângulo ou pivô | R02b |
| Elemento visível na cena e ausente no SVG | `hidden` ignorado | R02b |
| Linhas 10× mais grossas/finas | escala aplicada ao `strokeWidth` | R02c |
| Elemento certo, ordem errada (algo por cima do que devia estar por baixo) | percurso reordenado | R02b |

No corpus há três configurações raras que **só aparecem em peças
específicas** — se o diff apontar para elas, é aqui que estão:

- **Tracejado**: 8 ocorrências, todas de classe `octave`, em Chopin Étude (5)
  e Clair de Lune (3).
- **Rotação**: 8 ocorrências, todas de classe `arpeg` com ângulo −90, em
  Chopin Nocturne (1) e Clair de Lune (7).
- **`hidden`**: 116 nós, todos de classe `note`.

Linha de base do projeto anterior (mesma tolerância, mesmo corpus):
**0,0135% – 0,3946%, média 0,1251%**. As peças mais difíceis lá foram
Nocturne (0,55% de média) e Clair de Lune (0,45%) — as duas com mais texto.

## O que fazer

1. Listar, do CSV, todas as páginas acima de **0,1%**, em ordem decrescente.
2. Para cada uma: abrir o diff, ampliar a região de maior concentração,
   classificar pela tabela acima e **registrar** a classificação.
3. Corrigir no passo de origem (não no harness, não com tolerância maior),
   rodar de novo os critérios daquele passo, e remedir a página.
4. Repetir até que a média do corpus fique abaixo de 0,1% ou até que o que
   sobrou seja demonstravelmente ruído de antialiasing.
5. Guardar, para cada categoria encontrada, **um recorte PNG de exemplo** —
   R06c vai usá-los no relatório.

## Fora de escopo

- Aumentar a tolerância do diff para melhorar o número. A tolerância é 32 e
  está fixa desde o projeto anterior; mudá-la invalida toda a comparação
  histórica.
- Mudanças no formato/exportador para "facilitar" o render, sem medir.

## Critérios de aceite

1. Toda página acima de 0,1% tem uma causa registrada (categoria + evidência
   visual), ou uma justificativa explícita de por que é ruído.
2. Toda correção feita cita o passo em que foi feita e foi revalidada pelos
   critérios daquele passo (incluindo o teste widget-vs-harness de R05c, que
   continua em 0 pixels).
3. A varredura foi refeita depois da última correção, e o CSV novo substituiu
   o antigo.
4. Recortes de exemplo guardados por categoria.
5. Se a média continuar acima de 0,1% depois de esgotar as causas: **pare** e
   leve ao usuário a lista de causas restantes com os números — não declare o
   passo concluído.

## Notas de execução

Primeira investigação (2026-09-19, categoria "forma certa, espessura errada").

**Sintoma:** colchetes de pedal do Clair de Lune (retângulos de 18 unidades =
1,8 px, ex. `x=3948 y=5550 w=3489 h=18`) saíam na cena com **2 fileiras
totalmente pretas** onde o SVG tem 1 preta + 1 borda suave (fileira 606:
cena 0 × SVG 59); hastes verticais ~0,4 px mais largas de cada lado; pontos
de aumento com bordas mais escuras (ex. 114 × 192). Medido em
`Clair_de_Lune__Debussy-p1` (fit 0,1): antes 53 578 px (0,8590%).

**Causa:** formas de "só preenchimento" (`SetPen(0)` em
`DrawFilledRectangle`, `DrawObliquePolygon`, `DrawDot`, `DrawVerticalDots`:
colchetes de pedal, feixes, pontos) ganhavam no exportador um traço
`strokeWidth = 1` para reproduzir a regra CSS global do SVG
(`rect {stroke:currentColor}`). No `resvg` esse hairline de 0,1 px é quase
invisível (experimento: `stroke:none` nos `rect` do SVG dá 0 px >32 de
diferença); no Impeller ele alarga a forma em um pixel inteiro
(experimento: mesmo retângulo num `.vsb` mínimo — com traço: fileiras
605/606 pretas; sem traço: 605 preta + 606 cinza 82, contra 59 do SVG,
dentro da tolerância 32).

**Correção (passo de origem: exportador, S05):**
`ApplyStrokeFromPen` em `verovio/src/bridgedevicecontext.cpp` agora emite
`hasStroke = false` (`"stroke": "none"`) quando `pen.GetWidth() <= 0`; todo
`SetPen(0)` existente combina com preenchimento, então nenhuma forma fica
sem canal. Supersede o fato de R02c ("`r` e `e` ... traçados com largura 1")
e §5.2 da especificação (exceção documentada + revisão). Glifos `u` não
mudam (o traço deles é parte do desenho, R03b).

**Revalidação:** `flutter test` 66/66 verde (inclui widget-vs-harness em
0 pixels, R05c), `flutter analyze` limpo; varredura refeita
(`compare-corpus.sh`, 34 páginas, 188 s, CSV substituído):
total 874 036 → 839 588 px (−3,9%), média 0,4122% → 0,3959%.
Clair de Lune p1−p4 −4,5k/−5,8k/−4,6k/−4,7k; Nocturne −1,2k..−7,0k (pontos +
feixes). Regressões pequenas (+0,1k..+1,3k, ≤0,02 pp) em páginas de feixe
(Étude, Butterfly, Mazurka, Maple, Scarlatti): churn de AA nas mesmas
bordas (pixels corrigidos e novos intercalados ao longo das arestas dos
feixes — Étude p1: 1 696 corrigidos × 2 598 novos), sem nada sistemático.
Efeito colateral: `.vsb` 66–2 159 bytes menores (bbox sem a expansão de
0,5 do traço fantasma). Recortes de evidência: `/tmp` não versionado
(crops `clair-pedal-*`, `etude-reg-*`); os diffs por página estão em
`compare/corpus/*-diff.png`.
