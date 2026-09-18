# S06 — `Toolkit` + CLI (`-t vsb-json`)

**Depende de:** S05 · **Decisão necessária:** depende de D-NOME (resolvida em S01)

## Objetivo

Expor o exportador pela mesma interface que os outros formatos do Verovio, de
modo que `verovio -t vsb-json partitura.mei -o saida.json` produza a cena de
**todas** as páginas.

## Ler antes (só isto)

- `verovio/src/toolkit.cpp` `RenderToDeviceContext` L1674-L1730 (genérico, já
  existe) e, no repositório antigo, `RenderToLottieAnimation`
  (`../verovio_lottie/verovio/src/toolkit.cpp` L1912+) como modelo de laço de
  páginas.
- `verovio/include/vrv/toolkitdef.h` L13-L37 (`FileFormat`).
- `verovio/src/options.cpp` `SetOutputTo` (busque o símbolo; era ~L1987-L2027).
- `verovio/tools/main.cpp` L284-L292 (validação de formato), L312-L315 (a lista
  que força `breaks: none` — **não** inclua o formato novo aí) e L350-L390 (o
  laço de páginas do SVG).

## O que fazer

1. `FileFormat`: acrescentar `VSB_JSON` (e `VSB`, já usado em S07).
2. `Toolkit`:

   ```cpp
   std::string RenderToBridgeJson();                       // todas as páginas
   bool RenderToBridgeJsonFile(const std::string &filename);
   ```

   O laço é: `BridgeDeviceContext dc; dc.SetResources(&m_doc.GetResources());`
   → para cada página `RenderToDeviceContext(p, &dc)` → `BridgeWriter::WriteSingleJson(...)`.
   O dicionário de glifos é **acumulado entre páginas** (uma peça inteira
   compartilha um dicionário só) — confira que o device context não o zera em
   `StartPage`.
3. `SetOutputTo`: aceitar `"vsb-json"`.
4. `tools/main.cpp`: incluir na lista de formatos válidos e na mensagem de erro;
   escrever o arquivo (aceitar `-o -` para stdout, já que é texto).
5. `-a`/`--all-pages` e `-p`/`--page N`: o formato é naturalmente multi-página;
   `-p N` exporta só aquela página (útil para depurar). Espelhe o comportamento
   dos outros formatos, sem inventar semântica nova.

## Fora de escopo

- Pacote zip e timemap (S07).
- Bindings C/FFI (P02).
- Opções de CLI específicas do formato — **não existem**; a animação toda é do
  lado Flutter. Se aparecer vontade de criar uma, pare e pergunte.

## Critérios de aceite

1. `verovio -h` lista `vsb-json` entre os formatos de `--output-to`.
2. Para as 10 peças do corpus:

   ```sh
   ./verovio/tools/verovio -t vsb-json -a --resource-path verovio/data -o compare/out/$n.json $f
   python3 -m json.tool compare/out/$n.json > /dev/null && echo "OK $n"
   ```

   10/10 `OK`, sem crash, sem aviso no stderr.
3. O nº de páginas no JSON bate com `verovio -t svg -a` (conte os `<svg>` de
   página gerados) para todas as peças.
4. `-p 2` produz um JSON com exatamente uma página, cujo conteúdo é igual ao da
   página de índice 1 do export completo (compare os dois sub-objetos).
5. Um dicionário de glifos único para a peça inteira: exportar uma peça de 4+
   páginas e conferir que `glyphs` tem **menos** entradas que a soma dos
   dicionários por página exportados individualmente (prova de compartilhamento).
6. `LC_ALL=tr_TR.UTF-8 verovio -t vsb-json ...` produz saída idêntica (o mesmo
   teste de locale de S05, agora pela CLI).

## Notas de execução

- 2026-09-17: `FileFormat` ganhou `VSB` e `VSB_JSON` (`toolkitdef.h`); `VSB` fica
  sem uso até S07 (declarado agora porque o passo pediu, sem CLI/`SetOutputTo`
  associado). `Options::SetOutputTo` aceita `"vsb-json"`. `Toolkit` ganhou
  `RenderToBridgeJson(int fromPage = 1, int toPage = -1)` (`toPage < 0` = até a
  última página) e `RenderToBridgeJsonFile(filename, fromPage, toPage)`, nos
  moldes de `RenderToLottieAnimation`/`RenderToLottie` do fork antigo: um
  `BridgeDeviceContext` local, `SetResources` chamado antes do laço (achado de
  S05 - `RenderToDeviceContext` não faz isso sozinho), um `RenderToDeviceContext`
  por página do intervalo, depois `BridgeWriter::WriteSingleJson` sobre todas as
  páginas acumuladas e o dicionário de glifos único do device context (nunca
  resetado em `StartPage`, então acumula sozinho). `generator` gravado como
  `"verovio <versão> / bridge 1"`, igual ao exemplo do `manifest.json` na
  especificação. `main.cpp`: `"vsb-json"` na lista de formatos válidos e na
  mensagem de erro, sem entrar na lista que força `breaks: none`; o branch novo
  usa exatamente o mesmo `from`/`to` que o branch `svg` já calculava a partir de
  `-a`/`-p` (nenhuma semântica nova), mas escreve **um** JSON só (o formato é um
  documento único com `scene.pages`, não um arquivo por página como o SVG).
  `cmake ../cmake && make -j4` limpo, sem avisos novos.
- **Critério 1**: `verovio -h base` lista `"vsb-json"` na ajuda de
  `-t`/`--output-to`.
- **Critério 2**: as 10 peças do corpus (5 `.mei` + 5 `.mxl`) exportadas com
  `-t vsb-json -a`, 10/10 `python3 -m json.tool` válido, exit code 0. `stderr`
  tem só `[Warning]` de parsing de entrada (`@startid`+`@tstamp`, etc.) e a
  linha `Output written to`; confirmado que são os **mesmos avisos, em igual
  quantidade**, que `-t svg -a` já emite para os mesmos arquivos (comparado
  para 3 peças) - não são avisos novos introduzidos pelo exportador.
- **Critério 3**: contagem de páginas do JSON (`len(scene.pages)`) bate com a
  contagem de arquivos `.svg` gerados por `-t svg -a` nas 10 peças (34 páginas
  no total, mesmo número já registrado em S05).
- **Critério 4**: testado com Chopin Etude (4 páginas), mesmo `-x 42` nas duas
  chamadas (necessário para ids auto-gerados baterem entre os dois processos,
  achado de S04/S05). `-p 2` produz `scene.pages` com 1 elemento; comparado
  contra `scene.pages[1]` do export completo (`-a`), os dois sub-objetos são
  idênticos **exceto o campo `"index"`** (`0` no export de 1 página vs. `1` no
  export completo) - esperado e correto: `index` é a posição da página *dentro
  do documento exportado* (`BridgeWriter::WriteScene` usa a posição no array
  `pages` recebido, não um número de página absoluto da peça), então um
  documento de 1 página sempre tem `index: 0`. Ignorando esse campo (que por
  construção não podia bater), o conteúdo é 100% idêntico.
- **Critério 5**: mesma peça (Etude, 4 páginas), dicionário de glifos do export
  completo (`-a`) tem 34 entradas; soma dos dicionários dos 4 exports de página
  única (`-p 1`..`-p 4`, 20+25+26+16) dá 87 - confirma o compartilhamento (34 <
  87).
- **Critério 6**: `LC_ALL=de_DE.utf8` (mesma classe de locale de vírgula
  decimal do teste de S05; `tr_TR.UTF-8` continua não instalado no ambiente)
  contra locale padrão (`C`/`en_US`), mesma peça, mesmo `-x 42`: `cmp` não
  reporta diferença - saída da CLI byte-idêntica.
- Bloqueios: nenhum.
