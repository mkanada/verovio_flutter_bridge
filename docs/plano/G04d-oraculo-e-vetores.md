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

Concluído em 2026-09-29. `compare/scripts/ghost_ref.py` (referência da §10 +
`--self-test`), `compare/scripts/ghost_oracle.py` (oráculo), `compare/scripts/
g04d-make-vectors.py` (gera os vetores) e `docs/formato/fantasma/` (`vetores.json`,
26 casos, e os 9 `.vsb` que eles usam, 168 KB no total).

1. **Oráculo, `--targets 2400 --seed 42`: 2 400 alvos, 0 divergências**
   (`loc`, glifo do acidente/ausência e nº de linhas suplementares), 181 cópias
   MEI renderizadas, 10 peças do corpus + 8 de `corpus/fantasma/` (todas as
   notas de `f0*` com 4 deltas cada; o resto sorteado), deltas ±1/±2/±3/±12
   e "far" (tecla 21 ou 108: 203 alvos); 912 com acidente previsto, 1 488 sem;
   contagens previstas de 0 a 16 linhas. **Sabotagem confirmada**: trocar
   `(pname − 1)` por `pname` na fórmula → 236/236 divergências. Duas correções
   de **medição** no caminho (a fórmula não mudou): as linhas suplementares
   de *outras* notas da coluna eram contadas, e notas `visible="false"`
   (o Verovio não desenha nem as suas linhas) entravam no sorteio.
   CSVs: `compare/out/g04d/swap.csv` e `self-divergencias.csv`.
   Limite honesto do oráculo: o Verovio desenha o acidente que se escreve,
   então "acidente previsto = acidente medido" só prova que a cópia foi
   escrita como previsto; a **necessidade** do acidente é provada pelo teste
   `self`: para 9 039 notas sem acidente desenhado, `alt == acc ?? key ?? 0`
   em 8 566; as 473 restantes são dados de origem (457 do Étude, sem
   `key.sig` na `<scoreDef>`; 16 em quatro peças, acidentes estendidos a
   outras oitavas pelo importador) — ver §2.8. Para as 1 087 notas com acidente
   desenhado, o som bate com o glifo em todas (0 exceções), e a fórmula
   com a tecla que a própria nota soa nunca desenha acidente diferente do
   em vigor (0 exceções).
2. **Folga do acidente fechada em `0,5·unit`** (§10): mediana 0,4996 em 1 085
   acidentes (`unit` 90) e 0,4996 com `--unit` 60 e 120 no Satie (mín. 0,491;
   máx. 3,10, colunas de acidentes empilhados). Não havia outro tamanho de
   pauta no corpus.
3. `python3 compare/scripts/ghost_ref.py --self-test`: 26 casos, 0
   divergências. Os resumos dos vetores são contas **feitas à mão** (com a
   conta no campo `conta`); o gerador para se um não bater com a referência —
   e parou duas vezes, ambas erro de conta minha (esqueci o `co`; contei uma
   linha suplementar dentro da pauta), não da referência.
4. Tempo do oráculo completo (18 peças, 2 400 alvos, 181 cópias, 4 processos):
   17 s.

Valores da §10 que **não** têm oráculo (o Verovio não desenha 8va de fantasma):
deslocamento por oitava, posição do marcador (`−3·unit`/`+5·unit`), colisão e
escolha de pauta — cobertos só pelos vetores, e sinalizados como convenção.
