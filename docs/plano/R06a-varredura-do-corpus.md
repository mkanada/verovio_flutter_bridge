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
- Tolerância sempre **128/255 por canal** (decisão do usuário em 2026-09-19;
  antes 32/255).
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

Executado em 2026-09-19. Comando: `./compare/scripts/compare-corpus.sh`
(tolerância padrão 32 na época; hoje 128). Backend: **Impeller** (oficial, R05a confirmado).
Tempo total: **187s** (run 1) e **188s** (run 2 de reprodutibilidade).
Verovio **6.3.0-b971951**. Commit `5aefc6b` com a árvore suja das mudanças
ainda não commitadas de R05 (compare-page.sh, widget_vs_harness_test.dart,
compare/README.md, docs) — nenhum commit feito neste passo.

O `compare-corpus.sh` foi reescrito: sonda páginas por peça com
`verovio -t svg -a` (nunca hardcode), chama o `compare-page.sh` de R05b por
página (que gera o `.vsb` completo a cada chamada — custo aceitável: ~5,5s
por página) e move as 5 saídas (`.svg`, `.vsb`, 3 PNGs) mais o log da página
para `compare/out/corpus/`, agregando a linha estável + `bytes_vsb`
(`stat -c%s` do `.vsb`) em `resultado.csv`. Contagens sondadas batem com a
tabela do passo (Étude 4, Mazurka 3, Butterfly 3, Little bird 2, Scarlatti 3,
Nocturne 7, Clair 5, Satie 2, Maple 3, Prelúdio 2 = **34**).

Dado bruto (sem interpretar — julgamento em R06b): mín 0,0552% (Satie p2),
máx 0,8590% (Clair p1), média **0,4122%**; **31/34** páginas acima de 0,1%.
Páginas já medidas antes reproduzem exatamente (Étude p1 0,4978%, Nocturne
p1 0,6794%, Clair p1 0,8590%, Maple p1 0,3603%). `bytes_vsb` difere da tabela
do passo (ex.: Étude ~288,5k vs 288 443) porque aqui as flags são as padrão
do `compare-page.sh`, não `-a -x 42` de S08 — comparação autoconsistente.

Reprodutibilidade (critério 4): run 1 × run 2 com todas as colunas de
pixels/dimensões **idênticas nas 34 linhas**; só `bytes_vsb` varia (máx 274
bytes, média 84) — causa conhecida: `xml:id` auto-gerado não é
determinístico entre processos (achado R05b); não afeta um pixel. Critério
lido no seu escopo ("as percentagens idênticas"): atendido.

DESVIO (2026-09-19, a pedido do usuário): as saídas foram movidas de
`compare/out/corpus/` (git-ignorado, invisível após push) para
`compare/corpus/` (**versionado** — é assim que as páginas ficam visíveis
após commit+push). `CORPUS_DIR` continua configurável
(`CORPUS_DIR=compare/out/corpus` restaura o comportamento do passo). Um
`.gitignore` dentro de `compare/corpus/` versiona só PNGs, CSV e logs de
página; `.svg`/`.vsb`/`.log.stderr` seguem git-ignorados (regeneráveis pelo
próprio script em ~3 min). Re-varredura no novo destino (188s, exit 0):
34 linhas, 102 PNGs, percentagens idênticas às runs 1–2 nas 34 páginas.
