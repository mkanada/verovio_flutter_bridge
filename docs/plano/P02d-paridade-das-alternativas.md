# P02d — Referência SVG e paridade das páginas alternativas

**Depende de:** P02c, P03a (o `compare` lê o `.vsb` pelo `score_bridge`) ·
**Decisão necessária:** não

## Objetivo

Provar que cada página alternativa desenhada pelo Flutter bate com o SVG do
Verovio da **mesma** seleção em mais de 99,99% dos pixels. É o requisito
inegociável 1 do `CLAUDE.md`, agora para as páginas novas.

## Ler antes (só isto)

- `compare/scripts/compare-page.sh` e `compare/scripts/compare-corpus.sh`.
- `compare/lib/main.dart` (comando `scene-to-png`, `--page N`).
- `verovio/tools/main.cpp` (tratamento de opções longas e o ramo `svg`).

## Contexto que você precisa (não vá procurar, está aqui)

- A CLI do Verovio não tem como pedir uma seleção. Para gerar a referência,
  acrescente **na CLI** (só `tools/main.cpp`, nada em `View`/DCs) uma opção
  `--select-from <measure-id>` que, depois de carregar, chama
  `Select({"start": id, "end": <último compasso>})` + `RedoLayout()`. Com
  ela, `-t svg -a` gera as páginas da sequência. **Tem que ser o mesmo
  caminho** que o exportador usa em P02c: se o C++ de P02c tiver um helper,
  reuse-o.
- A referência usa as mesmas opções do `.vsb` (P01c): `--header none
  --footer none --no-instrument-labels`.
- `scene-to-png` desenha `scene.pages[N]`. Acrescente
  `--alternate <start-id>` (ou `--alternate-index K`) para desenhar
  `alternates.sequences[K].pages[N]`. O `compare` lê o `.vsb` pelo
  `score_bridge` (`compare/lib/src/scene_to_png.dart`), e por isso este passo
  vem depois de P03a: use `VsbDocument.alternates` e o `PageRef` de lá.

## O que fazer

1. `--select-from` na CLI (documentado no `-h`).
2. `scene-to-png --alternate ...`.
3. `compare-page.sh`/`compare-corpus.sh`: um modo que, além das páginas
   normais, varre todas as páginas de todas as sequências alternativas de
   cada peça (nomes de saída `<peça>-alt<K>-p<N>-*.png`).
4. Rode a varredura inteira e registre em `docs/relatorio-paridade.md`
   (seção nova, datada).

## Fora de escopo

- Corrigir divergências de desenho que não sejam específicas das
  alternativas (se aparecerem, registre e pare).

## Critérios de aceite

1. Todas as páginas alternativas do corpus acima de **99,99%** (tolerância
   128/255). Tabela por página nas notas.
2. A média das alternativas é comparável à das páginas normais de P01c. Uma
   página acima de 0,01% de divergência precisa de explicação com imagem de
   diff.
3. `-t svg` sem `--select-from`: byte-idêntico ao de antes do passo.
4. Build sem avisos novos; `flutter analyze` limpo em `compare/`.

## Notas de execução

**`--select-from` (item 1).** Implementado como opção genérica registrada
(`OptionString m_selectFrom`, `options.h`/`.cpp`, grupo geral), não como
flag ad-hoc de `getopt` — primeira tentativa foi um `getopt_long` manual
(entrada em `baseOptions` + `case` próprio, como `--stdin`/`'z'`), mas
registrar como `vrv::Option` de verdade dá dois benefícios de graça: aparece
documentado em `-h general` (item explícito do passo) e evita uma entrada
de long-option duplicada (a lista genérica de `main.cpp` já registra
**todo** `vrv::Option` automaticamente — uma entrada manual para o mesmo
nome longo colidiria). Lido via `options->m_selectFrom.IsSet()` logo depois
do `LoadFile`/`LoadData`, antes de qualquer render.

**Mesmo caminho do exportador (item 1, "reuse-o").** `Toolkit::
SelectFromMeasureToEnd(measureId)` (novo método público, `toolkit.h`/`.cpp`)
extrai exatamente a lógica que P02c já tinha inline em
`RenderAlternatesToBridge` (achar o último compasso, montar o JSON de
seleção, `Select`+`RedoLayout`, `HasSelection()` como sinal de sucesso) —
refatorado para os dois chamarem o mesmo método, não duas cópias
parecidas. `RenderAlternatesToBridge` ficou mais curto e a CLI ganha a
garantia de "é o mesmo mecanismo" por construção, não por revisão manual.

**`scene-to-png --alternate` (item 2).** `sceneToPng` ganhou
`alternateStart` opcional: quando dado, lê `doc.alternateStartingAt(id)`
(P03a) em vez de `doc.pages`; `--page` continua 1-based, agora dentro da
sequência. `compare/lib/main.dart` expõe `--alternate <start-id>` no
comando.

**`compare-page.sh --alternate` / `compare-corpus.sh SWEEP_ALTERNATES=1`
(item 3).** Achado ao testar manualmente: sem uma semente fixa de
`xml:id`, o `--alternate <id>` do chamador nunca bate com o `.vsb` que o
próprio script gera internamente (cada `verovio` sorteia uma sequência de
ids diferente sem `--xml-id-seed`) — o `.vsb`/SVG de referência das páginas
**normais** nunca precisou de semente (a comparação é só de pixel, nunca
por id), mas o modo `--alternate` depende de casar o mesmo `xml:id` entre
duas chamadas separadas ao `verovio`. Corrigido com `--xml-id-seed 42`
fixo (a mesma semente do resto do projeto, `check-suffix-rule.py`) só
nesse modo. `compare-corpus.sh` ganhou uma segunda passada opcional
(`SWEEP_ALTERNATES=1`) que sonda `alternates.json` de cada peça (mesma
semente) e chama `compare-page.sh --alternate` para cada página de cada
sequência, num CSV à parte (`resultado-alternates.csv`) — não entra no
`resultado.csv` nem no total de 34 páginas do gate de R06a, que continua
medindo só as páginas normais.

**Critério 1** (todas as páginas alternativas do corpus acima de 99,99%).
`CORPUS_DIR=compare/out/p02d SWEEP_ALTERNATES=1 compare-corpus.sh 128`:
18/18 páginas alternativas (as 4 peças com pontos de chegada que sobrevivem
à regra de existência de §2.5 — Gymnopédie 1, Maple Leaf Rag 13 em 8
sequências, Mazurka 2, Little bird 2), sem nenhuma falha. Tabela completa
em `docs/relatorio-paridade.md`, seção "Atualização de 2026-09-22 — P02d".

**Critério 2** (média comparável às páginas normais de P01c). 0,006514%
(alternativas) vs. 0,006402% (normais de P01c) — praticamente igual;
14/18 (78%) ≤ 0,01% vs. 27/34 (79%) nas normais; máximo 0,021789%, bem
abaixo do teto de 0,05%. Nenhuma página precisou de investigação de
imagem de diff (nenhuma acima de 0,01% chegou perto do teto).

**Critério 3** (`-t svg` sem `--select-from` byte-idêntico a antes do
passo). `git stash` dos 5 arquivos tocados
(`options.h`/`toolkit.h`/`options.cpp`/`toolkit.cpp`/`main.cpp`),
recompilado, `-t svg -a` no Chopin Étude (4 páginas, `-x 42`) antes/depois:
0 diferenças.

**Critério 4**: build sem avisos novos (duas recompilações completas, por
mudar `options.h`); `flutter analyze` limpo em `compare/` (0 avisos).
