# G08a — Especificação: glifos de pausa, figura no `pitchpos.json`, §11

**Depende de:** — · **Decisão necessária:** sim — **D-SUM-FIGURA** (ver
[`G07`](G07-visao-geral-nota-escondida.md)). Pergunte ao usuário antes de
escrever; a recomendação é a opção (a).

## Objetivo

Deixar escrito, na especificação do formato, tudo o que o host precisa para
esconder uma coluna de notas e desenhar a pausa substituta: os glifos que o
dicionário passa a trazer sempre, a figura da nota e a regra normativa.
Só documento e schema — nenhuma linha de C++.

## Ler antes (só isto)

- [`G07`](G07-visao-geral-nota-escondida.md) inteiro.
- `docs/formato/especificacao-v1.md`: §2.8 (`pitchpos.json`), §4 (glifos
  reservados, L564), §5.1 (nó `staff`: `lines`, `ledger`, `ledgerCue`,
  `gs`), §6 (cor herdada), §9, §10 (o molde de seção normativa) e o
  histórico de revisões.
- `docs/formato/schema-v1.json` (`$defs/pitchposEvent`) e
  `docs/formato/exemplo-pitchpos.json`.
- [`G04a`](G04a-especificacao-pitchpos.md) (como a §10 foi escrita e
  validada).

## Contexto que você precisa

- A §10 é o molde: passos numerados, cada um com a expressão exata, e
  exemplos trabalhados com números de uma fixture real. A §11 segue o
  mesmo formato, com as 7 regras de G07.
- **Figura** (D-SUM-FIGURA = a): em `pitchpos.json`, por evento, `dur`
  (inteiro: `1`, `2`, `4`, `8`, `16`, `32`, `64`… — o denominador da
  figura; breve e longa ficam fora, sem o campo) e `dots` (opcional, padrão
  `0`). Vale para nota **e** pausa. É a figura **escrita**: quiáltera,
  ligadura e fermata não a mudam. Nota de acorde herda a do acorde.
- **Glifos reservados novos** (§4): `E4E3`-`E4E9` (pausas de semibreve a
  semifusa) e `E1E7` (ponto de aumento). Somados aos 8 de hoje, 16.
- A regra 3 de G07 (linhas suplementares) é escrita aqui como normativa,
  mas **G08c pode mudá-la**: se a varredura achar traço ambíguo, entra o
  plano B de D-SUM-NATIVO e a §11 é corrigida lá. Diga isso no texto do
  passo, não na spec.
- A regra 6 deixa a conta dos **pontos** em aberto: escreva-a a partir de
  `View::DrawDots`/`DrawDotsPart` (`view_element.cpp` L887) e marque na
  §11 que G08c a confere contra o Verovio.
- Nada aqui muda `version` (§9): tudo aditivo.

## O que fazer

1. §2.8: campos `dur` e `dots`, com exemplo (uma semínima pontuada e uma
   colcheia de tercina, mostrando que a tercina continua `dur: 8`).
2. §4: lista de glifos reservados ampliada, com o motivo (§11).
3. **§11 Nota escondida e pausa substituta (normativo)**: as regras 1-7 de
   G07, cada uma com a expressão exata e a fonte dos números; "O que o host
   não deve fazer" (deduzir a figura do timemap; esconder `verse`; apagar o
   grupo `beam` inteiro, que levaria as notas visíveis junto).
4. §11.1: dois exemplos trabalhados com números reais — uma coluna com
   linha suplementar e uma dentro de barra — a preencher com a fixture do
   hino que G08c põe no corpus (deixe o esqueleto e uma nota apontando).
5. `schema-v1.json` e `exemplo-pitchpos.json` com os campos novos.
6. Histórico de revisões: linha de G08a.

## Fora de escopo

- C++ (G08b), referência e vetores (G08c).
- Quais colunas somem e quando: é do host.
- Cor, piscar, revelar: parâmetros do host, não do formato.

## Critérios de aceite

1. D-SUM-FIGURA registrada como resolvida na tabela de decisões do
   `README.md` do plano, com a data e a opção.
2. A §11 cobre as 7 regras de G07 sem depender de nenhuma leitura fora da
   spec (um leitor só com a spec consegue implementar).
3. `schema-v1.json` valida `exemplo-pitchpos.json` com os campos novos e
   continua validando um `pitchpos.json` antigo (sem `dur`).
4. Nenhuma frase da spec diz que o host "deduz" algo que o `.vsb` traz.

## Notas de execução

_(preencher ao executar)_
