# P01c — Regenerar corpus e fixtures, re-medir paridade e fatos

**Depende de:** P01b · **Decisão necessária:** não

## Objetivo

Os padrões de P01b mudam a paginação de **todas** as peças: sem cabeçalho,
rodapé e rótulo, cabem mais compassos por sistema e mais sistemas por página.
Números fixados no plano e nos testes (páginas por peça, páginas dos saltos,
`edgeX` da haste, contagens por página) ficam errados. Este passo regenera
tudo, re-mede e corrige os documentos e testes **sem mudar código de
produção**.

## Ler antes (só isto)

- `docs/plano/README.md`: "Fatos medidos nos `.vsb` do corpus" e "Repetições
  no corpus".
- `compare/scripts/compare-page.sh` e `compare/scripts/compare-corpus.sh`.
- `docs/plano/E05-portao-das-repeticoes.md`, "Notas de execução" (como as
  fixtures de `score_bridge/test/fixtures/repeticoes/` foram geradas:
  `-x 42`, `--breaks encoded` para r06/r07).

## Contexto que você precisa (não vá procurar, está aqui)

- **Paridade:** a referência SVG precisa ser desenhada com **as mesmas
  opções** do `.vsb`. Os scripts de comparação passam a chamar `-t svg` com
  `--header none --footer none --no-instrument-labels`. Sem isso, toda página
  diverge.
- Fixtures que precisam ser regeneradas (todas com `-x 42`):
  - `score_bridge/test/fixtures/maple-leaf-rag.vsb` (usada por
    `score_timeline_jump_curtain_test.dart`, com `edgeX` esperados fixos);
  - `score_bridge/test/fixtures/repeticoes/*.vsb` (23 arquivos);
  - `erik-satie.vsb` e `r13-um-compasso.vsb`: confira nos testes se algum
    número depende da paginação. Se nada depender, **não** regenere (menos
    ruído).
- Fatos de hoje que **vão mudar** e que os passos seguintes citam: 34
  páginas no corpus; Maple Leaf Rag com saltos 34 → 19 (página 1 → 0) e
  67 → 52 (página 2, a última, → 1), 66 → 68 cruzando da página 1 para a 2;
  Gymnopédie 39 → 1 e Maple 84 → 69 na mesma página.
- A paridade de referência é média **0,008800%** (Skia, tolerância 128/255),
  em `docs/relatorio-paridade.md`. Com menos texto (sem título, número de
  página e rótulo), é esperado que a média **caia**. Uma página que piorar
  precisa de explicação.

## O que fazer

1. Scripts de comparação: acrescente as três flags ao `-t svg` de referência
   e à sondagem de páginas (`compare-corpus.sh` L74). O `-t vsb` já recebe os
   padrões sozinho.
2. Regenere o corpus em `compare/out/p01c/` e rode a varredura de paridade
   (R06a) completa.
3. Regenere as fixtures listadas acima com os mesmos parâmetros de antes.
4. Rode `flutter test`. Para cada teste que quebrar **só** por número de
   paginação (página, `edgeX`, contagem), meça o valor novo, confira que o
   comportamento é o mesmo (a mesma regra, outro número) e atualize a
   expectativa. Registre cada troca numa tabela nas notas (arquivo, valor
   antigo, valor novo, por quê). Um teste que quebrar por **outro** motivo:
   pare e investigue.
5. Re-meça e atualize no `README.md` do plano:
   - "Fatos medidos nos `.vsb` do corpus" (peças/páginas e o que mudar);
   - a lista de saltos entre páginas e na mesma página (use
     `compare/scripts/repeat-order.py` + a página de cada compasso);
   - acrescente uma tabela nova, "Saltos e pontos de chegada (P01c)": para
     cada peça com repetição, cada salto `origem → destino`, página de
     origem, página de destino, e se o destino é o 1º compasso da página.
     **É a entrada de P02b.**
6. Atualize `docs/relatorio-paridade.md` com a nova varredura (seção nova
   datada; não apague a anterior).

## Fora de escopo

- Qualquer mudança em `score_bridge/lib` ou em `verovio/src`.
- Páginas alternativas.

## Critérios de aceite

1. Varredura de paridade das páginas do corpus acima de 99,99% em todas as
   páginas, com média registrada e comparada à de 0,008800%.
2. `flutter test` verde, com a tabela de expectativas trocadas nas notas.
3. `repeticoes_test.dart` verde: a **sequência de compassos** (ordem de
   execução) não pode mudar, só as páginas.
4. README do plano com os fatos re-medidos e a tabela "Saltos e pontos de
   chegada".
5. `flutter analyze` limpo.

## Notas de execução

**Scripts.** `compare/scripts/compare-page.sh` e `compare-corpus.sh`: as
duas chamadas de `-t svg` (referência de página e sondagem de contagem de
páginas) ganharam `--header none --footer none --no-instrument-labels`. O
`-t vsb` não mudou: já recebe os padrões sozinho desde P01b
(`ApplyBridgeDefaults`).

**Varredura de paridade (critério 1).** `CORPUS_DIR=compare/out/p01c/corpus
compare-corpus.sh 128` — git-ignorado, não sobrescreve `compare/corpus/`
(versionado, referência de R06c/E05 **sem** os padrões novos). 34/34
páginas, média **0,006402%** (era 0,008800%, −27%), máximo 0,024964% (era
0,038624%), 27/34 páginas ≤ 0,01%, 34/34 ≤ 0,05% — o portão de paridade
continua satisfeito, com folga maior (menos texto desenhado = menos piso de
antialiasing, a maior fonte de divergência conhecida). Detalhes e tabela em
`docs/relatorio-paridade.md`, seção "Atualização de 2026-09-22".

**Fixtures regeneradas** (mesmo comando de sempre, `-x 42`, `--breaks
encoded` só em r06/r07 — a paginação nova não muda nenhum flag de geração,
só o binário do Verovio já aplica os padrões):
`score_bridge/test/fixtures/repeticoes/*.vsb` (23 arquivos, as 10 peças do
corpus + as 13 partituras de E01a) e as cópias avulsas `erik-satie.vsb`,
`maple-leaf-rag.vsb`, `r13-um-compasso.vsb` (idênticas às de
`repeticoes/`, como sempre foram).

**Achado que não é de P01c: `maple-leaf-rag.vsb` estava parado desde
E02b.** Esse fixture nunca tinha sido regenerado depois de E04b (que
corrigiu a Maple Leaf Rag perder o 1º ritornelo: README, "Repetições no
corpus", 130 → 145 ocorrências) — só a cópia em `repeticoes/` tinha sido
atualizada, em E05. Os testes que usam `maple-leaf-rag.vsb`
(`score_timeline_occurrences_test.dart`, `score_timeline_jump_curtain_test.dart`)
ainda esperavam 130 ocorrências e os saltos/tempos de antes de E04b. Regenerar
em P01c corrigiu esse latente, então algumas das mudanças abaixo são o efeito
de E04b aparecendo agora, não um efeito de P01b/P01c em si — registrado
comentário por comentário nos arquivos de teste.

**`flutter test` (critério 2).** 7 falhas na 1ª rodada após regenerar os
fixtures, todas por número (nenhuma por lógica):

| Arquivo | Teste | Valor antigo | Valor novo | Por quê |
| --- | --- | --- | --- | --- |
| `corpus_fixture_test.dart` | elements pág. 0 | 1055 | 1114 | sem pgHead/pgFoot/label (D-VSB-PADRAO) |
| `corpus_fixture_test.dart` | 1º `system` da pág. 0 | id `d1wmfkp6`, bbox `(180, 546.16, 20008.5, 4886)` | id `xm8ku22`, bbox `(-441, 0.16, 20010.5, 4646)` | sem cabeçalho, o 1º `system` some antes; sem rótulo, a pauta começa em x negativo (a barra de compasso fica à esquerda de x=0, achado já citado em P00 para `--no-instrument-labels`) |
| `corpus_fixture_test.dart` | último elemento da pág. 0 | id `a1zfws3`, classe `svg`, nodePath 1378 | id `v14b0krf`, classe `text`, nodePath 1465 | sem cabeçalho, a árvore troca de forma (o nó `svg` raiz deixa de ser o último a aparecer no percurso pré-ordem porque o cabeçalho, que vinha depois, não existe mais) |
| `corpus_fixture_test.dart` | elements pág. 1 | 170 | 88 | idem (pág. 1 não tem pgFoot de "MEI engraved with Verovio" nem número de página) |
| `score_timeline_jump_curtain_test.dart` | salto que cruza página no meio da peça | 39900ms, pág. 1→0 | **não existe mais** | a página 0 agora cabe mais compassos; esse salto fica inteiro dentro dela (mesma regra "sem haste na mesma página", só que agora sem precisar de haste onde antes precisava) |
| `score_timeline_jump_curtain_test.dart` | salto da última página | 97500ms, pág. 2→1 | 153900ms, pág. 2→1 (mesmos índices de página, novo tempo/compasso) | E04b (145 em vez de 130 ocorrências) desloca todos os tempos depois do 1º ritornelo perdido |
| `score_timeline_occurrences_test.dart` | contagem de ocorrências | 130 (85 pass1, 45 pass2) | 145 (85 pass1, **60** pass2) | efeito de E04b, não de P01b/P01c (ver achado acima) |
| `score_timeline_occurrences_test.dart` | `restPageAt(58000)` | página 1 | página 0 | paginação nova |
| `score_timeline_occurrences_test.dart` | salto até um compasso específico | 39900ms → compasso 19 (`qqplm6a`) | **não é mais um salto** (39900ms é sequência normal); troquei pelo 1º ritornelo (19500ms → `q1t6l0ej`), que continua sendo um salto de verdade | mesmo motivo do item acima |

Todos os valores novos foram medidos com scripts descartáveis
(`test/_scratch*.dart`, apagados depois) que chamam a mesma API que o teste
final usa (`ScoreTimeline`, `SweepCurtain`, `curtainAt`), nunca inventados.
`repeticoes_test.dart` (critério 3, sequência de execução) e
`occurrencesOf` (grupo "critério 6" de `score_timeline_occurrences_test.dart`)
já passavam sem alteração: nenhum dos dois depende de posição/página, só da
ordem de compassos e da resolução de ids, que P01c não toca.

Depois dos ajustes: **271/271 verdes** (`flutter test`), `flutter analyze`
limpo. Build do Verovio sem avisos novos (só os dois arquivos de scripts e
docs mudaram no lado C++; nenhum `.cpp`/`.h` neste passo).

**Critério 4** — README atualizado: fatos de página (34 no total, inalterado);
tabela nova "Saltos e pontos de chegada (P01c)" com origem/destino/página/se
é 1º compasso de página normal, para as 6 peças com repetição de verdade.
**Critério 5**: `flutter analyze` limpo (rodado acima).
