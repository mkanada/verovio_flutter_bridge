# P01b — Gate D-BIN: decidir (com o usuário) se o JSON fica

**Depende de:** P01a · **Decisão necessária:** SIM (D-BIN), **em duas etapas**

## Objetivo

Levar os números ao usuário e registrar a decisão sobre encoding binário. A
decisão é dele, em duas etapas: primeiro *se* vale mexer, e só depois *como*.

## Ler antes (só isto)

- `docs/medicoes.md` (P01a).
- `../verovio_lottie/docs/plano/D06-tamanho-do-arquivo.md`, seção "Passo 0" —
  o método de decidir com o usuário continua valendo (o conteúdo técnico de
  lá **não** vale: o conflito precomp × slot de cor não existe aqui).
- Linha D-BIN da tabela de decisões do [README do plano](README.md).

## Contexto que você precisa (não vá procurar, está aqui)

- O `.vsb` já é zip com deflate; o JSON comprime bem. As duas perguntas que
  importam para o zywny são **tempo de abertura** e **tamanho no aparelho/
  rede** — não "JSON é elegante".
- Ordem de custo/benefício das técnicas, se a resposta for "reduzir"
  (proponha, não escolha sozinho):
  1. comprimir melhor o que já existe (medir `-9` no zip);
  2. reduzir precisão numérica (menos dígitos significativos) — **medir
     paridade antes e depois**;
  3. CBOR/MessagePack (troca o parser, mantém o modelo);
  4. FlatBuffers (schema compartilhado, parse quase zero-cópia).
- **Precisão numérica é a forma mais fácil de quebrar a paridade sem
  perceber.** A especificação hoje limita a 6 dígitos significativos (§7);
  qualquer redução exige rodar R06 de novo.
- Se a resposta for "está bom", o passo **termina** — não implemente nada.
  Essa é a saída esperada, não um fracasso.

## O que fazer

1. Montar um resumo de meia página: tamanho e tempo de abertura por peça, o
   pior caso (peça grande), e o que cada um significa na prática ("abrir uma
   sonata de 20 páginas leva X ms no aparelho Y").
2. Fazer a pergunta objetiva: *o tempo de abertura e o tamanho são um
   problema para o zywny?*
3. Registrar a resposta, **com data**, em `docs/medicoes.md` e marcar D-BIN
   como resolvida na tabela do README do plano e no `CLAUDE.md`.
4. Se for "reduzir": apresentar as opções acima com estimativa de custo e
   ganho, pedir a escolha, e só então implementar.

## Fora de escopo

- Implementar qualquer encoding novo sem decisão registrada.
- Mexer em precisão numérica "de leve" para testar — se mexer, o critério 4
  vale.

## Critérios de aceite

1. A pergunta foi feita e a resposta está registrada em `docs/medicoes.md`,
   com data.
2. D-BIN está marcada como resolvida no [README do plano](README.md) e no
   `CLAUDE.md`, com o resultado.
3. Se a decisão for "está bom": nada foi implementado, e o documento diz isso
   explicitamente.
4. Se a decisão for implementar algo: **paridade inalterada** — R06a/R06c
   rodados de novo, com as mesmas médias (diferença desprezível e explicada),
   e o relatório de paridade atualizado com a nova medição.
5. Se a decisão envolver mudança de formato: a
   [especificação](../formato/especificacao-v1.md) foi atualizada e o
   "Histórico de revisões" registra a mudança.

## Notas de execução

(a preencher por quem executar)
