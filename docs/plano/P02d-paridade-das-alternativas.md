# P02d — Referência SVG e paridade das páginas alternativas

**Depende de:** P02c, P03a (o `compare` lê o `.vsb` pelo `score_bridge`) ·
**Decisão necessária:** não

## Objetivo

Provar que cada página alternativa desenhada pelo Flutter bate com o SVG do
Verovio da **mesma** seleção em mais de 99,99% dos pixels. É o requisito
inegociável 1 do `CLAUDE.md`, agora para as páginas novas.

## Ler antes (só isto)

- `compare/scripts/compare-page.sh` e `compare/scripts/compare-corpus.sh`.
- `compare/lib/main.dart` (comando `scene-to-png`, `--page N`).
- `verovio/tools/main.cpp` (tratamento de opções longas e o ramo `svg`).

## Contexto que você precisa (não vá procurar, está aqui)

- A CLI do Verovio não tem como pedir uma seleção. Para gerar a referência,
  acrescente **na CLI** (só `tools/main.cpp`, nada em `View`/DCs) uma opção
  `--select-from <measure-id>` que, depois de carregar, chama
  `Select({"start": id, "end": <último compasso>})` + `RedoLayout()`. Com
  ela, `-t svg -a` gera as páginas da sequência. **Tem que ser o mesmo
  caminho** que o exportador usa em P02c: se o C++ de P02c tiver um helper,
  reuse-o.
- A referência usa as mesmas opções do `.vsb` (P01c): `--header none
  --footer none --no-instrument-labels`.
- `scene-to-png` desenha `scene.pages[N]`. Acrescente
  `--alternate <start-id>` (ou `--alternate-index K`) para desenhar
  `alternates.sequences[K].pages[N]`. O `compare` lê o `.vsb` pelo
  `score_bridge` (`compare/lib/src/scene_to_png.dart`), e por isso este passo
  vem depois de P03a: use `VsbDocument.alternates` e o `PageRef` de lá.

## O que fazer

1. `--select-from` na CLI (documentado no `-h`).
2. `scene-to-png --alternate ...`.
3. `compare-page.sh`/`compare-corpus.sh`: um modo que, além das páginas
   normais, varre todas as páginas de todas as sequências alternativas de
   cada peça (nomes de saída `<peça>-alt<K>-p<N>-*.png`).
4. Rode a varredura inteira e registre em `docs/relatorio-paridade.md`
   (seção nova, datada).

## Fora de escopo

- Corrigir divergências de desenho que não sejam específicas das
  alternativas (se aparecerem, registre e pare).

## Critérios de aceite

1. Todas as páginas alternativas do corpus acima de **99,99%** (tolerância
   128/255). Tabela por página nas notas.
2. A média das alternativas é comparável à das páginas normais de P01c. Uma
   página acima de 0,01% de divergência precisa de explicação com imagem de
   diff.
3. `-t svg` sem `--select-from`: byte-idêntico ao de antes do passo.
4. Build sem avisos novos; `flutter analyze` limpo em `compare/`.

## Notas de execução

_(preencher)_
