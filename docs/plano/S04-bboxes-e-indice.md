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
- Qualquer decisão sobre *como* o Flutter usa a bbox (A04).
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

(a preencher por quem executar)
