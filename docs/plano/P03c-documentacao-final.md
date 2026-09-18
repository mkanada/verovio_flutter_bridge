# P03c — Documentação final e fechamento dos requisitos

**Depende de:** P03b · **Decisão necessária:** não

## Objetivo

Deixar o projeto legível para quem chega depois — incluindo o próprio usuário
daqui a seis meses — e declarar, um a um, os quatro requisitos atendidos, cada
um apontando para a evidência que o prova.

## Ler antes (só isto)

- [`CLAUDE.md`](../../CLAUDE.md) (os quatro requisitos e as decisões
  arquiteturais).
- [`docs/relatorio-paridade.md`](../relatorio-paridade.md) (R06c) e
  `docs/medicoes.md` (P01a/P03a).
- [README do plano](README.md) (a tabela de passos).

## Contexto que você precisa (não vá procurar, está aqui)

Mapa requisito → evidência, que é o esqueleto do fechamento:

| Requisito (`CLAUDE.md`) | Evidência |
| --- | --- |
| Paridade visual > 99,9% | `docs/relatorio-paridade.md` (R06c) |
| Animação individual por nota | critério 1 de A02c (frames com fases distintas) |
| Cor individual em runtime | critérios 2, 3 e 5 de A01c e A02b |
| Virada de página + overlays | A03b (frames da virada) e A04b (overlay alinhado) |

Documentos que precisam refletir o que a implementação **descobriu**, não o
que o plano previa:

- `README.md` da raiz: estado real, como buildar, como usar;
- `score_bridge/README.md`: a API pública com exemplos curtos;
- `docs/formato/especificacao-v1.md`: tudo que mudou durante a execução, com
  o "Histórico de revisões" atualizado (S08 já deve ter entrado ali);
- `CLAUDE.md`: decisões que mudaram, decisões pendentes que foram resolvidas
  (D-BIN em P01b, D-RUNTIME em P02a, backend gráfico em R05a).

## O que fazer

1. Escrever/atualizar os quatro documentos acima.
2. Conferir que **toda** decisão que estava pendente foi resolvida e
   registrada com data — ou, se continua aberta, que está marcada como aberta
   e com o motivo.
3. Percorrer a tabela de passos do README do plano: cada passo `concluído`
   com notas de execução preenchidas; cada ressalva ainda válida repetida no
   README, para não ficar escondida dentro do arquivo do passo.
4. Fazer uma leitura de olhos frescos: pegar um passo qualquer da fase R e
   conferir se alguém que só lê `CLAUDE.md` + README + aquele arquivo
   conseguiria executá-lo.

## Fora de escopo

- Publicar o pacote.
- Refatoração de código "para ficar bonito na documentação".

## Critérios de aceite

1. Os quatro requisitos do `CLAUDE.md` estão declarados como atendidos, cada
   um apontando para a evidência concreta (tabela acima).
2. `README.md` da raiz, `score_bridge/README.md`,
   `docs/formato/especificacao-v1.md` e `CLAUDE.md` atualizados e coerentes
   entre si.
3. A tabela de passos do README do plano está com todos os passos
   `concluído`, cada um com notas de execução preenchidas, e as ressalvas
   ainda válidas visíveis no próprio README.
4. Todas as decisões (D-BIN, D-RUNTIME, backend gráfico) estão registradas com
   data e resultado.
5. `flutter analyze` limpo em `score_bridge/`, `compare/` e `example/`.

## Notas de execução

(a preencher por quem executar)
