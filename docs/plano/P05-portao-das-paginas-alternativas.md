# P05 — Portão da fase P: páginas alternativas de ponta a ponta

**Depende de:** P02d, P04c · **Decisão necessária:** não (mas os números do
critério 4 vão para o usuário julgar, ver abaixo)

## Objetivo

Fechar a fase provando, de ponta a ponta (partitura → `.vsb` com
alternativas → `ScoreTimeline`/`ScorePlayer`/`ScoreView`), que o player
mostra a página certa em todo salto, que a paridade continua acima de
99,99%, e que tamanho e tempo de geração são aceitáveis para gerar no
aparelho (D-RUNTIME). Depois, deixar a documentação refletindo o estado novo.

## Ler antes (só isto)

- As "Notas de execução" de P01a a P04c.
- `docs/plano/E05-portao-das-repeticoes.md` (o portão anterior, como
  modelo).

## O que fazer

1. Regenere as 23 fixtures de `score_bridge/test/fixtures/repeticoes/` com
   alternativas (mesmos parâmetros de E05: `-x 42`, `--breaks encoded` em
   r06/r07).
2. `test/paginas_alternativas_test.dart`, sobre as 23:
   - invariantes de P04a (compasso presente na `view`; `view` só muda em
     virada ou salto);
   - todo salto para página diferente com sequência disponível cai com o
     destino como 1º compasso da página exibida;
   - `ScorePlayer` do início ao fim a 4× em `pagedSweep` sem exceção, sem
     destaque no fim, sem `Picture` vazando.
3. `repeticoes_test.dart` (E05) continua verde: a ordem de execução não
   mudou.
4. Varredura de paridade completa (normais + alternativas) e
   `docs/relatorio-paridade.md` atualizado.
5. **Tabela para o usuário** (em `docs/relatorio-paginas-alternativas.md`,
   novo): por peça, páginas normais, sequências, páginas alternativas,
   tamanho do `.vsb` com e sem alternativas, tempo de `RenderToBridgeFile`
   com e sem, e tempo de parse no Dart com e sem. Tamanho é decisão do
   usuário (D-BIN continua dele). **Não otimize sem pedir.**
6. Documentação:
   - README do plano: fase P na tabela de passos (todos `concluído`),
     mapa do código (`PageRef`, `AlternateSequence`, `geometryOf`,
     `showPage`/`displayedPage`, `MeasureInfo.view`, `restViewAt`,
     `bridgealternates.cpp`, `--no-vsb-alternates`, `--select-from`), fatos
     do corpus e decisões;
   - `CLAUDE.md`, em "Decisões registradas": D-ALT, D-ALT-INDICE,
     D-ALT-EXTENSAO, D-VSB-PADRAO, D-ALT-MECANISMO e D-META-TITULO, como
     foram decididas;
   - spec: conferir §2.3 (título) e §2.5 (alternates) contra o que foi
     implementado;
   - `docs/nota-para-zywny-fase-p.md` (novo, curto): chamar
     `setOutputTo('vsb')` **antes** de `loadData` (senão os padrões de
     D-VSB-PADRAO não valem); `displayedPage` × `currentPage`; o
     `useAlternates` do player; o custo medido no item 5.

## Fora de escopo

- Qualquer mudança no `zywny`.
- Encoding binário ou corte de páginas alternativas não usadas (D-ALT-
  EXTENSAO manda ir até o fim; rever é decisão do usuário, com os números do
  item 5).

## Critérios de aceite

1. `paginas_alternativas_test.dart` e `repeticoes_test.dart` verdes.
2. Paridade: todas as páginas (normais e alternativas) acima de 99,99%, com
   média registrada.
3. Tabela do item 5 publicada no relatório.
4. README, `CLAUDE.md`, spec e nota para o `zywny` atualizados; fase P
   marcada `concluído`.
5. `flutter analyze` limpo, `flutter test` verde, build do Verovio sem
   avisos novos.

## Notas de execução

**Fixtures (item 1).** As 23 fixtures de `test/fixtures/repeticoes/`
regeneradas com o mesmo comando de E05/P01c (`--xml-id-seed 42`, `--breaks
encoded` só em r06/r07). Verificado, para as 8 sem sequência alternativa
nenhuma antes, que `scene.json`/`glyphs.json`/`timemap.json` continuam
byte-idênticos ao commit anterior (a única diferença é a string de versão
do `generator` em `manifest.json`); para as que ganharam `alternates.json`
(mesma verificação na Maple Leaf Rag, a maior), idem — só o arquivo novo
muda. **9 das 23** ganharam `alternates.json`: Chopin_Mazurka_Op6_No1 (1
sequência), Grieg_Little_bird_Op43_No4 (1), Erik_Satie_-_Gymnopedie_No.1
(1), Maple_Leaf_Rag_Scott_Joplin (8), r03-casas (1), r04-casas (1),
r05-casa-1-sozinha (1), r09-ds-al-coda (1), r11-varias-sections (1) —
nenhuma das outras 14 (incluindo r06/r07-salto-de-pagina, cujos saltos já
caem no 1º compasso de página normal, por construção da partitura de
teste) tem ponto de chegada que sobreviva à regra de existência de §2.5.

**`test/paginas_alternativas_test.dart` (item 2, critério 1).** 10 testes:
uma pré-condição, os dois invariantes de P04a já usados em
`score_timeline_route_test.dart` (agora repetidos aqui sobre as 23
fixtures — e, diferente de antes de P05, exercitando alternativas de
verdade em 7 delas, não só reduzindo à identidade), um invariante novo
("todo salto que muda de view cai no 1º compasso da página exibida" —
não estava em nenhum teste anterior, porque só fazia sentido depois que
mais de uma fixture tinha alternativa) e a reprodução completa a 4× em
`pagedSweep` das 6 peças com repetição de verdade (mesma lista de E05),
com `PictureStats.live` de volta a 0 no fim. Todos passam.

**`repeticoes_test.dart` (item 3, critério 1).** Continua verde sem
alteração: a ordem de execução (o que este teste compara) não depende de
`alternates.json` nem de qual `view` o player escolhe — só da resolução
de ids e passagens (E02a/E02b), inalterada pela fase P.

**Varredura de paridade completa (item 4, critério 2).**
`CORPUS_DIR=compare/out/p05-parity SWEEP_ALTERNATES=1
compare/scripts/compare-corpus.sh 128` (git-ignorado). **34/34 páginas
normais**, média **0,006402%** — idêntica a P01c, byte a byte (nenhuma
mudança de código no exportador desde então). **18/18 páginas
alternativas**, média **0,006514%** — idêntica a P02d. Nenhuma página
mudou de percentual em nenhum dos dois grupos: esperado, já que nenhum
passo entre P02d e este portão (P03a-P04c) tocou `verovio/src`. Detalhes
em `docs/relatorio-paridade.md`, seção "P05".

**Tabela para o usuário (item 5, critério 3).** `docs/relatorio-paginas-
alternativas.md` (novo): tamanho/tempo de geração (`verovio -t vsb` com e
sem `--no-vsb-alternates`) e tempo de parse no Dart (tocando ou não
`.alternates`, que é preguiçoso desde P03a) para as 10 peças do corpus.
Achado principal: custo **zero** em 6/10 peças (sem sequência
alternativa); nas outras 4, escala com o **número de sequências**, não
com o tamanho da peça — de +15% (Gymnopédie, 1 sequência) a **+330%/+280%
tamanho/tempo** (Maple Leaf Rag, 8 sequências, o pior caso do corpus).
D-BIN continua decisão do usuário; nada foi otimizado.

**Documentação (item 6).**

- README: fase P inteira marcada `concluído` (tabela de passos); "Mapa do
  código" ganhou a linha deste passo (a maioria das entradas de
  `PageRef`/`AlternateSequence`/`geometryOf`/`showPage`/`displayedPage`/
  `MeasureInfo.view`/`restViewAt`/`bridgealternates.cpp`/
  `--no-vsb-alternates`/`--select-from` já tinha sido acrescentada pelos
  passos P02b-P04c, então só faltava referenciar os artefatos deste
  portão); nota no rodapé, ao lado da de "Fase E concluída".
- `CLAUDE.md`, "Decisões registradas": bloco novo "Fase P (páginas
  alternativas), cinco decisões" (D-ALT, D-ALT-INDICE, D-ALT-EXTENSAO,
  D-VSB-PADRAO, D-ALT-MECANISMO, D-META-TITULO) — **não existia nenhuma
  menção à fase P em `CLAUDE.md` antes deste passo** (P00 documentou as
  decisões só em `docs/plano/`, e nenhum passo anterior tinha atualizado
  `CLAUDE.md`; corrigido aqui, como o item 6 pedia).
- `docs/formato/especificacao-v1.md`: §2.3 e §2.5 conferidas contra a
  implementação final — **as duas já estavam exatas** (escritas certas em
  P01a e P02a/P02c respectivamente, sem nenhuma mudança de formato desde
  então); nenhuma edição necessária.
- `docs/nota-para-zywny-fase-p.md` (novo, no formato de
  `nota-para-zywny-fase-e.md`): `setOutputTo('vsb')` antes de `loadData`;
  `displayedPage` × `currentPage`; `useAlternates`; custo medido (item 5),
  com um lembrete de que gerar `.vsb` sem alternativas
  (`--no-vsb-alternates`) ainda não está exposto ao host.

**Achados fora do escopo deste passo, registrados e não corrigidos** (já
citados nas notas de P04c, repetidos aqui porque afetam o portão): o
exemplo de E03b (`docs/exemplos/repeticao/MapleLeafRag/`) documenta dois
saltos que não são mais travessias de página na paginação atual (P01c) —
ficou assim desde antes deste passo, e continua assim.

**Critério 5.** `flutter analyze`: nenhum problema. `flutter test` (suíte
inteira, 305 casos — os 295 de P04c + os 10 novos de
`paginas_alternativas_test.dart`): todos passam. Build do Verovio: nenhum
arquivo de `verovio/src`/`verovio/include` tocado neste passo (só
regeneração de fixtures com o binário já existente), então não há novos
avisos de compilação a checar.
