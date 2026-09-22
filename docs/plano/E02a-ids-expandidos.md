# E02a — Ids expandidos (`-rendN`) chegam à nota desenhada

**Depende de:** E01b (e D-EXPMAP resolvida) · **Decisão necessária:** não

## Objetivo

Na segunda passagem de uma repetição, **a nota acende**. Hoje o timemap manda
`abc-rend2`, o `ScoreController` não acha esse id na cena e ignora em
silêncio, e a partitura fica apagada durante toda a repetição (na Gymnopédie,
de 92 368 ms a 165 789 ms, ou seja, 73 s sem destaque).

A regra do projeto é "identificadores = os `xml:id` do timemap". Então quem
recebe id do host aceita também o id expandido e o leva ao nó da cena. Não é
só o player: o host pode acender a nota vinda do próprio timemap ou do MIDI,
que usa os mesmos ids.

## Ler antes (só isto)

- `score_bridge/lib/src/score_controller.dart` (`_known`, L122, e todo método
  público que recebe `id`).
- `score_bridge/lib/src/segmentation.dart`: `animatableIdsFromTimemap` (L163).
- `score_bridge/lib/src/hit_test.dart`: `ScoreGeometry.elementOf` (L122),
  `pageOf` (L125), `rectForId` (L133).
- `score_bridge/lib/src/score_view.dart`: `ScoreViewController.scrollToId`
  (L197/L686).
- `score_bridge/lib/src/model.dart`: `VsbDocument`, `ScenePage.byId` (L259).
- A especificação §2 atualizada em E01b (a regra dos ids expandidos).

## Contexto que você precisa (não vá procurar, está aqui)

- **Regra (se D-EXPMAP = (a)):** um id que existe na cena é ele mesmo. Se não
  existe e casa com `^(.*)-rend([0-9]+)$`, com a base existindo na cena, ele é
  a base, na passagem `N`. Caso contrário não é da cena. **Nunca** tire o
  sufixo de um id que existe na cena: se o host gerar a partitura com a
  expansão desenhada (`--expand-always`), os clones `-rend2` estarão na cena
  e são nós próprios.
- Verificação feita em 2026-09-21: 0 divergências entre a regra e o
  `-t expansionmap` em 2 933 ids (Gymnopédie + Maple Leaf Rag,
  `--xml-id-seed 42`). Se a execução for num processo só, pelo binding, use
  `Toolkit::GetNotatedIdForElement`, exposto no wrapper C como
  `vrvToolkit_getNotatedIdForElement`.
- Nas 10 peças, **toda** base de `-rend2` também aparece no timemap sem
  sufixo (S04: "0 ids-base ausentes"). Por isso, no corpus, o conjunto de
  nós dinâmicos de A01a não muda. Mas uma expansão que pula o original (um
  `<expansion>` MEI sem a casa 1, por exemplo) deixaria a base só como
  `-rend2`. `animatableIdsFromTimemap` tem que resolver, senão a base vira
  estática, é assada no `Picture` e não muda de cor nunca.
- `HighlightEngine.start` **substitui** o destaque em curso do id
  (`highlight_engine.dart` L154), e `ScorePlayer._apply` aplica os `off`
  antes dos `on` da mesma entrada (`score_player.dart` L193). Numa repetição
  de um compasso só (E01a r13), a mesma nota notada recebe, no mesmo
  instante, o `off` da passagem 1 e o `on` da passagem 2. Com os ids
  resolvidos antes, isso vira `release(x)` e `highlight(x)`, e a nota
  reacende. É isso que se quer.
- O estado do controller (cor fixa, destaque, halo) é por **id da cena**.
  `setColor('x-rend2', …)` pinta `x` nas duas passagens, porque é o mesmo
  desenho. Documente.

## O que fazer

1. Em `VsbDocument` (ou num arquivo novo `expansion.dart`, exportado pela API
   pública):

   ```dart
   /// Id do nó da cena que [id] representa (ele mesmo, ou a base de um
   /// `-rend<N>`), ou `null`.
   String? sceneIdOf(String id);

   /// A execução que [id] representa: N de `-rend<N>`; 1 para id da cena.
   int passOf(String id);
   ```

   Com memo (o timemap tem até ~2 500 ids distintos por peça).
2. Passe por `sceneIdOf` em todos os pontos de entrada de id:
   - todos os métodos públicos do `ScoreController`;
   - `animatableIdsFromTimemap`;
   - `ScoreGeometry.elementOf`, `pageOf` e `rectForId`;
   - `ScoreViewController.scrollToId`;
   - `overlayIds` do `ScorePageView`/`ScoreView`.

   Para achar os demais: `graft callers _known --depth 2` e
   `graft grep "String id"` em `score_bridge/lib`. Hit-test (`idAt`)
   continua devolvendo o id da cena.
3. Atualize os comentários que dizem que `-rend2` é ignorado (há pelo menos
   5: `score_controller.dart` L20, `segmentation.dart` L177,
   `score_view.dart` L195, `hit_test.dart` L121, `score_timeline.dart` L12).

## Fora de escopo

- Sequência de compassos e página durante a repetição (E02b).
- Escolher a passagem num toque (E02c).

## Critérios de aceite

1. Teste unitário da resolução: `x` na cena → `x`, passagem 1; `x-rend2` com
   `x` na cena → `x`, passagem 2; `x-rend3` → `x`, passagem 3; `x-rend2`
   **presente** na cena → ele mesmo; `nao-existe-rend2` → `null`;
   `abc-rendezvous` → `null`.
2. A regra concorda com o Verovio em **todo** id de timemap das 10 peças e das
   13 partituras de E01a (script em `compare/scripts/`, `-t expansionmap` e
   `-t timemap` com o mesmo `--xml-id-seed`): 0 divergências.
3. Gymnopédie com `ScorePlayer` (`release: 0`): em 20 instantes sorteados
   entre 92 368 e 165 789 ms, o conjunto `controller.highlightedIds` é igual
   ao dos ids ativos no timemap naquele instante, resolvidos, e **não
   vazio**. Hoje é vazio.
4. r13 (repetição de um compasso): um quadro depois do salto, a nota repetida
   está na cor de destaque, e não em `release`.
5. O conjunto de nós dinâmicos por página (A01a) é **idêntico** ao de antes
   nas 10 peças. Um teste sintético com timemap que só traz `x-rend2` torna
   `x` dinâmico.
6. `ScoreGeometry.rectForId('x-rend2') == rectForId('x')` e
   `scrollToId('x-rend2')` rola até `x`.
7. O teste existente com `nao-existe-rend2` continua passando.
   `flutter analyze` limpo, `flutter test` verde.

## Notas de execução

_(preencher ao executar)_
