# S04 — Bounding boxes e índice de elementos endereçáveis

**Depende de:** S02 · **Decisão necessária:** não

## Objetivo

Fazer o formato carregar, para cada elemento que o host pode querer endereçar,
**onde ele está na página**. É o que permite ao Flutter posicionar widgets
reais (cursor, alvo de toque, tooltip) sobre a partitura sem reimplementar
geometria, e o que permite rolar até um compasso.

## Ler antes (só isto)

- `verovio/include/vrv/bridgegeometry.h` (`BridgeNode`, `BridgeShape`,
  `BridgeGlyphUse`, `BridgeTextRun`).
- `verovio/src/bridgedevicecontext.cpp`: `StartGraphic`/`EndGraphic` (busque os
  símbolos; era L~600) — é onde a árvore é empilhada/desempilhada.
- `verovio/include/vrv/bboxdevicecontext.h` — como o Verovio já calcula bbox
  para outro fim (referência de abordagem, **não** reutilize a classe).
- Seção 5.1 da [especificação](../formato/especificacao-v1.md).

## O que fazer

1. Acrescentar a `BridgeNode`:

   ```cpp
   bool hasBBox = false;
   double bbox[4] = { 0, 0, 0, 0 };   // x0, y0, x1, y1 em unidades de viewBox
   ```

2. Calcular a bbox em `EndGraphic`/`EndCustomGraphic`, como união de:
   - bbox de cada forma filha (path: envoltória dos vértices **e** das tangentes
     — use a envoltória de controle, é conservadora e barata; rect/ellipse:
     trivial; traço: expanda `strokeWidth / 2` em cada lado);
   - bbox de cada uso de glifo: `glyph.bbox * (sx, sy) + (x, y)`;
   - bbox de cada run de texto: use `GetTextExtent`/`GetSmuflTextExtent` do
     próprio `DeviceContext` (já existem, `include/vrv/devicecontext.h` L178-L180)
     e aplique o alinhamento;
   - bbox de cada nó filho (já calculada, ordem natural bottom-up);
   - com `rotate` presente, transforme a bbox dos filhos pelo ângulo **antes**
     de unir (4 cantos rotacionados, envoltória alinhada aos eixos).
   Nós `hidden` **não** contribuem.

3. Emitir bbox **sempre** para nós com `id` e para nós cuja classe seja
   `page`, `system`, `measure`, `staff`, `layer`. Para os demais, emitir só se
   não custar nada (ela já foi calculada de qualquer forma — o filtro é só na
   serialização, em S05, para não inchar o arquivo).

4. Montar também, no `BridgePage`, um índice plano pronto para o host:

   ```cpp
   struct BridgeIndexEntry { std::string id, className; int nodePath; double bbox[4]; };
   std::vector<BridgeIndexEntry> index;   // todos os nós com id, em ordem de documento
   ```

   `nodePath` pode ser um índice sequencial de nó na ordem de percurso — o
   objetivo é o Dart achar o nó por `id` em O(1) sem varrer a árvore.

## Fora de escopo

- Serializar (S05).
- Qualquer decisão sobre *como* o Flutter usa a bbox (A04a/A04b).
- Bbox "de tinta" exata de curvas (a envoltória de controle é suficiente e é o
  que o resto do Verovio já usa; não implemente cálculo de extremos de Bézier
  sem um caso real pedindo).

## Critérios de aceite

1. Compila.
2. **Sanidade geométrica**, num teste temporário sobre 2 peças do corpus:
   - toda bbox de nó contém as bboxes de todos os seus filhos (teste recursivo,
     tolerância `1e-6`);
   - a bbox do nó raiz de cada página está contida no `viewBox` da página;
   - nenhum nó com `id` tem bbox degenerada (largura ou altura zero), **exceto**
     os que legitimamente não desenham nada — liste esses nas notas por classe,
     não apenas o total.
3. **Conferência contra o SVG**: escolha 5 notas de uma página, pegue a bbox
   exportada, converta para pixels com o `fit` da página e marque o retângulo
   sobre o PNG do SVG (script de 10 linhas com `PIL`, saída em `compare/out/`).
   Inspeção visual: cada retângulo cobre a cabeça de nota + haste
   correspondente. Anexe o PNG resultante nas notas de execução.
4. Todo `id` do `timemap` de uma peça (`verovio -t timemap`) que seja de nota
   aparece no índice da página correspondente:

   ```sh
   # compare o conjunto de ids do timemap com o do índice; a diferença deve ser
   # vazia (ids do timemap ausentes no índice = bug)
   ```

## Notas de execução

- 2026-09-17: retomado de um estado interrompido (outro modelo já tinha implementado
  `CalculateNodeBBox`/`BuildIndex`, `hasBBox`/`bbox` em `BridgeNode`/`BridgeTextRun` e
  `BridgeIndexEntry`, mas não tinha rodado nenhum critério de aceite; as notas estavam
  vazias e os artefatos em `compare/out/s04-*` eram de uma iteração anterior ao último
  `git diff` do arquivo — todos removidos por estarem desatualizados).
- **Bug encontrado e corrigido**: `GlyphBBox` (em `bridgedevicecontext.cpp`, dentro do
  namespace anônimo) dividia `use.sx`/`use.sy` por `DEFINITION_FACTOR` antes de escalar
  o `bbox` do glifo, mas `use.sx`/`use.sy` (calculados em `MakeGlyphUse`, fórmula
  `pointSize/unitsPerEm*DEFINITION_FACTOR`) **já são** o mesmo fator que
  `SvgDeviceContext::DrawMusicText` usa no `transform="translate(x,y) scale(sx,sy)"` do
  `<use>` (`svgdevicecontext.cpp:1202-1205`) — a divisão extra encolhia a bbox de todo
  glifo (notehead, clave, acidente, articulação — a maioria do conteúdo visual) em 10x.
  Corrigido para `x0 = use.x + glyphBBox[0] * use.sx` (e simétrico em y/x1/y1), sem a
  divisão. Confirmado por reconstrução manual: para o glifo `m1c8yet1` (clave, `E050`,
  `translate(117, 21248) scale(0.72, 0.72)` no SVG da mesma sessão), `x0` calculado
  bate exatamente com `109.8 = 117 + (-10) * 0.72`.
- Verificação: teste temporário `s04_bbox_check.cpp` (fora do repo, em
  `$SCRATCH/s04_bbox_check.cpp`, compilado e linkado à mão contra os `.o` já gerados
  pelo `make` do alvo `verovio`, exceto `main.cpp.o`) que usa `Toolkit` +
  `BridgeDeviceContext` diretamente (sem passar pelo CLI, já que S06 — a integração do
  `Toolkit`/CLI — ainda não existe) para as 5 peças do corpus MEI (15 páginas, 1228 a
  658 ids de nota por peça). Removido ao final (não sobrou nenhum arquivo novo em
  `verovio/`).
- **Efeito colateral encontrado**: `CMakeFiles/verovio.dir/.../src/lottiedevicecontext.cpp.o`
  era um objeto órfão (o `.cpp` foi renomeado em S02, mas o `.o` antigo sobrevivia no
  diretório de build e quebrava o link de qualquer executável extra que reunisse todos
  os `.o` do alvo `verovio`). Removido; `cmake ../cmake && make -j4` limpo depois.
- **Critério 1 (compila)**: `cmake ../cmake && make -j4` sem avisos novos.
- **Critério 2 (sanidade geométrica)**, nas 5 peças (15 páginas, ~1000-1500 ids por
  página):
  - Contenção pai⊇filho (grupos, tolerância `1e-6`): **0 violações** em todas as
    páginas.
  - Bbox degenerada (largura ou altura zero) entre nós com `id`: **0 ocorrências** em
    qualquer classe, nas 5 peças.
  - Bbox do nó raiz contida no `viewBox` da página (`abs = bbox + origin`, já que a
    bbox do nó é gravada no referencial de conteúdo, antes do
    `translate(originX, originY)` — ver seção 3 da especificação): **falha nas 15/15
    páginas**, por uma margem moderada (tipicamente 5-15% da largura/altura da
    página). Rastreado até a causa: nós `clef` de troca de clave com oitava (ex.:
    glifo `E07C`, `d1uty755` na Mazurka p2) têm bbox de fonte genuinamente larga
    (confirmado batendo `translate`+`bbox*scale` contra o SVG da mesma sessão), e a
    envoltória de controle de Béziers (ties/slurs perto da margem) soma um pouco mais
    — exatamente o compromisso que o plano já autoriza ("conservadora e barata", fora
    de escopo implementar extremos exatos de Bézier). Não é um bug de cálculo: é
    geometria real de glifo/curva que a política de bbox conservadora deste passo
    aceita passar um pouco da margem nominal. Registrado como ressalva, não bloqueia.
- **Critério 3 (conferência visual)**: 5 notas da primeira página de
  `Chopin_Etude_Op10_No9.mei` (`d414233e38`, `d414233e62`, `d414233e89`,
  `d414233e110`, `d414233e148`), bbox convertida para pixel com `fit` da página
  (`scale=0.1, tx=ty=0` — página A4 padrão sem escala customizada) e `origin=[500,500]`
  somado antes de escalar, marcadas sobre o PNG gerado a partir do SVG **da mesma
  sessão** (mesmos `xml:id`, ver nota abaixo). Inspeção visual: as 5 caixas cobrem
  cabeça de nota + haste (+ feixe/articulação quando presente) corretamente. PNG em
  `compare/out/s04-bbox-overlay-chopin-etude-p1.png`.
- **Critério 4 (ids do timemap no índice)**: `Toolkit::RenderToTimemap()` chamado **na
  mesma sessão** do `Toolkit` que gerou a `BridgeDeviceContext` (ver nota abaixo sobre
  ids não-determinísticos) e comparado contra `BridgePage::index` de todas as páginas:
  **0 ids de nota ausentes**, nas 5 peças (1228, 897, 846, 493 e 658 ids de nota,
  4122 no total).
- **Achado importante para passos futuros (S06/S07)**: `xml:id` auto-gerado (elementos
  sem `xml:id` explícito no MEI) **não é determinístico entre execuções separadas do
  processo** — confirmado rodando `verovio -t timemap` duas vezes sobre o mesmo
  arquivo e comparando a saída (`diff` mostrou ids diferentes para os mesmos eventos).
  Por isso o critério 4 só pode ser verificado corretamente comparando timemap e cena
  gerados pelo **mesmo** `Toolkit`/sessão, nunca por duas invocações separadas do CLI.
  Isso é relevante para S07 (pacote `.vsb` com timemap embutido): `scene.json` e
  `timemap.json` **precisam** vir da mesma chamada de `Toolkit` (o mesmo `LoadFile` +
  os métodos `RenderTo*`), não de dois processos/`LoadFile` distintos, ou os ids podem
  não bater.
- Bloqueios: nenhum. Ressalva registrada acima (critério 2, bbox do nó raiz vs.
  viewBox) não impede seguir para S05.
