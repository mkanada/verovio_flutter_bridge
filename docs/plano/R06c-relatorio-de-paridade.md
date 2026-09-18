# R06c — Relatório de paridade e mesa de prova (portão da fase A)

**Depende de:** R06b · **Decisão necessária:** não (mas o resultado é um
portão: sem ele, a fase A não começa)

## Objetivo

Declarar, por escrito e com evidência, que o requisito nº 1 do projeto está
atendido: **mais de 99,9% dos pixels iguais** ao SVG do Verovio. É o
documento que o usuário vai ler para decidir se o projeto está de pé.

## Ler antes (só isto)

- `../verovio_lottie/docs/plano/relatorio-paridade.md` — o formato a imitar
  (tabela peça/página/%, médias, categorias, comparação) e os números da
  linha de base.
- `compare/out/corpus/resultado.csv` e as classificações de R06b.

## Contexto que você precisa (não vá procurar, está aqui)

- Alvo: **média do corpus < 0,1%** e **nenhuma página acima de 0,5%**.
- Linha de base do `verovio_lottie` (mesma tolerância 32/255, mesmo corpus,
  34 páginas): **0,0135% – 0,3946%, média 0,1251%**. O relatório tem que
  comparar lado a lado — é a única forma de mostrar que a mudança de
  arquitetura não custou qualidade visual.
- "Nenhuma divergência estrutural" é uma afirmação **visual**, declarada
  explicitamente: nenhuma nota, clave ou haste em posição errada, nenhuma cor
  errada, nada faltando ou sobrando. Não se deduz da percentagem.
- A mesa de prova do projeto anterior (`../verovio_lottie/docs/mesa-de-prova/`)
  é o padrão de organização: um diretório por peça, com SVG, cena e diff, para
  inspeção humana direto no GitHub.

## O que fazer

1. Escrever `docs/relatorio-paridade.md` com:
   - resumo (páginas processadas, min/max/média, declaração estrutural);
   - tabela por peça e página;
   - médias por peça;
   - **categorias de divergência**, cada uma com recorte de exemplo e causa;
   - comparação lado a lado com os números do `verovio_lottie`;
   - tamanho dos pacotes (peça, páginas, KB, KB/página) — insumo de P01;
   - o comando exato que gerou o CSV, a data, o commit, o backend e as
     versões (Verovio, Flutter, resvg).
2. Guardar a amostra de imagens em `docs/mesa-de-prova/<peça>/`.
3. Atualizar a tabela de passos do [README do plano](README.md) e, se algum
   número desmentir uma afirmação do `CLAUDE.md` ou da especificação,
   corrigir lá também.

## Fora de escopo

- Otimizar tamanho (P01) e animação (fase A).
- Medir desempenho — este relatório é sobre **imagem**, não sobre tempo.

## Critérios de aceite

1. **Média do corpus < 0,1%** de pixels divergentes (tolerância 32/255). Se
   não bater, o passo não está concluído e a fase A **não começa**: volte a
   R06b com a causa dominante.
2. Nenhuma página acima de **0,5%**.
3. Declaração explícita, no relatório, de que não há divergência estrutural,
   com a metodologia da verificação.
4. `docs/relatorio-paridade.md` existe e contém tabela completa, médias,
   categorias com imagem, comparação com o `verovio_lottie` e os comandos.
5. `docs/mesa-de-prova/` com a amostra de imagens.
6. O CSV bruto está em `compare/out/corpus/resultado.csv` e o relatório cita
   o comando que o gerou.

## Notas de execução

(a preencher por quem executar)
