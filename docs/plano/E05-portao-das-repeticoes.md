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

_(preencher ao executar)_
