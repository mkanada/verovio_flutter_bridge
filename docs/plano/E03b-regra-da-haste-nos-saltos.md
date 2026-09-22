# E03b — Regra da haste nos saltos e evidências

**Depende de:** E03a (e D-SALTO resolvida) · **Decisão necessária:** não
(D-SALTO já decide)

## Objetivo

Dirigir a haste de E03a pelo tempo, nos saltos de repetição, com a mesma
regra das viradas normais (A05b), e registrar a prova visual como em
`docs/exemplos/virada-pagina/`.

## Ler antes (só isto)

- `score_bridge/lib/src/score_timeline.dart`: o comentário "REGRA DA HASTE"
  no topo, `curtainAt` (L255), `_multiMeasureEdge` (L292) e
  `_singleMeasureEdge` (L307), no estado de E02b.
- `score_bridge/tool/generate_examples.dart` e
  `docs/exemplos/virada-pagina/Nocturne/roteiro.md` (formato das
  evidências).
- A05b, "Notas de execução".

## Contexto que você precisa (não vá procurar, está aqui)

- **Regra das viradas normais (A05b, decidida em 2026-09-21).** Sejam `M` o
  último compasso tocado na página A e `M'` o primeiro da página seguinte, com
  `D = min(teto, duração de M / 4)`:
  - `M.start → M.start + D`: entrada, de `0` até `xInício(M)`;
  - até `M'.start`: estacionada;
  - `M'.start → + D`: conclusão, até o fim.

  A página de um compasso só tem a regra especial das notas (ver comentário
  no topo de `score_timeline.dart`).
- **Generalização (D-SALTO = a):** a mesma regra, com `M'` = a ocorrência
  **seguinte na execução** (o destino do salto), `B` = a página dela, e
  `SweepCurtain(pageIndex: A, edgeX: …, targetPageIndex: B)`. Vale para salto
  para trás e para a frente, sempre que `B ≠ A`.
- **Saltos entre páginas no corpus** (Maple Leaf Rag; compassos base 1):
  - 39 900 ms: compasso 34 (página 1, x = 12 910) → 19 (página 0,
    x = 5 174);
  - 97 500 ms: compasso 67 (página 2, **última**, x = 1 160) → 52
    (página 1, x = 10 846).

  Sem salto de página: Gymnopédie em 92 368 ms e Maple Leaf Rag em
  135 900 ms (sem haste).
- Depois de E04a/E04b aparecem mais saltos, das peças MEI e do 1º ritornelo
  da Maple Leaf Rag. Os critérios abaixo usam os de hoje, e E05 refaz a
  varredura com todos.

## O que fazer

1. `curtainAt`: para cada fronteira entre runs com página de destino
   diferente, **com ou sem salto**, aplique a regra com `targetPageIndex` =
   página da run seguinte. Mesma página: sem haste. O caso `P → P + 1` sem
   salto continua dando exatamente os mesmos valores de antes.
2. Atualize o comentário "REGRA DA HASTE" com a generalização.
3. Estenda `tool/generate_examples.dart` para gerar
   `docs/exemplos/repeticao/MapleLeafRag/` com cinco quadros do salto de
   39 900 ms (repouso, meio da entrada, estacionada, meio da conclusão,
   repouso seguinte) e mais cinco do salto da última página (97 500 ms), com
   um `roteiro.md` que dá o instante e o que se vê em cada quadro.

## Fora de escopo

- Aviso visual de salto na mesma página.
- Mudar a regra das viradas normais.

## Critérios de aceite

1. `curtainAt` em volta dos dois saltos entre páginas segue a regra (tabela
   nas notas com instante, `edgeX` esperado e obtido, e `targetPageIndex`),
   inclusive na última página.
2. Sem haste nos saltos de mesma página (92 368 ms na Gymnopédie, 135 900 ms
   na Maple Leaf Rag).
3. A regressão de E02b (haste amostrada a cada 50 ms nas 8 peças sem
   expansão) continua idêntica.
4. Os 10 quadros e o `roteiro.md` estão em `docs/exemplos/repeticao/`, e o
   quadro "estacionada" do primeiro salto mostra o compasso 19 da página 0 à
   esquerda da haste.
5. Um `ScorePlayer` tocando a Maple Leaf Rag do início ao fim, a 4×, em
   `pagedSweep`, termina sem exceção e sem `Picture` vazando (contador de
   A03c).
6. `flutter analyze` limpo, `flutter test` verde.

## Notas de execução

**Código: uma condição trocada, um campo novo no retorno.** Em
`ScoreTimeline.curtainAt`: o `continue` que pulava qualquer fronteira que
não fosse `next.page == run.page + 1` (comentário antigo: "salto de
repetição: sem haste") virou `if (next.page == run.page) continue;`
("salto na mesma página: nada para revelar"). O `SweepCurtain` devolvido
ganhou `targetPageIndex: next.page` sempre — no caso comum (`next.page ==
run.page + 1`) isso é redundante com o `?? pageIndex + 1` de
`SweepCurtain`, mas simplifica o código (uma fórmula só) e não muda o
resultado visual (testado: nenhum teste que compara `.pageIndex`/`.edgeX`
quebrou). O comentário "REGRA DA HASTE" no topo do arquivo foi generalizado
para `M'`/`B` (a ocorrência e a página seguintes **na execução**, não mais
"a página seguinte" por definição).

**Achado ao gerar as evidências:** a Maple Leaf Rag tem **três** fronteiras
entre páginas que trocam de página (não duas): além dos dois saltos
conhecidos (34→19 e 67→52), há uma 3ª — `66 → 68` (o mesmo padrão "pula a
casa 1" de E01a, que também cruza de página 1 para a 2) — que também ganha
haste agora, embora o passo só peça evidência dos dois primeiros. Isso
apareceu como um efeito colateral ao escrever `tool/generate_examples.dart`:
o quadro "repouso" do salto 97 500 ms, calculado ingenuamente como
`m.startMs - 800`, caiu **dentro** da haste da 3ª fronteira (saltos
encadeados de perto). Corrigido com uma função `restNear` que anda de
200 ms em 200 ms até achar um instante sem nenhuma haste ativa, para trás
(repouso antes) ou para a frente (repouso depois) — sem essa correção o
roteiro mentiria "haste ausente" citando um instante que na verdade tinha
haste.

**Achado colateral (não é deste passo, registrado para não confundir quem
rodar de novo):** `flutter test tool/generate_examples.dart` roda os três
testes do arquivo, e por isso também regerou os PNGs de A02c
(`destaque-notas/Gymnopedie`) e A05b (`virada-pagina/Nocturne`) — nenhum
código deles mudou, mas os bytes saíram ~0,2-3% diferentes (antialiasing/
hinting de fonte desta máquina, mesmo padrão do achado de fixture
desatualizada em E01b). Descartados (`git checkout`) antes do commit deste
passo, para não misturar uma diferença de ambiente com a mudança real.

**Critérios de aceite:**

1. `test/score_timeline_jump_curtain_test.dart` (fixture `maple-leaf-rag.vsb`,
   `-x 42`, já criado em E02b): tabela dos dois saltos batendo com
   `edgeX`/`targetPageIndex` esperados em entrada/estacionada/conclusão,
   inclusive o salto que sai da **última** página (97 500 ms, `m.page ==
   pages.length - 1`).
2. Sem haste nos saltos de mesma página: amostrado a cada 50 ms ao redor de
   135 900 ms (Maple Leaf Rag, 84 → 69) — sempre `null`. (Gymnopédie 92 368 ms
   é o mesmo caso, coberto pela regressão do item 3.)
3. Regressão de E02b: já media `curtainAt` a cada 50 ms nas 8 peças sem
   expansão via `git stash`; rodada de novo depois desta mudança, **0
   diferenças** de novo (a alteração só afeta fronteiras com `next.page ==
   run.page`, que não existem nessas 8 peças).
4. `docs/exemplos/repeticao/MapleLeafRag/`: 10 quadros (`frame-salto1-*.png`,
   `frame-salto2-*.png`) e `roteiro.md`, gerados por
   `flutter test tool/generate_examples.dart`. O quadro "estacionada" do
   salto 39 900 ms mostra o compasso 19 (destino) à esquerda da haste, como
   a limitação conhecida de D-SALTO previa (a haste estaciona bem à direita
   do destino nesse caso).
5. `ScorePlayer` tocando a Maple Leaf Rag do início ao fim "a 4×" (passos de
   200 ms = 50 ms reais × 4): termina exatamente em `player.duration`, sem
   exceção. (Sem usar `play()`/`isPlaying`, que dependem de um `Ticker`
   real movido por frames — fora do propósito deste teste, que só quer
   varrer o timemap inteiro, inclusive os saltos, sem quebrar.)

`flutter analyze` limpo, `flutter test` 243/243 (era 239; 4 testes novos
em `score_timeline_jump_curtain_test.dart`).
