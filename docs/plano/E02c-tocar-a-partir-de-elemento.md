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

_(preencher ao executar)_
