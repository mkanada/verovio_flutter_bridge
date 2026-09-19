# R06a — Varredura do corpus: CSV das 34 páginas

**Depende de:** R05b, R05c, S06 · **Decisão necessária:** não

## Objetivo

Rodar a comparação nas 34 páginas do corpus e produzir o dado bruto — sem
interpretar, sem corrigir nada ainda. O julgamento é de R06b; o relatório é
de R06c.

## Ler antes (só isto)

- `compare/scripts/compare-corpus.sh` (vindo do projeto anterior, precisa ser
  reescrito para o fluxo de R05b).
- Notas de execução de R05b (a linha de estatística em formato estável).

## Contexto que você precisa (não vá procurar, está aqui)

O corpus e o tamanho de cada peça (medido em S08, `compare/out/s08/`):

| Peça | Páginas | `.vsb` (bytes) | Runs de texto | Usos de glifo |
| --- | ---: | ---: | ---: | ---: |
| Chopin Nocturne Op.9 No.1 | 7 | 472 703 | 89 | 2 665 |
| Clair de Lune (Debussy) | 5 | 383 502 | 88 | 2 458 |
| Chopin Étude Op.10 No.9 | 4 | 288 443 | 64 | 1 792 |
| Chopin Mazurka Op.6 No.1 | 3 | 223 137 | 34 | 1 434 |
| Grieg Butterfly Op.43 No.1 | 3 | 219 454 | 23 | 1 594 |
| Maple Leaf Rag (Joplin) | 3 | 314 700 | 46 | 2 045 |
| Scarlatti Sonata in C major | 3 | 170 786 | 21 | 1 064 |
| Grieg Little bird Op.43 No.4 | 2 | 140 433 | 12 | 1 109 |
| Prelúdio BWV 846 | 2 | 146 141 | 19 | 835 |
| Gymnopédie No.1 (Satie) | 2 | 91 253 | 21 | 417 |

**Total: 34 páginas.** Uma varredura que produza 33 ou 35 linhas está errada.

Outros fatos úteis:

- Todas as peças geram `timemap.json` no pacote.
- Tolerância sempre **32/255 por canal**.
- Tempo: cada página passa por Verovio (2×), `resvg` e Flutter; no projeto
  anterior a varredura inteira levava alguns minutos. Se estiver levando
  muito mais, provavelmente você está regerando o `.vsb` por página em vez de
  uma vez por peça.
- A linha de base do projeto anterior, para comparação direta:
  **0,0135% – 0,3946%, média 0,1251%**.

## O que fazer

1. Reescrever `compare/scripts/compare-corpus.sh` chamando o
   `compare-page.sh` de R05b por página e agregando a linha estável em
   `compare/out/corpus/resultado.csv`, com cabeçalho:

   ```
   peca;pagina;largura;altura;divergentes;total;pct;bytes_vsb
   ```

2. Rodar o corpus inteiro e guardar **todas** as saídas (SVG, `.vsb`, os três
   PNGs por página) em `compare/out/corpus/` — R06b vai precisar delas.
3. Registrar nas notas: comando exato, data, backend, tempo total, versão do
   Verovio (`verovio --version`) e o commit do repositório.

## Fora de escopo

- Investigar ou corrigir divergência (R06b).
- Escrever o relatório (R06c).
- Otimizar tamanho (P01).

## Critérios de aceite

1. **34/34 páginas** processadas sem crash. Se alguma falhar, o passo não
   está concluído: registre a peça, a página e o erro.
2. `compare/out/corpus/resultado.csv` existe, com 34 linhas de dados mais o
   cabeçalho, e todas as colunas preenchidas.
3. Os três PNGs de cada página estão em `compare/out/corpus/`.
4. A varredura é reproduzível: rodar de novo produz o mesmo CSV (as
   percentagens idênticas; o tempo, não).
5. Nas notas: comando, data, backend, tempo total, versão e commit.

## Notas de execução

(a preencher por quem executar)
