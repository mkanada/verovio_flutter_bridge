# R06 — Varredura do corpus e relatório de paridade

**Depende de:** R03, R04, R05, S06 · **Decisão necessária:** não (mas o
resultado é um portão: sem ele, a fase A não começa)

## Objetivo

Medir a paridade visual no corpus inteiro e provar o requisito nº 1 do
projeto: **mais de 99,9% dos pixels iguais** (isto é, divergência abaixo de
0,1%) na comparação SVG→PNG vs. cena→PNG.

## Ler antes (só isto)

- `../verovio_lottie/docs/plano/relatorio-paridade.md` — o formato do relatório
  a produzir (tabela peça/página/%, médias, categorias de divergência) e os
  números do projeto anterior, que são a linha de base a bater:
  **0,0135% – 0,3946%, média 0,1251%**.
- `../verovio_lottie/compare/scripts/compare-corpus.sh`.

## O que fazer

1. Reescrever `compare/scripts/compare-corpus.sh` para o fluxo de R05,
   gerando `compare/out/corpus/resultado.csv` (peça, página, largura, altura,
   pixels divergentes, %, tamanho do `.vsb`).
2. Rodar o corpus inteiro (10 peças, 34 páginas) com tolerância 32.
3. Escrever `docs/relatorio-paridade.md` com:
   - tabela por peça/página e as médias (mesmo formato do relatório anterior,
     para comparação direta);
   - **categorização** de toda divergência acima do ruído de antialiasing: para
     cada categoria, um exemplo recortado (PNG) e a causa provável;
   - comparação lado a lado com os números do `verovio_lottie`;
   - tamanho dos pacotes (peça, páginas, KB, KB/página).
4. Para cada página **acima de 0,1%**, abrir o diff e classificar a causa. Se a
   causa for corrigível num passo R já existente, corrija lá e remeça — não
   documente como "aceito" sem ter olhado.
5. Guardar as imagens de prova (SVG, cena, diff) de uma amostra em
   `docs/mesa-de-prova/<peça>/` (mesmo padrão do projeto anterior), para
   inspeção humana no GitHub.

## Fora de escopo

- Otimizar tamanho (P01).
- Animação (fase A).

## Critérios de aceite

1. 34/34 páginas processadas sem crash.
2. **Média do corpus < 0,1%** de pixels divergentes (tolerância 32/255) —
   o requisito ">99,9%". Se não bater, o passo **não** está concluído: a fase A
   não começa; identifique a causa dominante e volte ao passo R correspondente.
3. Nenhuma página acima de **0,5%**.
4. Nenhuma divergência estrutural: nenhuma nota/clave/haste em posição errada,
   nenhuma cor errada, nenhum elemento faltando ou sobrando. A verificação é
   visual, sobre os diffs, e o resultado é declarado explicitamente no
   relatório (não deduzido da %).
5. `docs/relatorio-paridade.md` existe, com tabela completa, médias, categorias
   e a comparação com o `verovio_lottie`.
6. O CSV bruto está em `compare/out/corpus/resultado.csv` e o relatório cita o
   comando exato que o gerou.

## Notas de execução

(a preencher por quem executar)
