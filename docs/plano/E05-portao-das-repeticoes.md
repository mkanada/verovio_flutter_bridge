# E05 — Portão da fase E: repetições de ponta a ponta

**Depende de:** E02c, E03b, E04b · **Decisão necessária:** não

## Objetivo

Fechar a fase provando, de ponta a ponta (partitura → `.vsb` →
`ScoreTimeline`/`ScorePlayer`), que **cada peça toca na ordem que um músico
tocaria**, que a vista acompanha e que a paridade visual não mudou. Depois,
deixar o plano e a documentação refletindo o estado novo.

## Ler antes (só isto)

- As "Notas de execução" de E01a a E04b.
- `docs/relatorio-paridade.md` (números de referência).

## Contexto que você precisa (não vá procurar, está aqui)

- O script de E01a compara a sequência do **timemap**. Este portão compara a
  do **Dart**: `ScoreTimeline.measures`, com `pass`, contra o `.esperado`.
  São caminhos independentes, e um erro de resolução de id só aparece no
  segundo.
- A paridade atual (R06c, re-medida em Skia) é média 0,008800% nas 34
  páginas. As fases E01-E04 não deveriam mudar nenhum pixel (`scene.json` e
  `glyphs.json` byte-idênticos em cada passo). Este portão confirma com a
  varredura, não só com a comparação de bytes.

## O que fazer

1. Teste Dart (`test/repeticoes_test.dart`) que carrega os `.vsb` das 10 peças
   e das 13 partituras de E01a (fixtures geradas uma vez e versionadas em
   `score_bridge/test/fixtures/repeticoes/`, com `--xml-id-seed` fixo) e
   compara a sequência de `measures` (id do compasso → número em ordem de
   documento) com o `.esperado`.
2. Para cada peça com repetição, um `ScorePlayer` tocando do início ao fim a
   4× em `pagedSweep`: sem exceção, todas as notas apagadas no fim e página
   final correta.
3. Varredura de paridade (R06a) de novo sobre os `.vsb` regenerados.
4. Documentação:
   - README do plano: a tabela de repetições com os números finais, a linha
     "Ids do timemap ausentes da cena" (agora resolvidos por E02a), o mapa do
     código (`expansion`/`sceneIdOf`, `MeasureInfo.pass`, `onsetsOf`,
     `seekToElement`, `SweepCurtain.targetPageIndex`) e os status da fase E;
   - `CLAUDE.md`, em "Decisões registradas": D-EXPMAP, D-EXPAND, D-SALTO e
     D-TOQUE como foram decididas;
   - especificação: conferir que §2 descreve `measureOn` e os ids expandidos
     como ficaram.
5. Nota curta para o `zywny` (em `docs/`, sem mexer no app): o que o host
   ganha (`MeasureInfo.pass` para mostrar "2ª vez", `seekToElement`) e o
   que continua fora (modo sem repetições; D.C./D.S. em MEI).

## Fora de escopo

- Modo "sem repetições" (precisa de uma segunda expansão; `--expand-never`
  não serve, ver E04a).
- D.C./D.S./coda em MEI.
- Qualquer mudança no `zywny`.

## Critérios de aceite

1. `repeticoes_test.dart` verde: as 23 sequências batem com o `.esperado`.
2. As peças com repetição tocam do início ao fim a 4× sem exceção e terminam
   sem destaque.
3. Varredura de paridade: nenhuma página muda de percentual em relação a
   `docs/relatorio-paridade.md` (média 0,008800%, Skia), ou cada diferença é
   explicada.
4. README, `CLAUDE.md` e especificação atualizados, e toda a fase E marcada
   `concluído` na tabela de passos.
5. `flutter analyze` limpo, `flutter test` verde, build do Verovio sem avisos
   novos.

## Notas de execução

**Fixtures.** `score_bridge/test/fixtures/repeticoes/` (novo, 23 arquivos
`.vsb`, ~1,9 MB): as 10 peças do corpus + as 13 partituras de E01a, todas
geradas com `-x 42` (ids estáveis) — `--breaks encoded` também para
r06/r07, que dependem de quebra de página codificada. Gerados uma vez e
versionados, como o passo pedia.

**`test/repeticoes_test.dart`.** Dois caminhos independentes comparados,
como o passo descreve:

- **E01a (`repeat-order.py`) lê o timemap** e já validou, em cada passo da
  fase, que a sequência de execução bate com o `.esperado` — mas nunca
  passou pelo Dart.
- **Este teste usa `ScoreTimeline.measures`** (que resolve ids expandidos
  via `sceneIdOf`/`passOf`, E02a, e monta ocorrências, E02b) e monta a
  mesma notação em blocos (`1-4 1-4 5-6`) a partir da ordem de documento
  dos compassos na cena (`_measureOrder`, o mesmo tipo de percurso usado
  em vários passos anteriores) — sem tocar no `repeat-order.py` nem no
  script Python de forma alguma.

As 23 sequências batem, byte a byte com o `.esperado` — nenhuma
divergência entre os dois caminhos apareceu (o que confirmaria um erro de
resolução de id só visível no lado Dart).

**Reprodução completa (critério 2).** As 6 peças com repetição de verdade
(Gymnopédie, Maple Leaf Rag, Mazurka, Butterfly, Little bird, Scarlatti)
tocadas com `player.play(); player.speed = 4.0` e `tester.pump` (o Ticker
real do `ScoreController`/`ScorePlayer`, não `advance()` manual — só assim
o `release` dos destaques termina de verdade; uma tentativa inicial com
`advance()` manual deixava `highlightedCount` preso porque o relógio do
*destaque* é o do `ScoreController`, movido a frames reais, não o do
`ScorePlayer`). Todas terminam com `isPlaying == false`, posição igual à
duração, nenhum destaque aceso e a página final certa
(`restPageAt(posição final) == página do último compasso`). As 13
partituras mínimas não entraram nessa reprodução completa (já são curtas
demais para testar vazamento/exceção de forma interessante, e já foram
exercitadas por `ScorePlayer` em E02a/E02c/E03b).

**Varredura de paridade (critério 3).** `compare-corpus.sh 128` rodado com
`CORPUS_DIR=compare/out/e05-parity` (git-ignorado — não sobrescreve o
`compare/corpus/` versionado de R06c) sobre os `.vsb` regenerados com o
binário atual (pós E04a/E04b). Resultado: **34/34 páginas**, média
**0,008800%**, mesma distribuição de R06c/2026-09-20 (27/34 ≤ 0,01%, 34/34
≤ 0,05%) — **nenhuma página mudou de percentual**. Esperado: toda a fase E
(exceto os dois passos do fork) mexeu só em `score_bridge`, e os dois
passos do fork (E04a/E04b) já tinham `scene.json`/`glyphs.json`
comprovados byte-idênticos nas suas próprias notas de execução.

**Documentação atualizada:**

- README: tabela de repetições com os números finais (Mazurka 117,
  Butterfly 48, Little bird 69, Scarlatti 99, Maple Leaf Rag 145, todos
  "corrigido em E04a/E04b"); linha "Ids do timemap ausentes da cena"
  atualizada (resolvida desde E02a); mapa do código com as entradas de
  E02a-E04b; toda a fase E marcada `concluído` na tabela de passos.
- `CLAUDE.md`, "Decisões registradas": D-EXPMAP, D-EXPAND, D-SALTO e
  D-TOQUE, como foram decididas e onde estão implementadas.
- `docs/formato/especificacao-v1.md`: §2.4 (escrita em E01b) já descreve
  `measureOn` e a regra do sufixo dos ids expandidos; conferido que
  continua exata depois de E02a-E04b (nenhuma mudança de formato depois
  de E01b — só de comportamento em `score_bridge` e no fork).
- `docs/nota-para-zywny-fase-e.md` (novo): o que o host ganha
  (`MeasureInfo.pass`, `seekToElement`, resolução automática de ids
  expandidos, vista acompanhando saltos) e o que continua fora (modo sem
  repetições, D.C./D.S. em MEI, casas com mais de dois números, repetição
  aninhada).

**Critérios de aceite:**

1. `repeticoes_test.dart` verde: as 23 sequências batem com o `.esperado`
   (grupo "sequência de execução", 23 testes).
2. As 6 peças com repetição tocam do início ao fim a 4× sem exceção e
   terminam sem destaque, na página certa (grupo "ScorePlayer toca do
   início ao fim", 6 testes).
3. Varredura de paridade: 0,008800% de média, idêntica a
   `docs/relatorio-paridade.md` — nenhuma página mudou.
4. README, `CLAUDE.md` e especificação atualizados; fase E inteira
   `concluído` na tabela de passos.
5. `flutter analyze` limpo, `flutter test` 272/272 (era 243 antes deste
   passo: 29 testes novos em `repeticoes_test.dart`). Build do Verovio sem
   avisos novos (conferido ao final de E04a e E04b, cada um só recompilando
   o próprio arquivo tocado).
