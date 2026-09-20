# R06b — Investigação e correção das páginas acima de 0,1%

**Depende de:** R06a · **Decisão necessária:** não

## Objetivo

Olhar cada página que passou de 0,01% e descobrir **por quê**, corrigindo no
passo de origem. É o trabalho que transforma um número ruim em um número bom
— e o único jeito honesto de chegar aos 99,99%.

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

1. Listar, do CSV, todas as páginas acima de **0,01%**, em ordem decrescente.
2. Para cada uma: abrir o diff, ampliar a região de maior concentração,
   classificar pela tabela acima e **registrar** a classificação.
3. Corrigir no passo de origem (não no harness, não com tolerância maior),
   rodar de novo os critérios daquele passo, e remedir a página.
4. Repetir até que a média do corpus fique abaixo de 0,01% ou até que o que
   sobrou seja demonstravelmente ruído de antialiasing.
5. Guardar, para cada categoria encontrada, **um recorte PNG de exemplo** —
   R06c vai usá-los no relatório.

## Fora de escopo

- Aumentar a tolerância do diff para melhorar o número — **exceção
  registrada**: em 2026-09-19 o usuário mandou trocar 32 → **128/255** e o
  portão 99,9% → **99,99%** ("libero de um lado pra restringir do outro,
  ignorando problemas de AA"). Vale dali em diante; números medidos a 32
  (R02d–R06a, linha de base do `verovio_lottie`) continuam citados como
  "medidos a 32" e não são comparáveis aos novos.
- Mudanças no formato/exportador para "facilitar" o render, sem medir.

## Critérios de aceite

1. Toda página acima de 0,01% tem uma causa registrada (categoria + evidência
   visual), ou uma justificativa explícita de por que é ruído.
2. Toda correção feita cita o passo em que foi feita e foi revalidada pelos
   critérios daquele passo (incluindo o teste widget-vs-harness de R05c, que
   continua em 0 pixels).
3. A varredura foi refeita depois da última correção, e o CSV novo substituiu
   o antigo.
4. Recortes de exemplo guardados por categoria.
5. Se a média continuar acima de 0,01% depois de esgotar as causas: **pare** e
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
invisível (experimento a tolerância 32: `stroke:none` nos `rect` do SVG dá
0 px >32 de
diferença); no Impeller ele alarga a forma em um pixel inteiro
(experimento: mesmo retângulo num `.vsb` mínimo — com traço: fileiras
605/606 pretas; sem traço: 605 preta + 606 cinza 82, contra 59 do SVG,
dentro da tolerância 32 da época).

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

---

Segunda investigação (2026-09-19, tolerância **128/255**, percentuais com 6
casas, portão **99,99%** — decisão do usuário, ver "Fora de escopo" acima).
Varredura refeita (`compare-corpus.sh`, 34 páginas, ~188 s, CSV substituído;
PNGs de cena/SVG byte-idênticos aos da varredura anterior — determinismo
confirmado por `cmp`): total 27 420 px, **média 0,012930%** (99,9871%).
**26/34 páginas passam** (≤ 0,01%); 8 ficam acima, todas classificadas abaixo.
Morfologia no corpus inteiro (limiar 128): só 0,73% dos pixels divergentes
são órfãos (>2 px de qualquer tinta do outro lado); 20–30% são franja clara
nos dois lados; o resto é borda adjacente — ou seja, o resíduo é quase todo
ruído de borda, não conteúdo.

| Página (>0,01% a 128) | % | Categoria (tabela do passo) | Evidência |
| --- | --- | --- | --- |
| Clair p4 0,088215% (5 502 px) | — | **Artefato da referência** (mãos PUA; ver abaixo) + halo de borda | `r06b-hands-*` |
| Clair p1 0,074892% (4 671 px) | — | idem | hotspot (600,400); órfãos 1 248 px |
| Étude p1 0,031698% / p2 0,030335% | — | Halo fino em toda borda (**ruído**, Impeller × tiny-skia) | `r06b-edge-*` (título/feixes idênticos a olho nu) |
| Satie p1 0,028171% | — | idem (texto de andamento + ♩) | hotspot (600,100) |
| Nocturne p4 0,019593% / p3 0,015264% | — | Espaços em texto (correção abaixo) + halo | `r06b-dim-*` (p5: 0,018470% → **0,008594%**, passa) |
| Mazurka p1 0,013115% | — | Halo (rubato/feixes idênticos) | hotspot (400,1100) |

**Categorias novas encontradas (com correção ou justificativa):**

1. **Espaços em texto comum — CORRIGIDA (origem: exportador, R04).**
   Sintoma: extensor `(dim. -     - ...)` (Nocturne p5) com hifens espalhados
   na cena e colados no SVG; mesma família em `'     con sordina'` e
   `'…75\n'` (Clair). Causa: o Verovio nunca emite `xml:space`/`textLength`,
   então o resvg colapsa espaços — mas `SvgDeviceContext::DrawText` (L1107)
   troca antes o primeiro/último `' '` por NBSP (não-colapsável). O
   exportador passava a cadeia crua e o Flutter preservava tudo. Correção em
   `BridgeDeviceContext::DrawText`: réplica literal (sentinela NBSP nas
   bordas → strip/colapso → reconversão; comentário no código cita as linhas
   do SVG). Prova de que a réplica está exata: primeira versão (só colapso)
   regrediu Satie/Maple (+1k/+1,6k px) porque removia o avanço que o NBSP
   garante — reproduzido old-vs-new binary run a run; versão final volta
   Satie/Maple ao baseline e zera os runs multi-espaço no corpus (4 → 0).
   Revalidação: `flutter test` 66/66 (widget-vs-harness 0 px), `flutter
   analyze` limpo, varredura refeita: Nocturne p5 sai da lista (>0,01%),
   média 0,013242% → **0,012930%**.
2. **Mãos PUA ☛☛ vs `pp` (Clair p1/p4) — ARTEFATO DA REFERÊNCIA, sem correção
   (decisão herdada D01-6).** O MXL traz `<words font-family="Leland Text">`
   com U+E520 U+E520; o Verovio emite os codepoints crus no `<tspan>` (sem
   família); nenhum loaded font do `svg_render` é consultado na ordem certa
   e o resvg cai no **OpenSymbol do sistema** (prova: strip `/tmp/e520-fonts`
   — Leipzig=Bravura=Leland=Gootville dão `p`, OpenSymbol dá ☛). O `.vsb`
   carrega `Leipzig:E520` (vetor `p`, musicalmente correto — a edição quer
   dizer `pp`) pelo caminho D01-6, deliberado no projeto anterior. Perseguir
   a referência aqui seria vendorar um acidente de fontconfig desta máquina;
   em máquina sem OpenSymbol a referência muda sozinha. Recortes
   `r06b-hands-{svg,scene}.png` (também `morendo` em p4).
3. **Halo duro de borda (todo o resto) — RUÍDO.** Nos hotspots de Étude, Satie,
   Mazurka e Nocturne p3/p4, cena e SVG são visualmente idênticos (títulos
   "molto agitato.", "douloureux ♩= ca. 76", "rubato", "a tempo", feixes,
   colchetes): os pixels >128 são transições onde o Impeller dá preto puro e
   o resvg dá cinza médio (ex. fileira 606 do pedal: 0 × 59 a tol 32; a 128
   restam os casos 0 × 130+). Sem ponto de correção no nosso código ou no
   formato — é a curva de AA dos motores.

**Configurações raras verificadas (todas OK, sem diff associado):**
tracejado — 8 formas `dash=[36,72]` (Étude p2/p3/p4, Clair p2/p4) com fase
visual conferida lado a lado (`r06b-dash-*`); rotação — `arpeg` −90° da
Nocturne p7 no lugar (`r06b-arpeg-*`); `hidden` — 0 formas sob nós `hidden`
no corpus (o pintor já os pula, R02b).

**Critério 5 (parada honesta):** média **0,012930% > 0,01%** e 8 páginas acima
de 0,01% após esgotar as causas corrigíveis (o que resta é halo de motor +
artefato de fonte da referência, nenhum dos dois endereçável sem caçar
artefato). Passo **não concluído** — segue a lista acima com os números.
Recortes por categoria em `compare/corpus/r06b-{hands,dim,dash,arpeg,edge}-*.png`
(versionados, para o R06c).

---

Terceira investigação (2026-09-20, após correção do corpus: PUA `E520` do
Clair de Lune trocado por `<dynamics><pp/>` semântico, ver commit
`146990d`). Varredura refeita (`compare-corpus.sh`, 34 páginas, 187 s):
total 27 420 → **22 947 px (−16,3%)**, média 0,012930% → **0,010821%**.
Só Clair p1 (4 671 → 2 409) e p4 (5 502 → 3 291) mudaram — as outras 32
páginas deram delta 0, confirmando o determinismo.

Morfologia das 8 páginas acima de 0,01% (limiar 128, dilatação 2 px):
**0 pixels órfãos em todas** (antes: 1 248 só no Clair — era o conteúdo das
mãos; agora não há nenhum conteúdo presente de um lado e ausente do outro).
Assinatura de halo (um lado preto puro, outro cinza médio): 40–60% na
maioria; Clair p4 17% — região densa (feixes + `morendo` bold-itálico +
pontos), mas ainda 100% borda-adjacente. Concentração difusa: a célula
hottest detém 9–23% dos divergentes (Clair p4 20% pelos feixes), sem um
elemento isolado. Conferência visual dos 8 hotspots (SVG × cena lado a
lado): idênticos — `molto agitato.`/`cresc.`, `douloureux ♩= ca. 76`,
`a tempo`, `legato`/`rubato`, título `Clair de Lune`, `pp con sordina`,
`pp morendo jusqu'à la fin`.

Categoria "mãos PUA" **encerrada como causa**: os dois pontos agora
convergem (`pp` via `DrawMusicText` + texto itálico comum). Evidência
"depois" em `compare/corpus/r06b-hands-fixed-p{1,4}-{svg,scene}.png` (os
`r06b-hands-*` antigos ficam como evidência do "antes").

**Critério 5 (parada honesta, reafirmado):** média **0,010821% > 0,01%**
(faltam ~1 740 px; só Étude p1+p2 têm 3 869 px de halo puro) e 8 páginas
acima de 0,01%, sem nenhuma causa corrigível restante no nosso código, no
formato ou nas peças — o resíduo é curva de AA Impeller × tiny-skia.
Passo **não concluído** — R06c decide com estes números.
