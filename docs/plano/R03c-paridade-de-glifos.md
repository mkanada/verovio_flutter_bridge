# R03c — Paridade parcial: a página só com formas e glifos

**Depende de:** R03b, R02d · **Decisão necessária:** não

## Objetivo

Medir onde estamos com formas + glifos prontos e **texto comum ainda
ausente**. Este é o ponto de controle que separa "erro de glifo" de "erro de
texto": depois dele, toda divergência restante tem que estar em título,
indicação de andamento, dedilhado ou número de compasso — nunca dentro do
pentagrama.

## Ler antes (só isto)

- Notas de execução de R02d (como você gerou o primeiro PNG) e de R03b.
- `compare/scripts/compare-page.sh` (o trecho SVG→PNG).

## Contexto que você precisa (não vá procurar, está aqui)

- Quanto o texto comum pesa em cada peça (contagem de runs `t` no `.vsb`):
  Gymnopédie 21, Prelúdio 19, Scarlatti 21, Little bird 12, Butterfly 23,
  Mazurka 34, Maple Leaf Rag 46, Étude 64, Clair de Lune 88, Nocturne 89.
  Escolha **Gymnopédie ou Scarlatti** para este passo (pouco texto) e deixe
  Clair de Lune para R04d (muito texto, e o texto dela é grande: 50 runs
  bold+italic).
- No projeto anterior, com texto comum ainda ausente, a divergência do corpus
  era de **alguns por cento** e caiu para 0,13% de média quando o texto
  entrou. Ordem de grandeza esperada aqui: poucos por cento, concentrada em
  blocos retangulares onde deveria haver texto.
- A tolerância do diff é sempre **32/255 por canal** — todo número citado no
  plano usa essa tolerância; um número medido com outra não é comparável.
- Sintomas e onde está o bug:

  | Sintoma no diff | Causa provável | Passo |
  | --- | --- | --- |
  | Glifo espelhado ou de cabeça para baixo | `scale(1,-1)` do XML | S03 (volte e registre) |
  | Todos os glifos deslocados por um mesmo vetor | `origin`/`fit` | R02b |
  | Glifos 10× maiores/menores | confusão entre escala de bbox e de contorno | R03a |
  | Glifos no lugar certo mas finos demais | traço do glifo ausente | R03b |
  | Cabeça de nota certa, haste deslocada | haste é `p`, não glifo | R02c |
  | Divergência só nas bordas, uniforme | antialiasing | esperado, dentro da tolerância |

## O que fazer

1. Gerar, para 2 peças (uma MEI e uma MusicXML) e 2 páginas cada, os PNGs do
   SVG e da cena, e rodar `compare diff` com tolerância 32.
2. Registrar os 4 percentuais nas notas, junto com o backend gráfico usado.
3. Abrir cada imagem de diff e **classificar** o resíduo. O critério não é o
   número: é a localização do resíduo.
4. Contar quantos `ui.Path` distintos foram construídos por página e
   confirmar que bate com o dicionário, não com os usos.

## Fora de escopo

- Corrigir divergência de texto (R04) — só confirmar que é texto.
- Varrer o corpus inteiro (R06a).

## Critérios de aceite

1. Quatro páginas medidas, com percentual e imagem de diff anexados nas
   notas.
2. **Nenhuma divergência dentro dos pentagramas** na inspeção visual dos
   diffs: cabeças de nota, hastes, claves, acidentes, pausas e barras
   coincidem. Se houver, o passo não está concluído — volte ao passo indicado
   na tabela acima antes de seguir.
3. Nenhum glifo espelhado, invertido ou fora de escala.
4. O resíduo restante é visivelmente **texto** (retângulos onde deveria haver
   título/andamento/dedilhado) — declare isso explicitamente nas notas.
5. Nº de `Path` construídos por página == nº de glifos distintos usados
   naquela página.

## Notas de execução

Executado em 2026-09-19. Peças (1 MEI + 1 MusicXML, 2 páginas cada):
`corpus/mei/Scarlatti_Sonata_in_C-major.mei` (p1-p2 de 3) e
`corpus/musicxml/Erik_Satie_-_Gymnopedie_No.1.mxl` (p1-p2 de 2). Cena dos
`.vsb` de `compare/out/s08/` (inalterados desde S08); `compare` rebuildado
com o pintor de R03b (`flutter build linux --release` ok). Backend ativo
(log do embedder sob xvfb): **Impeller (OpenGLES-SDF)**, Flutter 3.47.4 —
a decisão Impeller×Skia continua em R05a. Artefatos em `compare/out/r03c/`
(`*-svg.png`, `*-scene.png`, `*-diff32.png`, todos 2100×2970).

Percentuais (`compare diff --tolerance 32`, 6 237 000 px, maxDiff 255):

| Página | Diferentes | % |
| --- | ---: | ---: |
| Satie p1 | 29 977 | **0,4806%** |
| Satie p2 | 4 462 | **0,0715%** |
| Scarlatti p1 | 18 652 | **0,2991%** |
| Scarlatti p2 | 13 029 | **0,2089%** |

(Em R02d, sem glifos, as mesmas p1 davam 2,04%/1,96%: a queda para <0,5%
é a tinta dos glifos entrando.)

Classificação do resíduo (inspeção dos 4 `*-diff32.png` + análise por
componentes conexos com PIL/numpy, caixas de texto vindas dos runs `t` do
`.vsb` mapeadas a pixels por `px = (x+500)*0.1`):
- **Todo componente sólido de diff (>100 px) toca um run de texto**: 74/74
  (Satie p1), 8/8 (Satie p2), 16/16 (Scarlatti p1), 11/11 (Scarlatti p2).
  São título ("Gymnopédie No.1", "Suite I"), "Lent et douloureux = ca. 76",
  "con pedale", "cresc.", dinâmicas (`pp`, `ppp`, `mp`, `f`, `p`),
  etiquetas "Piano"/"Pno.", números de compasso (8, 17, 26, 34, 42 / 6,
  12, 16, 20, 26, 31, 37, 43, 48, 52), marcas de repetição "(1)", "(2)",
  "1", "2" e o rodapé "MEI engraved with Verovio" — **declaro: o resíduo
  restante é visivelmente texto** (R04), como esperado.
- Todo o resto do diff são componentes de ≤100 px (≈99% com ≤5 px, ~75%
  pixels isolados), espalhados uniformemente por todas as faixas-y:
  **antialiasing de borda Impeller vs tiny-skia**, esperado e dentro da
  tolerância (sintoma "divergência só nas bordas, uniforme" da tabela).
- **Nenhuma divergência dentro dos pentagramas**: cabeças, hastes, claves,
  acidentes, pausas, barras e ligaduras aparecem em cinza (coincidem);
  nenhum glifo espelhado, invertido ou fora de escala (tabela de sintomas:
  nada de S03/R02b/R03a/R03b a corrigir).

`Path` construídos por página (pintura via `ScenePainter` com `GlyphCache`
fresco, conferido em teste temporário depois removido): Satie p1 **15**,
Satie p2 **8**, Scarlatti p1 **20**, Scarlatti p2 **18** — iguais aos
distintos `u.g` usados na página (348/69 e 388/521 usos), não aos usos.
