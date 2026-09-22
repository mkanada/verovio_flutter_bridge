# R06c — Relatório de paridade e mesa de prova (portão da fase A)

**Depende de:** R06b · **Decisão necessária:** não (mas o resultado é um
portão: sem ele, a fase A não começa)

## Objetivo

Declarar, por escrito e com evidência, que o requisito nº 1 do projeto está
atendido: **mais de 99,99% dos pixels iguais** ao SVG do Verovio (tolerância
128/255 por canal, decisão do usuário em 2026-09-19). É o
documento que o usuário vai ler para decidir se o projeto está de pé.

## Ler antes (só isto)

- `../verovio_lottie/docs/plano/relatorio-paridade.md` — o formato a imitar
  (tabela peça/página/%, médias, categorias, comparação) e os números da
  linha de base.
- `compare/corpus/resultado.csv` e as classificações de R06b. (Nota: este
  arquivo e o critério de aceite 6 abaixo ainda citavam
  `compare/out/corpus/resultado.csv` — caminho desatualizado desde o desvio
  já registrado em R06a, que passou a versionar as saídas em
  `compare/corpus/`.)

## Contexto que você precisa (não vá procurar, está aqui)

- Alvo: **média do corpus < 0,01%** e **nenhuma página acima de 0,05%**.
- Linha de base do `verovio_lottie` (tolerância 32/255, mesmo corpus,
  34 páginas): **0,0135% – 0,3946%, média 0,1251%** — medida na tolerância
  antiga, **não diretamente comparável** aos números a 128/255; o relatório
  mostra as duas lado a lado com a ressalva. É a única forma de mostrar que
  a mudança de arquitetura não custou qualidade visual.
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
   - tamanho dos pacotes (peça, páginas, KB, KB/página) — insumo para uma eventual decisão de encoding;
   - o comando exato que gerou o CSV, a data, o commit, o backend e as
     versões (Verovio, Flutter, resvg).
2. Guardar a amostra de imagens em `docs/mesa-de-prova/<peça>/`.
3. Atualizar a tabela de passos do [README do plano](README.md) e, se algum
   número desmentir uma afirmação do `CLAUDE.md` ou da especificação,
   corrigir lá também.

## Fora de escopo

- Otimizar tamanho e animação (fase A).
- Medir desempenho — este relatório é sobre **imagem**, não sobre tempo.

## Critérios de aceite

1. **Média do corpus < 0,01%** de pixels divergentes (tolerância 128/255,
   percentuais com 6 casas). Se
   não bater, o passo não está concluído e a fase A **não começa**: volte a
   R06b com a causa dominante.
2. Nenhuma página acima de **0,05%**.
3. Declaração explícita, no relatório, de que não há divergência estrutural,
   com a metodologia da verificação.
4. `docs/relatorio-paridade.md` existe e contém tabela completa, médias,
   categorias com imagem, comparação com o `verovio_lottie` e os comandos.
5. `docs/mesa-de-prova/` com a amostra de imagens.
6. O CSV bruto está em `compare/corpus/resultado.csv` (caminho corrigido
   acima — desvio já registrado em R06a) e o relatório cita o comando que o
   gerou.

## Notas de execução

**Passo concluído (2026-09-20).** `docs/relatorio-paridade.md` escrito a
partir do CSV já versionado da sexta investigação de R06b
(`compare/corpus/resultado.csv`, commit `e81b6e1`) — não foi necessário
refazer a varredura, só recomputar os agregados (`awk`, `LC_NUMERIC=C`) para
conferência independente.

1. Média 0,008456% < 0,01%. ✓
2. Página mais alta: Clair de Lune p1, 0,038624% < 0,05%. ✓
3. Seção "Resumo" do relatório declara ausência de divergência estrutural,
   com a metodologia (inspeção lado a lado + os dois testes de
   deslocamento/luminância de R06b). ✓
4. Relatório escrito com tabela completa (34 páginas), médias por peça,
   5 categorias (4 corrigidas + o piso de AA restante) com recorte de
   exemplo, comparação com o número **final** do `verovio_lottie`
   (0,0135%–0,3946%, média 0,1251%, tolerância 32/255 — não o número
   intermediário de A13, anterior às correções de texto comum daquele
   projeto) e o comando exato. ✓
5. `docs/mesa-de-prova/` criado com amostra curada de 4 páginas (não o
   corpus inteiro — as 34 páginas já estão versionadas em
   `compare/corpus/`, que cumpre o mesmo papel de "visível direto no
   GitHub" que a mesa de prova tinha no projeto anterior; ver
   `docs/mesa-de-prova/README.md` para a justificativa de cada escolha). ✓
6. CSV em `compare/corpus/resultado.csv` (não `compare/out/corpus/`, ver
   correção acima); relatório cita `compare/scripts/compare-corpus.sh 128`.
   ✓

**Portão aberto: fase A liberada para começar (A01a).**
