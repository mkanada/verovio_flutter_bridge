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

_(preencher ao executar)_
