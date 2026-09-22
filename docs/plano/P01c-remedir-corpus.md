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

_(preencher)_
