# E02b — Linha do tempo por ocorrência de compasso

**Depende de:** E02a · **Decisão necessária:** não

## Objetivo

`ScoreTimeline.measures` passa a ser, de fato, a **ordem de execução**: um
compasso repetido aparece uma vez por passagem. Com isso, o compasso
corrente, a página em repouso e a rolagem contínua acompanham a música
durante a repetição, inclusive quando ela volta para uma página anterior.

A haste nos saltos é do E03. Aqui, um salto para outra página é um **corte
seco** no instante do salto (a vista vai à página certa via `goToPage`). É um
comportamento provisório, mas correto.

## Ler antes (só isto)

- `score_bridge/lib/src/score_timeline.dart` inteiro (361 linhas): `_build`
  L115, `_collect` L197, `measureIndexAt` L227, `curtainAt` L255 e as regras
  de haste no comentário do topo.
- `score_bridge/lib/src/score_player.dart`: `_publish` (L253).
- A05a e A05b, só as "Notas de execução".
- E02a (`sceneIdOf`/`passOf`).

## Contexto que você precisa (não vá procurar, está aqui)

- **O defeito de hoje.** `_build` cria um `_Measure` por id de compasso
  (`byId.putIfAbsent`), ou seja, só na **primeira** ocorrência, e pula as
  notas `-rend2`. Durante a 2ª passagem, `measureIndexAt` fica preso no último
  compasso "novo" antes dela:
  - **Maple Leaf Rag**, de 39 900 a 57 900 ms: a música toca os compassos
    19-33 (página 0 e depois 1), e o índice fica no compasso 34 (casa 1,
    página 1). A vista mostra a página 1 enquanto se toca a página 0.
  - **Gymnopédie**, de 92 368 a 165 789 ms: preso no compasso 39. A página
    (0) coincide por acaso.
- **Ocorrências esperadas com a expansão de hoje** (antes de E04a/E04b):
  Gymnopédie 78 (31 na 2ª passagem), Maple Leaf Rag 130 (45 na 2ª). As outras
  8 peças: uma ocorrência por compasso.
- **Saltos no corpus** (compassos em ordem de documento, base 1):

  | Peça | Instante do salto | De → para | Páginas |
  | --- | --- | --- | --- |
  | Gymnopédie | 92 368 ms | 39 → 1 | 0 → 0 |
  | Maple Leaf Rag | 39 900 ms | 34 → 19 | 1 → 0 |
  | Maple Leaf Rag | 97 500 ms | 67 → 52 | **2 (última) → 1** |
  | Maple Leaf Rag | 135 900 ms | 83 → 69 | 2 → 2 |

  Viradas **para a frente dentro da 2ª passagem** também existem, e seguem a
  regra normal da haste: Maple Leaf Rag, compasso 29 (página 0) → 30
  (página 1) em 53 100 ms.
- `curtainAt` já pula pares de runs em que a página seguinte não é `P + 1`
  (comentário "salto de repetição: sem haste"). Mas, com a dedução de hoje,
  esse caso quase não acontece.
- Se o timemap tem `measureOn` (E01b), ele é a fonte das ocorrências. `.vsb`
  antigos (como `compare/out/s08/*.vsb`) não têm, e o caminho pelas notas
  precisa continuar funcionando.

## O que fazer

1. `_build` monta **ocorrências**:
   - com `measureOn`: cada `measureOn` resolvido (`sceneIdOf`) abre uma
     ocorrência, com `passOf` como passagem;
   - sem `measureOn`: pelas notas de `on` resolvidas, abrindo uma ocorrência
     nova quando o par (compasso da cena, passagem) muda.

   `noteIds`, `_Onset` e as bboxes usam ids da cena.
2. `MeasureInfo` ganha:

   ```dart
   final int pass;          // 1 na primeira execução do compasso
   final String timemapId;  // o id como está no timemap (id, ou id-rendN)
   ```

   `id` continua sendo o id do compasso na cena (compatível com quem já usa).
3. `_Run` quebra quando a página muda **ou** quando há salto (a ocorrência
   seguinte não é o próximo compasso na ordem de documento). A haste
   continua só nas transições `P → P + 1` **sem** salto. Salto (para trás,
   ou para a frente, como um "To Coda") não tem haste neste passo.
4. Nova consulta: `List<int> occurrencesOf(String id)` → índices em
   `measures`. Id de compasso: as ocorrências dele. Id de nota: as do
   compasso dela. Id expandido: só a da sua passagem.
5. `ScorePlayer`: `currentMeasureIndex` passa a indexar ocorrências (atualize
   a doc). Confira que `_publish` já leva a vista à página de repouso num
   salto (`goToPage`) e que `continuousScroll` rola para o compasso de
   destino.

## Fora de escopo

- Haste nos saltos (E03a/E03b).
- Tocar a partir de um elemento (E02c).
- Expansões erradas do Verovio: este passo só consome o timemap que existe.

## Critérios de aceite

1. Ocorrências: Gymnopédie 78 (31 com `pass == 2`) e Maple Leaf Rag 130 (45),
   as outras 8 peças com uma por compasso. A lista é **idêntica** pelo
   caminho `measureOn` (`.vsb` de E01b) e pelo caminho das notas (`.vsb` de
   S08), e bate com a sequência que o script de E01a imprime.
2. Em todas as peças, `startMs` é estritamente crescente, `endMs` é o
   `startMs` da seguinte, e a página de cada ocorrência é a do compasso na
   cena.
3. Maple Leaf Rag, em `pagedSweep`: em 45 000 ms, `restPageAt == 0` e a vista
   mostra a página 0 (hoje, 1). Em 58 000 ms, a página 1. Em 97 500 ms (salto
   da última página para a 1) a vista vai para a 1, sem exceção.
4. `continuousScroll`: no salto de 39 900 ms, `scrollToId` recebe o compasso
   19.
5. **Regressão da haste:** antes de mexer no código, grave `curtainAt`
   amostrado a cada 50 ms nas 8 peças sem expansão. Depois, os valores são
   idênticos. Nas duas peças com repetição, a virada para a frente de
   53 100 ms (Maple Leaf Rag) tem haste.
6. `occurrencesOf`: compasso 19 da Maple Leaf Rag → 2 ocorrências; uma nota
   dele → as mesmas 2; o id `-rend2` dessa nota → só a 2ª; uma nota da casa 1
   (compasso 34) → 1.
7. Os testes de A05a/A05b que mudaram de significado foram atualizados, cada
   mudança explicada nas notas. `flutter analyze` limpo, `flutter test`
   verde.

## Notas de execução

_(preencher ao executar)_
