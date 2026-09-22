# E02c — Tocar a partir de um elemento repetido

**Depende de:** E02b · **Decisão necessária:** **sim — D-TOQUE** (pare e
pergunte antes de escrever código)

## Objetivo

O host toca numa nota ou num compasso (`onElementTap`, A04b) e quer que o
player vá para lá. Com repetição, o mesmo desenho é tocado em mais de um
instante. Este passo dá a API que escolhe o instante e deixa a escolha
explícita quando o host quiser.

## Decisão necessária — D-TOQUE

**Qual passagem `seekToElement(id)` escolhe quando o elemento é tocado mais
de uma vez?**

- **(a) A mesma passagem da posição atual, se o elemento a tiver; senão a
  primeira (recomendado).** Quem está na 2ª passagem e toca num compasso de
  dentro da repetição continua na 2ª (é o caso de treinar a entrada da casa
  2). Quem está depois da repetição e toca num compasso de dentro dela volta
  para a 1ª.
- **(b) Sempre a primeira.** Previsível e simples. O host que quiser outra
  passa `pass:` explicitamente.
- **(c) A próxima ocorrência a partir da posição atual.** Tocar num compasso
  anterior dentro da repetição levaria para a frente, para a 2ª passagem, e
  não para trás.

Nos três casos, `pass:` explícito ganha da política.

## Ler antes (só isto)

- `score_bridge/lib/src/score_player.dart`: `seek` (L213).
- `score_bridge/lib/src/score_timeline.dart` depois de E02b
  (`occurrencesOf`, `MeasureInfo.pass`).
- `score_bridge/lib/src/score_page_view.dart` L257-L270 (`onElementTap` e
  `idAt`).

## Contexto que você precisa (não vá procurar, está aqui)

- `idAt` devolve id **da cena** (nota, por padrão; as classes aceitas são
  configuráveis). O id expandido nunca vem de um toque, mas pode vir do host
  (do timemap).
- O instante de uma nota numa passagem é o `tstamp` da entrada cujo `on` tem
  o id dela com aquele `-rendN` (ou sem sufixo, na passagem 1). O instante de
  um compasso é o `startMs` da ocorrência.
- Gymnopédie: a 1ª passagem dos compassos 1-39 vai de 0 a 92 368 ms e a 2ª
  (compassos 1-31) de 92 368 a 165 789 ms. Os compassos 32-39 (casa 1) só são
  tocados na 1ª. Os compassos 40-47 (casa 2) vêm depois de 165 789 ms e,
  por serem tocados uma vez só, são passagem 1.

## O que fazer

1. `ScoreTimeline.onsetsOf(String id)` → `List<({int pass, double ms})>`, em
   ordem de tempo, com uma entrada por passagem em que o elemento é tocado
   (compasso, nota ou id expandido, conforme o contexto acima; o id expandido
   devolve só a sua passagem).
2. `ScorePlayer.seekToElement(String id, {int? pass})` → `bool`: resolve pela
   política de D-TOQUE, chama `seek` e devolve `false` sem mexer em nada se o
   id é desconhecido, se a passagem pedida não existe ou se não há timemap.
3. Documente na API pública o exemplo de ligação `onElementTap:
   (id) => player.seekToElement(id)`.

## Fora de escopo

- Desenhar um seletor de passagem na interface (é do `zywny`).

## Critérios de aceite

1. Gymnopédie, nota do compasso 5, com a política decidida. Posição em
   10 000 ms → onset da 1ª passagem. Posição em 100 000 ms → da 2ª. Posição
   em 170 000 ms → conforme D-TOQUE (a e b: 1ª; c: nenhuma seguinte, então
   documente o que acontece).
2. `pass: 2` explícito leva ao onset da 2ª em qualquer posição, e `pass: 3`
   devolve `false` sem mudar a posição nem os destaques.
3. Nota da casa 1 (compasso 32): uma ocorrência só, e vai para ela de
   qualquer posição.
4. Id expandido (`x-rend2`) sem `pass:` vai para a passagem 2.
5. Teste de widget: toque numa nota via `onElementTap` → `seekToElement` → a
   nota tocada é a destacada depois do seek.
6. `flutter analyze` limpo, `flutter test` verde.

## Notas de execução

**D-TOQUE resolvida pelo usuário: (a) mesma passagem da posição atual,
senão a 1ª** (`pass:` explícito sempre ganha).

**Código novo.** `ScoreTimeline.onsetsOf(id)` (`score_timeline.dart`):
- se `id` resolve a um **compasso** (`_measureOfId[sceneId] == sceneId`), os
  onsets vêm de `occurrencesOf(id)` — reaproveita a lista de ocorrências de
  E02b, um `(pass, startMs)` por ocorrência;
- senão (nota, ou outro elemento com onset no timemap), varre `entries`
  procurando por `on` cujo `sceneIdOf` bate com o alvo, coletando
  `(passOf(onId), tstamp)`; um `id` expandido filtra para só a sua passagem
  (mesmo padrão de `occurrencesOf`).

`ScorePlayer.seekToElement(id, {pass})`: pega `timeline.onsetsOf(id)`; com
`pass` explícito, procura o onset daquela passagem (`false` se não achar);
sem `pass`, aplica D-TOQUE — `currentPass` é a passagem da ocorrência em
`timeline.measures[timeline.measureIndexAt(_positionMs)]`, e o alvo é o
onset da mesma passagem ou, na ausência, `onsets.first` (que é sempre a
passagem 1, porque `onsets` está em ordem de tempo e a 1ª passagem sempre
toca antes das demais). `false` sem mexer em nada se `onsets` vier vazio
(id desconhecido, ou sem timemap) ou (com `pass` explícito) se a passagem
pedida não existir. Guarda `_disposed` igual às outras chamadas públicas do
player.

Doc da API pública: `ScorePageView.onElementTap` agora cita o exemplo de
ligação (`onElementTap: (id) => player.seekToElement(id)`), e o método em
si documenta a política por extenso.

**Fixture novo**: `test/fixtures/erik-satie.vsb` reaproveitado (já tinha
`measureOn` de E01b/E02b). Não foi preciso nenhum fixture novo — os números
usados (compasso 5 = `jbxc50u`, nota `i88ib9g`, onsets 9 474 ms/101 842 ms;
compasso 32 = ocorrência única) foram lidos direto do `.vsb` existente.

**Critérios de aceite** (`test/score_player_seek_test.dart`, 8 testes):

1. Gymnopédie, nota do compasso 5: posição 10 000 ms → onset da 1ª (9 474
   ms); 100 000 ms (dentro da repetição) → onset da 2ª (101 842 ms);
   170 000 ms (depois da repetição, casa 2, tocada uma vez em pass 1) →
   conforme D-TOQUE(a): 1ª — bate com o que o critério já antecipava para as
   opções (a) e (b).
2. `pass: 2` explícito leva ao onset da 2ª de qualquer posição; `pass: 3`
   devolve `false` sem mudar a posição.
3. Nota da casa 1 (compasso 32, ocorrência única): uma só entrada em
   `onsetsOf`, e `seekToElement` vai para ela a partir de 4 posições
   diferentes (0, 50 000, 120 000, 170 000 ms).
4. Id expandido (`i88ib9g-rend2`) sem `pass:` vai para a passagem 2, mesmo
   partindo de uma posição na 1ª passagem.
5. Teste de widget: `ScorePageView` com `onElementTap: (id) =>
   player.seekToElement(id)`, toque físico (`tester.tapAt`) no centro da
   bbox da nota do compasso 5 → `player.position` vai para 9 474 ms e a nota
   fica destacada (`controller.isHighlighted`).
6. `id` desconhecido → `false`, posição inalterada.
7. `flutter analyze` limpo, `flutter test` 235/235 (era 227; 8 testes
   novos).

**Armadilha de teste (não é do produto):** os testes que chamam
`ScorePlayer.seek`/`seekToElement` sem depois desligar o `Ticker` antes do
fim do `testWidgets` derrubam a suíte com "An animation is still running
even after the widget tree was disposed" se a limpeza for feita via
`addTearDown` — o comentário em `score_player_test.dart` já avisava
("`addTearDown` roda tarde demais para a verificação do binding"), mas só
bateu nele de verdade ao escrever este arquivo. A limpeza precisa estar num
`finally` dentro do próprio corpo do teste (função `withPlayer` deste
arquivo, mesmo padrão do `Cleanup`/`testPlayer` de `score_player_test.dart`).
