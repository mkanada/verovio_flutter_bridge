# Relatório de páginas alternativas — custo de tamanho e tempo

**Data:** 2026-09-22 · **Passo:** P05 (portão da fase P).

Este relatório existe só para dar ao usuário os números que a D-BIN
("vale trocar o JSON por um encoding binário?") depende — **nenhuma
decisão foi tomada nem otimização foi feita aqui** (CLAUDE.md: "Encoding
binário só entra se o uso real no app `zywny` mostrar necessidade —
decisão do usuário, não decida sozinho").

## Por peça (as 10 do corpus)

Gerado com `verovio <peça> -t vsb --xml-id-seed 42` (com alternativas, o
padrão) e o mesmo comando + `--no-vsb-alternates` (sem), medido com `date
+%s%N` ao redor de cada chamada — uma execução só, não é média de várias
(o objetivo é ordem de grandeza, não medir jitter do processo).

| Peça | Páginas normais | Sequências | Páginas alternativas | `.vsb` sem alt. | `.vsb` com alt. | Δ tamanho | Geração sem alt. | Geração com alt. | Δ tempo |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Chopin Étude Op.10 No.9 | 4 | 0 | 0 | 168 595 B | 168 595 B | +0% | 394 ms | 411 ms | +4% |
| Chopin Mazurka Op.6 No.1 | 3 | 1 | 2 | 131 037 B | 217 476 B | +66% | 355 ms | 581 ms | +64% |
| Grieg Butterfly Op.43 No.1 | 3 | 0 | 0 | 127 059 B | 127 059 B | +0% | 288 ms | 284 ms | −1% |
| Grieg Little bird Op.43 No.4 | 2 | 1 | 2 | 85 830 B | 142 427 B | +66% | 205 ms | 380 ms | +85% |
| Scarlatti Sonata in C | 3 | 0 | 0 | 100 847 B | 100 847 B | +0% | 228 ms | 239 ms | +5% |
| Chopin Nocturne Op.9 No.1 | 7 | 0 | 0 | 266 993 B | 266 993 B | +0% | 705 ms | 713 ms | +1% |
| Clair de Lune (Debussy) | 5 | 0 | 0 | 247 822 B | 247 822 B | +0% | 772 ms | 756 ms | −2% |
| Gymnopédie (Satie) | 2 | 1 | 1 | 49 371 B | 56 911 B | +15% | 118 ms | 169 ms | +43% |
| **Maple Leaf Rag (Joplin)** | 3 | **8** | **13** | 188 458 B | 813 803 B | **+332%** | 521 ms | 1 978 ms | **+280%** |
| Prelude I BWV 846 | 2 | 0 | 0 | 86 684 B | 86 684 B | +0% | 195 ms | 215 ms | +10% |

Seis das dez peças não têm sequência alternativa nenhuma (todo ponto de
chegada de salto já é o 1º compasso de alguma página normal, P02b) — custo
zero, com ou sem `--no-vsb-alternates`. Nas quatro que têm, o custo escala
com o **número de sequências**, não com o tamanho da peça: a Maple Leaf
Rag (8 sequências, a mais repetitiva do corpus) tripla de tamanho e
quadruplica o tempo de geração; Mazurka e Little bird (1 sequência, 2
páginas cada) custam ~65% a mais; Gymnopédie (1 sequência, 1 página só)
custa 15%. Cada sequência renderiza do zero, do compasso de chegada até o
**fim da peça** (D-ALT-EXTENSAO) — uma peça com o ponto de chegada bem no
início paga o preço de desenhar quase a peça inteira de novo, uma vez por
sequência.

## Tempo de parse no Dart (`VsbDocument`)

`alternates` é preguiçoso desde P03a: `VsbDocument.fromBytes` sozinho não
paga o custo (`semAlt`); só a primeira leitura de `document.alternates`
monta a árvore de página das sequências (`comAlt`). Medido com o mesmo
método de `tool/measure_parse_time.dart` (3 execuções, mediana), sobre os
`.vsb` **com** alternativas de `test/fixtures/repeticoes/` (todos os 23,
`--xml-id-seed 42`):

| Peça | Bytes | Parse sem tocar `.alternates` | Parse tocando `.alternates` | Δ |
| --- | --- | --- | --- | --- |
| Chopin Nocturne Op.9 No.1 | 266 993 | 113,00 ms | 121,56 ms | +8% |
| Chopin Étude Op.10 No.9 | 168 595 | 92,18 ms | 85,08 ms | −8%¹ |
| Chopin Mazurka Op.6 No.1 | 217 476 | 59,67 ms | 104,29 ms | +75% |
| Clair de Lune (Debussy) | 247 822 | 121,88 ms | 119,49 ms | −2%¹ |
| Gymnopédie (Satie) | 56 911 | 18,28 ms | 22,25 ms | +22% |
| Grieg Butterfly Op.43 No.1 | 127 059 | 57,68 ms | 54,86 ms | −5%¹ |
| Grieg Little bird Op.43 No.4 | 142 427 | 33,71 ms | 71,65 ms | +113% |
| **Maple Leaf Rag (Joplin)** | 813 803 | 93,80 ms | **424,94 ms** | **+353%** |
| Prelude I BWV 846 | 86 684 | 32,88 ms | 39,62 ms | +21% |
| Scarlatti Sonata in C | 100 847 | 53,42 ms | 47,88 ms | −6%¹ |

¹ Sem sequência alternativa nenhuma: a diferença é ruído de medição (3
execuções, `Stopwatch` de processo), não custo real — `alternates` fica
`[]` sem tocar disco nem JSON (`parser.dart`, `loadAlternates` devolve
`const []` direto quando `manifest.files.alternates` é nulo).

A Maple Leaf Rag (8 sequências, o pior caso do corpus) confirma o 4,6× já
medido em P03a (410 ms vs. 89 ms, num arquivo menor, sem os padrões de
D-VSB-PADRAO) — aqui 4,5× (425 ms vs. 94 ms), mesma ordem de grandeza. Um
host que só precisa saber "há alternativas?" sem montar a geometria delas
ainda não tem essa consulta mais barata (`alternates.isNotEmpty` já monta
tudo, hoje) — não implementado porque nenhum passo pediu.

## Conclusão (sem decisão)

- Peças sem repetição, ou com pontos de chegada que já caem no início de
  uma página normal: **custo zero**, sempre.
- Peças com repetição "de verdade" (poucas sequências, poucas páginas por
  sequência): custo de dezenas de KB e dezenas/poucas centenas de ms —
  parece aceitável para gerar no aparelho (D-RUNTIME), mesmo em um
  dispositivo bem mais lento que o desta medição.
- O pior caso do corpus (Maple Leaf Rag, 8 sequências) mais que triplica o
  tamanho do pacote e o tempo de geração/parse. Se o `zywny` tiver peças
  com **muito mais** repetição que o corpus (rondós com refrão longo,
  variações), o custo pode crescer proporcionalmente ao número de saltos
  não-triviais — **é esse o número que decide D-BIN**, e só o uso real no
  `zywny` (peças de verdade, aparelho de verdade) pode medir.
