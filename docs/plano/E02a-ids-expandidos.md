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

**Código novo.** `score_bridge/lib/src/expansion.dart`: `IdExpansion`
(regra do sufixo, memoizada) — exportado pela API pública
(`score_bridge.dart`). `VsbDocument` ganha `sceneIdOf`/`passOf`, que
delegam para uma `IdExpansion` construída (`late final`, uma vez) a partir
de `{for (final page in pages) ...page.byId.keys}`.

**Pontos de entrada resolvidos:**

- `ScoreController`: `setColor`, `setColors`, `clearColor`, `highlightAll`
  (e portanto `highlight`), `release`, `isHighlighted`, `colorOf` — todos
  via um `_resolve(id)` privado no topo do método. `highlightedIds`/
  `colors`/`haloColors` não precisaram mudar: como só ids resolvidos entram
  no motor, eles já saem resolvidos.
- `ScoreGeometry.elementOf` (`hit_test.dart`) resolve com
  `document.sceneIdOf(id) ?? id`; `pageOf` e `rectForId` passaram a chamar
  `elementOf` em vez de indexar `_byId` direto, então ganham a resolução de
  graça. `idAt`/`idsIn` não mudam: devolvem id da cena, nunca recebem um de
  fora.
- `ScoreViewController.scrollToId` não precisou de nenhuma linha nova: já
  chama `_doc.geometry.elementOf(id)`, que passou a resolver.
- `_withInteraction` do `ScorePageView` (overlays) também não mudou por
  código: usa `geometry.elementOf(id)` para posicionar cada overlay.
- `animatableIdsFromTimemap` ganhou um parâmetro opcional `document:`
  (assinatura antiga preservada — sem ele, ids passam como estão, do jeito
  que um teste síntetico já testava). `ScorePageView._rebuildLayers` (o
  único uso em produção) passa `document: widget.document`.

**Por que `ScorePageView`/`_withInteraction` não mudaram:** a resolução foi
posta na camada mais baixa que todo mundo já chama (`ScoreGeometry`,
`ScoreController`), não repetida em cada chamador — só
`animatableIdsFromTimemap` precisou de um parâmetro novo, porque ela não
recebe o documento (só a lista de timemap).

**Critérios de aceite.**

1. Testes unitários da resolução em `test/expansion_test.dart`: os 6 casos
   do critério 1 (`x`→`x`/1; `x-rend2` com base→`x`/2; `x-rend3`→`x`/3;
   `x-rend2` presente na cena→ele mesmo/1; base ausente→`null`;
   `abc-rendezvous`→`null`), mais `VsbDocument.sceneIdOf`/`passOf` e um caso
   de `animatableIdsFromTimemap`.
2. `compare/scripts/check-suffix-rule.py` (novo): gera `-t expansionmap` e
   o `.vsb` (mesmo `--xml-id-seed`) das 10 peças **e** das 13 partituras de
   E01a, e compara a regra do sufixo com o que `-t expansionmap` diz ser a
   base de cada id de `on`/`off`/`measureOn` do timemap. **0 divergências em
   12 388 ids** (bem mais que os 2 933 verificados informalmente em E01b).
3. `test/score_player_test.dart`: novo teste "Gymnopédie: destaque não-vazio
   durante toda a 2ª passagem" — 20 instantes sorteados entre 92 368 e
   165 789 ms, `controller.highlightedIds` bate com os ids ativos do timemap
   **resolvidos** e nunca vazio. Antes de E02a esse conjunto seria vazio o
   tempo todo (o motivo de existir este passo).
4. Novo teste com a fixture `test/fixtures/r13-um-compasso.vsb` (gerada de
   `corpus/repeticoes/r13-um-compasso.musicxml`, E01a): 1 ms depois do
   instante em que a passagem 2 começa (`off m1n1` + `on m1n1-rend2` no
   mesmo instante, 2000 ms), a nota está destacada; quase 2 s depois (bem
   dentro do que seria a janela de `release` do bug antigo) continua
   destacada, na cor cheia — nunca esteve em `release`.
5. `test/expansion_test.dart`: um timemap sintético com só `x-rend2` (sem
   `x` solto) torna `x` dinâmico com `document:` e não sem. Sobre o corpus
   real: o conjunto de nós dinâmicos por página com/sem `document:` é
   **idêntico** nas 10 peças — confirma o achado de E01a ("0 ids-base
   ausentes"; a resolução não muda nada hoje, só protege o futuro).
6. `rectForId('x-rend2') == rectForId('x')`, `pageOf` idem,
   `elementOf('x-rend2')!.id == 'x'` (`expansion_test.dart`, documento
   sintético). `scrollToId` com um id `-rend<N>` sintético (base real +
   sufixo) em `score_view_test.dart`, nos dois modos (`pagedSweep` e
   `continuousScroll`): rola para a mesma página que o id base.
7. `nao-existe-rend2` continua sem destino em todos os pontos que já
   testavam isso (`score_controller_test.dart`, `score_view_test.dart`) —
   sem mudança de comportamento porque a base "nao-existe" não está na
   cena. `flutter analyze` limpo, `flutter test` 220/220 (era 207; a
   diferença é só teste novo, nenhum teste pré-existente removido).

**Teste pré-existente atualizado (comportamento, não regressão):**
`score_controller_test.dart` — "highlightAll com 50 ids: uma notificação;
-rend2 ignorados" testava exatamente o defeito que este passo corrige (ids
`-rend2` eram ignorados). Renomeado e reescrito para o comportamento
correto: um `-rend2` cuja base já está entre os 50 ids reais resolve à
mesma nota (sem duplicar `highlightedCount`) e passa a responder
`isHighlighted`/`colorOf` como a base.

**Fora do escopo, como previsto:** a sequência de compassos e a página
durante a repetição continuam vindo da cena sem resolução (E02b); a
escolha de passagem num toque (`onElementTap`) é E02c.
