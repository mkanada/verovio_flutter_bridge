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

_(preencher)_
