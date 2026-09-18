# P01a — Medições: tamanho, parse, compilação e memória

**Depende de:** R06c, A02c · **Decisão necessária:** não (a decisão é P01b)

## Objetivo

Produzir a tabela de custos do formato com o pipeline inteiro funcionando —
sem decidir nada ainda. O projeto anterior travou meses num passo de tamanho
porque tentou decidir antes de medir; aqui medir é um passo separado de
propósito.

## Ler antes (só isto)

- Notas de execução de S07 (tamanhos por peça), R01 (tempo de parse) e
  A01c/A02c (compilação de `Picture` e repaint).
- `score_bridge/tool/measure_parse_time.dart` (R01) — a ferramenta já existe.

## Contexto que você precisa (não vá procurar, está aqui)

Números já medidos, que esta tabela precisa **atualizar**, não redescobrir
(R01, `flutter test`, debug/JIT — não são números de release):

| Peça | `.vsb` (bytes) | Parse, mediana (ms) |
| --- | ---: | ---: |
| Gymnopédie No.1 | 90 837 | 29,1 |
| Grieg Little bird | 139 008 | 51,6 |
| Prelúdio BWV 846 | 145 958 | 45,5 |
| Scarlatti Sonata | 169 399 | 75,2 |
| Grieg Butterfly | 218 336 | 86,0 |
| Chopin Mazurka | 221 367 | 89,5 |
| Maple Leaf Rag | 310 849 | 106,9 |
| Chopin Étude | 286 268 | 127,8 |
| Clair de Lune | 381 747 | 150,4 |
| Chopin Nocturne | 471 450 | 141,6 |

O tempo **não** é proporcional aos bytes do `.vsb`: o parse descompacta o zip
e lê 3 JSONs, então depende também da forma da árvore. Meça em **release/AOT**
desta vez, porque é o número que o app vai ter.

Composição típica do conteúdo (corpus): 26 469 formas `p`, 15 413 usos de
glifo, 1 401 `r`, 911 `e`, 417 runs de texto, 50 544 nós — e apenas 16 a 37
glifos distintos por peça. O dicionário já removeu a maior repetição; o que
sobra é sobretudo geometria de `p` e a estrutura da árvore.

**O corpus não representa o pior caso**: são peças de 5 a 16 compassos, 2 a 7
páginas. Uma peça de 20+ páginas é obrigatória aqui — sem ela, qualquer
conclusão sobre tamanho e tempo de abertura é chute.

## O que fazer

1. Para as 10 peças do corpus, medir e tabular:
   - tamanho do `.vsb`, do `scene.json` cru e do `glyphs.json` cru;
   - proporção glifos/cena/timemap dentro do pacote;
   - tempo de parse no Dart, **release/AOT**, mediana de 5, em desktop **e**
     num dispositivo Android (se não houver aparelho, registre que faltou);
   - tempo de compilação dos `Picture` por página (A01c);
   - memória residente do documento carregado (`ProcessInfo.currentRss` antes
     e depois).
2. Repetir tudo para **uma peça grande fora do corpus** (20+ páginas, MEI de
   domínio público). Registre de onde ela veio e como foi gerada — ela vira
   parte do material de teste do projeto.
3. Escrever `docs/medicoes.md` com a tabela completa e, para cada número, o
   comando que o produziu.

## Fora de escopo

- Decidir qualquer coisa sobre encoding (P01b).
- Implementar otimização (P01b, e só com decisão registrada).
- Otimizar render (P03).

## Critérios de aceite

1. `docs/medicoes.md` existe, com as 10 peças **mais** a peça grande, e todas
   as colunas preenchidas (ou explicitamente marcadas como não medidas, com o
   motivo).
2. Cada número tem o comando que o gerou, e o documento diz a máquina, o
   backend, o modo de build (release/AOT) e as versões.
3. Os tempos de parse foram medidos em release, e a diferença para os números
   de debug de R01 está comentada.
4. A peça grande está descrita (origem, compassos, páginas) e o arquivo está
   acessível para os próximos passos.
5. Se algum número contradisser uma afirmação do plano ou do `CLAUDE.md`, a
   contradição está apontada explicitamente.

## Notas de execução

(a preencher por quem executar)
