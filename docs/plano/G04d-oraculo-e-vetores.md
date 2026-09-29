# G04d — Referência da fórmula, oráculo Verovio e vetores de teste

**Depende de:** G04b, G04c · **Decisão necessária:** não

## Objetivo

Provar, pelo critério visual do projeto, que a fórmula da §10 (G04a) põe a
fantasma **onde o Verovio desenharia aquela nota**; fechar os valores
provisórios da §10 (folga do acidente); e entregar ao `zywny` vetores de
teste (entrada → saída esperada) para a implementação Dart bater número a
número com a referência.

## Ler antes (só isto)

- [`G03`](G03-visao-geral-nota-fantasma.md) inteiro.
- `docs/formato/especificacao-v1.md` §2.8, §5.1 (campos de pauta) e §10.
- `compare/scripts/verify-midi-json.py` e `compare/scripts/repeat-order.py`
  (estilo dos scripts Python do projeto).

## Contexto que você precisa

- **O oráculo.** Para um alvo (nota esperada `E`, tecla `k`), a fórmula
  diz: pauta, `loc`, grafia (`pname`, `oct`, alteração), se há acidente e
  qual, e quantas linhas suplementares. Uma **cópia MEI** da partitura com
  `E` trocada por essa grafia (com `@accid` quando a fórmula manda
  desenhar acidente, senão `@accid.ges`) é renderizada pelo próprio
  Verovio; a cabeça de `E` na cena da cópia tem de cair no `loc` previsto,
  com o acidente previsto e o mesmo número de linhas suplementares.
- **Armadilha 1 — o layout se mexe.** Trocar uma nota por outra longe pode
  mudar o espaçamento entre pautas (o Verovio afasta as pautas por causa
  das linhas suplementares) e o x (o acidente ocupa espaço). Compare `loc`
  medido contra as linhas **da própria cópia** (campo `lines` de G04b),
  nunca o y absoluto da original. O x não é testável pelo oráculo — por
  decisão, a fantasma fica no x da nota esperada.
- **Armadilha 2 — acidentes se influenciam.** Duas trocas no mesmo
  compasso e pauta mudam o "em vigor" uma da outra. Para renderizar menos,
  junte várias trocas numa cópia só, mas **no máximo uma por compasso e
  pauta**.
- **MusicXML**: converta antes para MEI com o próprio Verovio (`-t mei`,
  `--xml-id-seed 42`) e trabalhe sempre sobre o MEI, para os ids baterem.
- **O que o oráculo não cobre**: a regra de alcance (8va/15ma é invenção
  do plano, não do Verovio — nos casos além de 4 linhas, confira o `loc`
  **antes** do deslocamento de oitava), o deslocamento de colisão e a
  escolha da pauta num acorde entre duas pautas. Esses entram só nos
  vetores, com casos escritos à mão.

## O que fazer

1. `compare/scripts/ghost_ref.py`: implementação de referência da §10,
   lendo um `.vsb` (cena + `pitchpos.json`); função `ghost(doc, event_ids,
   keys) → lista de fantasmas` com pauta (id do nó `staff`), `loc`, x, y,
   glifo e posição do acidente, linhas suplementares, marcador de oitava.
2. `compare/scripts/ghost_oracle.py`: sorteia alvos (semente fixa) no
   corpus + `corpus/fantasma/`, com teclas a ±1, ±2, ±3, ±12 semitons e
   uma além de 4 linhas suplementares; monta as cópias MEI, renderiza e
   compara; CSV em `compare/out/g04d/`.
3. Medir, nas cópias com acidente, a folga entre a borda direita do
   acidente e a borda esquerda da cabeça (mediana por tamanho de pauta) e
   fechar esse valor na §10.
4. Vetores: `docs/formato/fantasma/vetores.json` + os `.vsb` pequenos que
   eles usam (das partituras de `corpus/fantasma/` e de 1-2 peças do
   corpus), cobrindo: cada regra da §10, cada decisão de G03, pausa,
   cross-staff, acorde entre duas pautas, colisão (mesmo `loc` e segunda),
   duas fantasmas em segunda, 8va, 15mb, tom sem armadura (acima/abaixo),
   armadura com ♯ e com ♭, bequadro necessário, acidente já em vigor.

## Fora de escopo

- Implementação Dart e pintura (G05/`zywny`). Cor/fade/tempo na tela.

## Critérios de aceite

1. Oráculo: pelo menos 2 000 alvos, **100%** de acerto em `loc`, acidente
   (presença e glifo) e número de linhas suplementares. Cada divergência é
   corrigida (na fórmula, na especificação ou no exportador) ou explicada
   e registrada como limitação aceita pelo usuário.
2. Folga do acidente fechada na §10, com o número medido.
3. `ghost_ref.py` passa em todos os vetores de `vetores.json` (auto-teste
   `python3 compare/scripts/ghost_ref.py --self-test`).
4. Tempo total do oráculo e número de cópias renderizadas registrados.

## Notas de execução

_(vazio)_
