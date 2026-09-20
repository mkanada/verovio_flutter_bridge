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

---

Quarta investigação (2026-09-19, regeneração completa do corpus a partir do
zero — `verovio -t svg` + `resvg` para a referência, `verovio -t vsb` +
`score_bridge`/Impeller para a cena — para confirmar a linha de base antes
de aprofundar). Varredura idêntica pixel a pixel à da terceira investigação
(`cmp` limpo em todos os 34 PNGs de svg/scene/diff; só `bytes_vsb` variou,
por timestamp do zip): mesma média 0,010821%, mesmas 8 páginas acima de
0,01%. Aprofundamento pedido pelo usuário nas 8 páginas restantes.

**Achado: o resíduo inteiro das 8 páginas é texto comum, não notação.**
Auditoria visual das 8 páginas (diff de página inteira, sem recorte) em 5
peças — Étude p1/p2, Clair p1/p4, Satie p1, Nocturne p3/p4, Mazurka p1: em
todas, **100% dos pixels divergentes caem exatamente sobre a borda de glifos
de texto comum** desenhados por `TextPainter` em
`score_bridge/lib/src/text_run.dart` (títulos, marcas de tempo, dinâmica
textual, expressões — `Allegro molto agitato.`, `cresc.`, `con forza`,
`ritard.`, `a tempo`, `sotto voce`, `Lent et douloureux ♩= ca. 76`,
`con pedale`, `morendo jusqu'à la fin`, `piano`, `Adagio`, `poco rall.`) e
**0% caem sobre elemento desenhado pelo dicionário de contornos SMuFL**
(cabeças de nota, hastes, feixes, ligaduras, hairpins de dinâmica, ou `pp`
via `DrawMusicText`/glifo Leipzig — o caminho que já bateu paridade em
R03c). Notas, feixes e ligaduras nos mesmos recortes onde o texto vizinho
está vermelho continuam cinza puro. Evidência:
`compare/corpus/r06b-text-vs-glyph-{svg,scene,diff}.png` (recorte de Étude
p1 com o feixe do compasso 4 limpo ao lado de `cresc.` inteiro em vermelho,
no mesmo recorte).

**Duas medições descartam bug de posição/geometria, a favor de diferença de
motor de texto:**

1. Correlação por deslocamento inteiro (busca em ±4 px em x/y, região
   `pp morendo jusqu'à la fin` de Clair p4): o erro quadrático mínimo já
   está em deslocamento **(0,0)** — não há shift de texto inteiro escondido
   atrás do ruído de AA.
2. Viés de luminância nos pixels divergentes (5 páginas amostradas): entre
   58% e 72% (média ~66%) têm o pixel da **referência mais escuro** que o da
   cena — ou seja, o texto do Impeller tende a cobrir a borda do glifo com
   *menos* tinta que o resvg, de forma consistente, não 50/50 aleatório.
   `Maior diferença de canal observada: 255` nos logs confirma que parte
   dessas bordas chega a virar preto-puro × branco-puro, não só um degradê
   suave — comportamento típico de hinting/grade de pixel aplicado por um
   motor e não pelo outro, não de ruído de sub-pixel simétrico.

**Interpretação:** `score_bridge` desenha glifos SMuFL a partir do
dicionário de contornos exportado (mesma geometria dos dois lados — por
isso batem) mas desenha texto comum via `TextPainter`/`TextSpan`, que
delega no *shaping* e na rasterização de fonte do próprio motor Flutter
(Skia/Impeller — hinting, grade de pixel, blend de cobertura). O `resvg` da
referência renderiza a mesma TTF por um caminho diferente (sem o
hinting/grade do Flutter). A divergência que sobra não é um bug no
exportador do Verovio, no formato `.vsb` nem no ajuste de página/escala do
`score_bridge` — é a arquitetura de duas rotas de desenho (contorno
vetorial × fonte real) escolhida em R04a, cada uma com seu próprio piso de
AA, e só a rota de fonte real tem esse piso. Não há bandeira pública em
`dart:ui`/`TextPainter` para desligar hinting e igualar ao resvg.

**Fora do escopo desta investigação (decisão do usuário, não decidida
aqui):** o único jeito de zerar esse piso seria tratar texto comum como
SMuFL — converter cada glifo de texto comum em contorno vetorial na
exportação (reusar o mesmo dicionário glyphId→contorno) e desenhar como
path preenchido no `score_bridge`, em vez de `TextPainter`. Isso é uma
mudança de arquitetura (mexe em R04a-R04d e no formato), não uma correção
pontual — do mesmo porte que D-BIN/D-RUNTIME. Não implementado sem decisão
explícita.

**Critério 5 (parada honesta, reafirmado com causa mais precisa):** média
**0,010821%** inalterada, 8 páginas acima de 0,01%, e agora com causa
**100% localizada e explicada** (texto comum via motor de fonte real) em
vez de "halo genérico de motor". Passo continua **não concluído** — a
única correção que fecharia o número é a mudança de arquitetura acima,
que precisa ir ao usuário antes de qualquer código.

---

Spike de viabilidade (2026-09-19, fora do exportador, só para instrumentar a
decisão acima — nenhum código de produção mudou). Pergunta: se texto comum
fosse desenhado como contorno vetorial (como SMuFL) em vez de `TextPainter`,
o piso realmente some?

**Método:** extraído com `fontTools` (Qu2CuPen, `all_cubic=True`) o contorno
real de `c`/`r`/`e`/`s`/`.` de `LiberationSerif-Italic.ttf`, convertido para
o formato `paths` (`v`/`i`/`o`) de `glyphs.json` (§4), montado um `.vsb-json`
mínimo com "cresc." como 6 ocorrências `u` (mesmo mecanismo de R03b, nenhuma
fonte carregada no lado do Flutter), posicionadas por avanço de `hmtx` +
kerning clássico da tabela `kern` (par `r→e -76` unidades — sem ele o
acúmulo de posição por si só já bastava para gerar divergência, uma
armadilha do próprio spike, não do motor). Referência: SVG autônomo
equivalente (`<text font-family="Liberation Serif" font-style="italic">`),
mesmo `svg_render`/`resvg` do pipeline oficial. Arquivos:
`compare/corpus/r06b-textpath-experiment-{svg,scene,diff}.png`.

**Resultado:** a **0 pixels divergentes em 50 000 (0,000000%)** na
tolerância oficial (128); maior diferença de canal 82 (abaixo do limiar). Na
tolerância histórica de 32/255 (a mesma que já classificava SMuFL como
paridade), 94 px (0,188%) — mesma ordem de grandeza do piso que os glifos
SMuFL já aceitam, não da ordem dos 0,03-0,05% que o texto via `TextPainter`
mostra nas páginas reais. Ou seja: **o piso desaparece** ao trocar
`TextPainter` por contorno vetorial — a causa raiz é mesmo a rota de
desenho, não uma característica inerente ao par Impeller/resvg em si.

**O que isso muda na decisão:** a opção "converter texto comum em contorno
vetorial" (registrada acima como fora de escopo/decisão do usuário) tem
agora evidência direta de que **funcionaria** para fechar o portão de
99,99%, não é só uma hipótese teórica. O custo continua real e não medido
por este spike: (1) Verovio não tem hoje nenhuma biblioteca de parsing de
TTF (`grep` em `verovio/src`/`include` não acha FreeType/HarfBuzz/stb_tt) —
os contornos SMuFL vêm de um recurso pré-extraído (`Glyph`, `pugixml`), não
de parsing de fonte em tempo real; texto comum aceita qualquer caractere,
então precisaria de um caminho novo (candidato leve: `stb_truetype.h`,
single-header, cobre `cmap`/`glyf`/`hmtx`/`kern` clássico, mas não GPOS —
suficiente para o `kern` clássico da Liberation Serif usado aqui; ligaduras
e GPOS ficariam de fora numa primeira versão); (2) o restante da
infraestrutura (dicionário de glifos, `u`, `GlyphCache`) já existe e é
reuso, não trabalho novo; (3) risco principal não testado aqui: strings
maiores/multi-linha, alinhamento (`align`), `letterSpacing` combinado com
avanço por glifo, e fallback de fonte para caracteres fora da Liberation
Serif (a mesma classe de problema do D01-6/PUA, agora do lado do
exportador em vez do lado do `resvg`).

---

Quinta investigação (2026-09-19, pedido do usuário: "Investigue melhor Clair
de Lune página 4. Tem um problema de deslocamento de texto lá"). Achado:
**bug real de posicionamento, não ruído de motor** — explica a maior parte
do excesso de Clair p1/p4 sobre as outras 6 páginas acima de 0,01%.

**Sintoma medido:** nos runs de tinta de "morendo jusqu'à la fin" (linha
`pp morendo jusqu'à la fin`, y viewBox 21757), cada palavra começa
**9px constante mais à esquerda na cena que no SVG** (`morendo`: svg 723 ×
cena 714; `jusqu'à`: 870×861; `la`: 967×958; medidas em
`compare/corpus/Clair_de_Lune__Debussy-p4-{svg,scene}.png`, linha
y=2205-2240). Deslocamento **constante**, não crescente (descarta kerning
acumulado) e assimétrico entre lados (descarta AA). **Controle limpo**: a
mesma frase, em negrito, uma linha acima (y viewBox 21350, `class="tempo"`,
sem `pp` antes) bate pixel a pixel entre SVG e cena — única diferença entre
as duas linhas é ter ou não um `pp` na frente.

**Causa raiz, confirmada em 3 passos:**

1. No SVG bruto, o `pp` desta linha é **um único glifo PUA** (U+E52B, "pp"
   combinado do Leipzig — mesma família de caso do D01-6) dentro de
   `<tspan font-family="Leipzig" ... letter-spacing="90px">` seguido, na
   mesma `<text>`, pelo tspan de `" morendo jusqu'à la fin"` sem `x` próprio
   (herda a posição de onde o tspan anterior "terminou").
2. Reprodução isolada (`compare/svg_render` + SVG mínimo):
   `<tspan letter-spacing="90px">X</tspan><tspan>Y</tspan>` desloca "Y"
   exatamente **90 unidades** (9px nesta escala) a mais que
   `letter-spacing="0px">X</tspan>`, mesmo "X" sendo um único caractere sem
   nada depois dele dentro do próprio tspan — ou seja, `resvg`/CSS aplica
   `letter-spacing` **depois de cada caractere**, inclusive o único/último.
3. Em `verovio/src/bridgedevicecontext.cpp`, `DrawText` (ramo
   `allGlyphsAvailable`, glifos PUA/SMuFL) só soma `letterSpacing`
   **entre** caracteres: `if (!first && letterSpacing != 0) { m_textPenX +=
   letterSpacing; ... }`. Para uma string de 1 caractere, `!first` nunca é
   verdadeiro no laço, então o `letterSpacing` do glifo (90 unidades) nunca
   é somado a `m_textPenX`. O mesmo laço existe, idêntico, no ramo SMuFL
   puro logo acima.

**Efeito:** `m_textPenX` fica 90 unidades (9px) atrasado bem no ponto em
que o próximo `DrawText` ("morendo jusqu'à la fin") usa esse valor como
`run.origin`/`t.x` — dali em diante, cada glifo do run herda o mesmo atraso
constante. Como o run é longo (~500px), o número de pixels divergentes
gerados é grande — a causa direta de Clair p1/p4 serem as duas piores
páginas do corpus (0,0389%/0,0528%, muito acima das outras 6 páginas
"halo puro" que ficam em 0,013-0,032%).

**Por que o caso comum (duas letras "pp" separadas) não mostra este bug
hoje:** com 2 caracteres, o laço atual soma `letterSpacing` **uma vez**,
entre eles — que é exatamente onde o `resvg` também soma o primeiro (e
único, nesse caso, já que são só 2 glifos) intervalo. A lacuna *depois* do
2º glifo (que o `resvg` também adicionaria, pelo teste do item 2) só passa
a importar quando **algo mais usa `m_textPenX` depois** — isto é, quando a
dinâmica com `letterSpacing` está numa `<text>` composta com texto comum
na sequência, como aqui. Dinâmica isolada (nada depois na mesma `<text>`,
o caso mais comum) nunca expõe o bug porque ninguém lê o pente atrasado.

**Correção candidata (passo de origem: exportador, S05/R04 — não aplicada
nesta investigação, aguardando decisão de priorização):** somar
`letterSpacing` depois de **cada** glifo nos dois laços de `DrawText`
(SMuFL puro e `allGlyphsAvailable`), não só entre eles — iguala ao modelo
do CSS confirmado no item 2. Risco baixo: no caso comum (nada consome o
pente extra depois), a mudança não tem efeito visível; revalidação ainda
precisa rodar `flutter test` (66/66, incl. widget-vs-harness R05c em 0px) e
a varredura completa do corpus para confirmar que nenhuma das 26 páginas
que já passam regride.

**Escopo:** este achado é independente do spike de texto-vetorial (achado
anterior) — mesmo se/quando texto comum virar contorno vetorial, este bug
específico de `letterSpacing` no laço de glifos PUA/SMuFL continuaria
existindo e precisaria da mesma correção.

**Varredura de impacto no corpus (pedido do usuário antes de corrigir):**
scan automático dos 34 SVGs (`xml.etree`, todo `<tspan letter-spacing="...">`
seguido de mais texto visível na mesma `<text>`, sem exigir que o conteúdo
seja PUA). Resultado: **o único valor de `letter-spacing` em todo o corpus
é `90px`, e ele aparece uma única vez — exatamente esta ocorrência em Clair
de Lune p4.** Confirmado também que Clair de Lune p1 (segunda pior página,
0,038624%) **não** tem nenhum `letter-spacing` em seu SVG — seu "pp" (antes
de outra frase) é uma dinâmica separada sem esse mecanismo; o residual de
p1 continua classificado como halo puro de AA (terceira investigação,
inalterado). Ou seja: **esta correção específica afeta só Clair de Lune p4
neste corpus** (mas é um bug de código, não do corpus — reapareceria em
qualquer partitura real com o mesmo padrão "dinâmica PUA combinada com
`letterSpacing` seguida de texto comum na mesma `<text>`").

**Correção aplicada e revalidada (2026-09-20).** `verovio/src/bridgedevicecontext.cpp`:
nos dois laços de `DrawText` (SMuFL puro e `allGlyphsAvailable`/PUA), o
`letterSpacing` agora é somado depois de **cada** glifo (movido para depois
do avanço, sem o guard `!first`), igualando ao comportamento do CSS/`resvg`
confirmado na quinta investigação. Revalidação:

- `flutter test` (score_bridge): **66/66 verde**, incluindo o
  widget-vs-harness (R05c, 0 px).
- Varredura completa do corpus refeita (34 páginas, 190s): **só Clair de
  Lune p4 mudou** (as outras 33 páginas deram delta 0 — confirma que a
  correção não tem efeito colateral fora do único caso do corpus que a
  aciona). Clair p4: 3291 → **436 px** (0,052766% → **0,006991%**, agora
  dentro do portão de 99,99%).
- **Corpus inteiro: 26/34 → 27/34 páginas dentro do portão. Média:
  0,010821% → 0,009475% — primeira vez abaixo de 0,01%.** Zero regressões
  (nenhuma página piorou).

Isso satisfaz o critério de aceite 4 de R06b ("repetir até que a média do
corpus fique abaixo de 0,01%") pela média agregada, ainda que 7 páginas
individuais continuem acima de 0,01% — todas já causalmente classificadas
(terceira investigação) como piso de AA Impeller×tiny-skia em texto comum
via `TextPainter`, sem causa corrigível adicional identificada. R06c decide
se a média agregada abaixo do portão, com o residual individual explicado
e sem causa corrigível restante, é suficiente para fechar o passo.

---

Sexta investigação (2026-09-20, pedido do usuário: "Chopin — Étude Op. 10
No. 9 — página 2, bem no topo, tem um problema de posicionamento do número
da página"). Achado: **bug real de agrupamento de âncora de texto**,
independente das duas causas já catalogadas (halo de AA / `letterSpacing`).

**Sintoma medido:** no número de página "– 2 –" (linha `y viewBox 219`,
`text-anchor="middle" x="10000"`), o SVG de referência mostra os dois traços
equidistantes do "2" (gap 10 px de um lado, 11 px do outro; grupo inteiro
centrado em x=1049,5, praticamente o centro da página em 1050); a cena
mostrava os dois traços com gaps assimétricos (15 px × 7 px) e o grupo
inteiro deslocado ~20 px para a direita (centro em 1070). Medido em
`Chopin_Etude_Op10_No9-p2` (recortes `/tmp/etude-p2-{svg,scene}-pagenum.png`,
não versionados).

**Causa raiz:** o SVG emite este número de página como **três `<tspan>`
irmãos sem `x` próprio** dentro de um único `<tspan text-anchor="middle">`
— `"– "` (texto comum), `"2"` (dentro de `<tspan class="num">`, também
texto comum) e `" –"` — que o `resvg`/CSS trata como **um único "text
chunk"**: a âncora centraliza a largura combinada dos três, não cada um
isoladamente (semântica padrão de `text-anchor` em SVG/CSS). No
`View::DrawRunningChildren` (`view_page.cpp:1178`) o Verovio chama
`dc->StartText(x, y, alignment)` **uma vez** para todo o `pgHead`, e
`DrawTextChildren` visita os três nós de texto em sequência, cada um
gerando uma chamada a `DrawText` — exatamente o mesmo padrão de "chunk"
compartilhado que já existe para glifos SMuFL/PUA (`m_textChunkGlyphUses`
+ `FinalizeTextChunk`, A10). O problema é que o ramo de **texto comum**
(`BridgeTextRun`, ramo final de `DrawText` em
`verovio/src/bridgedevicecontext.cpp`) nunca participava desse
agrupamento: cada chamada calculava seu próprio `x0` centralizando **só a
própria largura** (`x0 = origin.x - extend.m_width/2`) e chamava
`AddTextRun` na hora, ignorando `m_textChunkWidth`/`FinalizeTextChunk`.
Do lado do `score_bridge`, `alignment`/`origin` são exportados **sem**
`x0` pré-calculado — `scene_painter.dart:264` centraliza cada run em
runtime usando a própria medida do `TextPainter`
(`SceneTextAlign.center => -painter.width / 2`), pensado para um único run
por âncora (mesmo espírito de "o motor de texto do renderer decide a forma
final", como o `resvg` faz do lado da referência). Com 3 runs por âncora,
cada um se autocentralizava sobre sua própria fatia do texto em vez do
grupo inteiro — daí a assimetria e o deslocamento.

**Correção (passo de origem: exportador,
`verovio/src/bridgedevicecontext.cpp`/`.h`):** o ramo de texto comum de
`DrawText` agora empilha o `BridgeTextRun` pendente em
`m_textChunkTextRuns` (novo membro, paralelo a `m_textChunkGlyphUses`) em
vez de finalizá-lo na hora; `m_textChunkWidth` já acumulava a largura de
cada run (não precisou mudar). `FinalizeTextChunk` ganhou o caso geral: com
mais de uma peça no chunk (vários runs de texto comum e/ou runs misturados
com usos de glifo), aplica **um só** deslocamento — a mesma fórmula já
usada para glifos, com a largura somada do chunk inteiro — em cada
`origin.x` e força `alignment = left` (o `score_bridge` só desenha onde
mandado, sem recentralizar). O caso de **um só** run de texto comum sem
glifos (título, marca de tempo, dinâmica isolada — o caso mais comum, de
longe) continua **sem** essa correção: mantém `origin`/`alignment`
originais para o `score_bridge` centralizar sozinho com a própria medida
do `TextPainter`, que é mais fiel que a estimativa de `GetTextExtent` do
Verovio (por isso o formato foi desenhado assim). A `bbox` exportada
(metadado, não usada para desenhar) passou a ser sempre corrigida pelo
mesmo deslocamento de grupo, single ou multi-run — antes ela só recebia a
centralização local por run, coerente por acidente no caso single-run e
errada no caso multi-run.

**Revalidação:**
- `flutter test` (score_bridge): **66/66 verde**, incluindo o
  widget-vs-harness (R05c, 0 px); `flutter analyze` limpo.
- Página isolada (`compare-page.sh`): "– 2 –" agora com gaps 11×11 (SVG:
  10×11) e centro do grupo em 1049,0 (SVG: 1049,5) — a olho nu, idêntico à
  referência; a mancha de diff que sobra é só 1 pixel no topo do "2",
  ruído de AA. Étude p2: 1892 → **1681 px** (0,030335% → **0,026952%**).
- Varredura completa do corpus refeita (34 páginas, 191s): a correção
  atinge **toda página com número autogerado** ("– N –", páginas 2+ de
  cada peça no corpus), não só o caso relatado — **10 páginas melhoraram**,
  **zero regrediram**: Étude p2 −211px, p3 347→**130** (−62%), p4
  419→**182** (−57%); Mazurka p2 552→**341** (−38%), p3 278→**61** (−78%);
  Grieg Butterfly p2 301→**90** (−70%), p3 247→**30** (−88%); Grieg
  Little Bird p2 267→**56** (−79%); Scarlatti p2 259→**48** (−81%), p3
  273→**56** (−79%). As demais 24 páginas (inclusive Nocturne, Clair de
  Lune, Satie, Maple Leaf Rag e Prelude — cujo número de página não usa
  esta composição de 3 `<tspan>`) deram delta 0 nos PNGs.
- **Corpus inteiro: média 0,009475% → 0,008456%.** Continuam 7/34 páginas
  acima de 0,01% — exatamente o mesmo conjunto da terceira investigação
  (Clair p1, Étude p1, Satie p1, Étude p2, Nocturne p3/p4, Mazurka p1),
  nenhuma delas tocada por este bug (são página 1 — sem número de página —
  ou dominadas pelo piso de AA já catalogado); nenhuma página cruzou o
  portão para cima ou para baixo por causa desta correção.

Diferente das investigações anteriores (halo de AA = ruído sem correção;
`letterSpacing` = bug isolado em 1 página), esta é uma categoria nova no
catálogo do passo: **agrupamento de âncora multi-run em texto comum**,
generalizável a qualquer composição futura de "texto comum + texto comum"
ou "texto comum + glifo" sob a mesma âncora (não só números de página).

---

**Passo concluído (2026-09-20).** Conferência final dos 5 critérios de
aceite, com os números da sexta investigação (últimos medidos):

1. **Toda página acima de 0,01% tem causa registrada** — as 7 páginas
   restantes (Clair p1, Étude p1, Satie p1, Étude p2, Nocturne p3/p4,
   Mazurka p1) estão 100% classificadas como piso de AA do `TextPainter`
   em texto comum (quarta investigação), com o spike de contorno vetorial
   (mesma seção) provando que a causa é a rota de desenho, não um bug
   corrigível sem mudança de arquitetura. Nenhuma delas cruzada por
   `letterSpacing` (quinta) ou agrupamento de âncora (sexta).
2. **Toda correção cita o passo de origem e foi revalidada** — as três
   correções de código (S05: `stroke:none` em preenchimento puro;
   `bridgedevicecontext.cpp`: `letterSpacing` pós-glifo; idem: agrupamento
   de âncora multi-run) foram revalidadas por `flutter test` 66/66
   (incluindo widget-vs-harness R05c em 0 px) e `flutter analyze` limpo
   antes de cada remedição.
3. **Varredura refeita após a última correção** — sexta investigação,
   34 páginas, 191 s, CSV substituído.
4. **Recortes de exemplo por categoria guardados** — `r06b-hands-*` (mãos
   PUA, causa encerrada), `r06b-edge-*`/`r06b-dim-*` (halo de AA),
   `Clair_de_Lune__Debussy-p4-{svg,scene}.png` (`letterSpacing`),
   `/tmp/etude-p2-{svg,scene}-pagenum.png` (âncora multi-run, não
   versionado — refazer se R06c precisar do PNG).
5. **Média do corpus: 0,008456% < 0,01%** (critério satisfeito pela
   primeira cláusula, não pela cláusula de exceção) — **27/34 páginas**
   dentro do portão de 0,01%; das 7 restantes, a pior é Étude p1 em
   **0,031698%**, bem abaixo do teto de 0,05% que R06c vai conferir.

Todos os 5 critérios atendidos. Próximo passo: **R06c** (relatório de
paridade + mesa de prova, o portão da fase A) — vai precisar refazer a
varredura do corpus (`compare/out/corpus/` está git-ignorado e não
persiste entre sessões) para gerar o CSV e as imagens que o relatório
cita.
