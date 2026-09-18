# S07 — Pacote `.vsb` (zip) com timemap embutido

**Depende de:** S06 · **Decisão necessária:** não (resolvida em S01)

## Objetivo

Empacotar `manifest.json` + `scene.json` + `glyphs.json` + `timemap.json` num
único arquivo `.vsb`, que é o formato que o app consome.

## Ler antes (só isto)

- `verovio/include/vrv/filereader.h` / `verovio/src/filereader.cpp` —
  `ZipFileWriter` (escrito em A11 do projeto anterior) e a nota do risco 5 do
  [README do plano](README.md) sobre `zip_file.hpp` ser header-only.
- `verovio/src/toolkit.cpp` `RenderToTimemap` (busque o símbolo) e
  `include/vrv/timemap.h`.
- Seção 2 da [especificação](../formato/especificacao-v1.md).

## O que fazer

1. `Toolkit::RenderToBridgeFile(const std::string &filename)`:
   - renderiza todas as páginas com o `BridgeDeviceContext`;
   - grava `manifest.json`, `scene.json`, `glyphs.json`;
   - grava `timemap.json` chamando o caminho de timemap já existente. Se a peça
     não produzir timemap (sem informação rítmica utilizável), **omita o arquivo
     e o campo no manifest** — não grave um timemap vazio.
2. `FileFormat::VSB`, `SetOutputTo("vsb")`, entrada em `tools/main.cpp`.
   Pacote binário: recusar `-o -` com mensagem clara (mesmo padrão que o
   `dotlottie` usava).
3. Compressão: use o padrão do `zip_file.hpp` (deflate). Registre nas notas o
   tamanho antes/depois do zip por peça.

## Fora de escopo

- Ler o `.vsb` no Dart (R01 já lê; aqui só se produz).
- Assinatura, versionamento incremental, delta entre versões.

## Critérios de aceite

1. `verovio -t vsb -a --resource-path verovio/data -o saida.vsb peca.mei` gera
   o arquivo para as 10 peças do corpus.
2. `unzip -t saida.vsb` passa em 10/10.
3. `unzip -p saida.vsb scene.json | python3 -m json.tool > /dev/null` e o mesmo
   para `glyphs.json`, `manifest.json`, `timemap.json` — todos válidos.
4. `manifest.json` bate com o conteúdo: `pageCount` igual ao nº de páginas de
   `scene.json`, e `files` lista exatamente os arquivos presentes no zip.
5. Os ids do `timemap.json` embutido são **os mesmos** do `verovio -t timemap`
   rodado separadamente na mesma peça (compare os dois JSONs; devem ser iguais
   módulo formatação).
6. Tabela de tamanhos (por peça: nº de páginas, `scene.json` cru, `glyphs.json`
   cru, `.vsb` final, KB/página) registrada nas notas de execução — é o insumo
   do gate de P01.

## Notas de execução

- 2026-09-17: `FileFormat::VSB` (já declarado em S06, sem uso) ganhou uso:
  `Options::SetOutputTo` aceita `"vsb"`; `Toolkit::RenderToBridgeFile(filename)`
  renderiza **todas** as páginas (sem `fromPage`/`toPage` — o pacote é sempre o
  documento inteiro, diferente de `RenderToBridgeJsonFile`), grava
  `manifest.json`/`scene.json`/`glyphs.json` num `ZipFileWriter` e, quando o
  resultado de `RenderToTimemap()` é um array JSON não vazio, também
  `timemap.json`. Extraí `Toolkit::RenderPagesToBridge(BridgeDeviceContext&,
  fromPage, toPage)` (privado) do laço que já existia em `RenderToBridgeJson`
  (S06) para as duas funções compartilharem o `SetResources`+laço de
  `RenderToDeviceContext` sem duplicar. `main.cpp`: `"vsb"` na lista de
  formatos e na mensagem de erro; ramo novo recusa `-o -` com `"vsb is a binary
  package and cannot be written to standard output."` (mesmo padrão do
  `dotlottie` do fork anterior, conferido em
  `verovio_lottie/verovio/tools/main.cpp`). `cmake ../cmake && make -j4`
  limpo, sem avisos novos.
- **Achado sobre "sem timemap"**: `RenderToTimemap()` tem **dois** jeitos de
  sinalizar "nada para gravar", não um só. `Doc::ExportTimemap` devolve o
  sentinela `"{}"` (objeto, nunca o formato de um timemap real) só na falha
  total de `CalculateTimemap()` (ex.: `GetPageCount() == 0`). Mas uma peça com
  páginas e **zero** conteúdo rítmico (testado com um MEI mínimo, só
  `scoreDef`+`staffDef`, sem `section`/medida nenhuma) "calcula com sucesso" e
  devolve um array JSON vazio (`Timemap::ToJson` sempre produz um array,
  mesmo sem instantes) — checar só contra `"{}"` deixava esse caso passar e
  gravava um `timemap.json` com `[]`, violando a regra do §2 ("nunca é gravado
  um timemap vazio"). Corrigido fazendo o parse do resultado como
  `jsonxx::Array` e tratando "não fez parse" ou "array vazio" igualmente como
  "sem timemap" (`hasTimemap = timemapArray.parse(timemapJson) &&
  !timemapArray.empty()`); confirmado manualmente com o MEI mínimo acima:
  antes da correção o pacote saía com `timemap.json: []` e `"timemap"` em
  `manifest.files`; depois, nenhum dos dois. Nenhuma peça do corpus real cai
  nesse caso (as 10 têm timemap não vazio), mas o `.vsb` é o formato que o app
  vai consumir — vale blindar contra entradas degeneradas.
- **Critério 1**: `verovio -t vsb -a --resource-path verovio/data -x 42 -o
  saida.vsb peca.mei/.mxl` — 10/10 peças do corpus (5 `.mei` + 5 `.mxl`), exit
  code 0.
- **Critério 2**: `unzip -t` — 10/10 arquivos passam.
- **Critério 3**: `unzip -p ... | python3 -m json.tool` válido para
  `manifest.json`, `scene.json`, `glyphs.json` nas 10 peças e `timemap.json`
  nas 10 (todas as peças do corpus produziram timemap não vazio — o ramo "sem
  timemap" foi exercitado à parte com o MEI mínimo do achado acima). Total
  40/40 arquivos válidos.
- **Critério 4**: para as 10 peças, `manifest.pageCount == len(scene.pages)` e
  o conjunto de membros do zip bate exatamente com `{"manifest.json",
  "scene.json", "glyphs.json"} ∪ ({"timemap.json"} se `"timemap"` está em
  `manifest.files`)`. Soma de páginas: 34 (mesmo número de S05/S06).
- **Critério 5**: comparado `timemap.json` embutido (extraído do `.vsb`, `-x
  42`) contra `verovio -t timemap --resource-path verovio/data -x 42 -o
  saida.json peca.*` rodado à parte, nas 10 peças. **Os ids (`on`/`off`/
  `qstamp`/`tstamp`/`measure`) batem 100% nas 10/10.** O JSON completo bate
  byte-a-byte (via comparação estrutural) em 9/10; a exceção é
  `Erik_Satie_-_Gymnopedie_No.1` (a única peça do corpus com um `<expansion>`
  — repetição/D.C.), onde um valor de `tempo` diverge no último dígito:
  `76.0002` (rodada isolada) vs `76.00019836425781` (embutido no pacote) — a
  representação em float32 de `76.0002` promovida a double, indicando que um
  dos dois caminhos passou por uma conversão `float`. **Achado, não é bug do
  S07:** `Doc::ExpandExpansions()` só expande a repetição *no import* quando o
  formato de saída já é `MIDI`/`TIMEMAP`/`EXPANSIONMAP` (`iomusxml.cpp`/
  `iomei.cpp`); para qualquer outro formato — inclusive `vsb` — a expansão só
  acontece depois, dentro de `Toolkit::SetMidiDoc()`, que nesse caso
  redocumenta a peça via `GetMEI()` + `MEIInput::Import()` (um round-trip por
  texto MEI). Nesse reimport, `Att::StrToDbl` (`verovio/libmei/addons/att.cpp`)
  usa `std::stof` (float, não `std::stod`) para converter qualquer atributo
  `double` do MEI — é aí que a precisão de `midi.bpm="76.0002"` se perde. Isso
  é um bug pré-existente em `Att::StrToDbl` (afeta qualquer atributo `double`
  do MEI, não só tempo), fora do escopo do S07 (que não mexe em
  `View`/`DeviceContext`/parsing de atributo) — registrado aqui para quem for
  cuidar de precisão numérica mais tarde (P01) ou reabrir o assunto. Não afeta
  nenhum `xml:id` endereçável.
- **Critério 6**: tabela de tamanhos (páginas / `scene.json` cru / `glyphs.json`
  cru / `.vsb` final / KB por página):

  | Peça | Pág. | scene.json | glyphs.json | .vsb | KB/pág |
  | --- | ---: | ---: | ---: | ---: | ---: |
  | Chopin_-_Nocturne_Op._9_No._1 | 7 | 2 643 247 | 30 475 | 471 450 | 65.8 |
  | Chopin_Etude_Op10_No9 | 4 | 1 771 562 | 29 569 | 286 268 | 69.9 |
  | Chopin_Mazurka_Op6_No1 | 3 | 1 353 489 | 20 913 | 221 367 | 72.1 |
  | Clair_de_Lune__Debussy | 5 | 2 378 951 | 24 317 | 381 747 | 74.6 |
  | Erik_Satie_-_Gymnopedie_No.1 | 2 | 511 542 | 14 089 | 90 837 | 44.4 |
  | Grieg_Butterfly_Op43_No1 | 3 | 1 300 912 | 17 332 | 218 336 | 71.1 |
  | Grieg_Little_bird_Op43_No4 | 2 | 863 925 | 17 151 | 139 008 | 67.9 |
  | Maple_Leaf_Rag_Scott_Joplin | 3 | 1 931 461 | 14 794 | 310 849 | 101.2 |
  | Prelude_I_BWV_846 | 2 | 868 882 | 10 951 | 145 958 | 71.3 |
  | Scarlatti_Sonata_in_C-major | 3 | 1 069 567 | 16 884 | 169 399 | 55.1 |

  Soma cru (scene+glyphs+manifest, sem timemap) das 10 peças: 14 891 893
  bytes. Soma dos `.vsb`: 2 435 219 bytes — o zip (deflate padrão do
  `zip_file.hpp`) comprime para **~16,4%** do tamanho cru (~6:1), consistente
  com texto JSON repetitivo (chaves, formatação numérica). `timemap.json` não
  entrou na soma "cru" por peça pois seu peso é marginal frente a
  `scene.json`/`glyphs.json` (dezenas de KB vs. centenas de KB a MB). Esses
  números são o insumo direto do gate de P01 (D-BIN).
- Bloqueios: nenhum.
