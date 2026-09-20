# P02a — Decisão D-RUNTIME, `libverovio` e wrapper C

**Depende de:** S07 · **Decisão necessária:** SIM (D-RUNTIME)

## Objetivo

Decidir se o app precisa gerar `.vsb` no aparelho e, se precisar, produzir a
biblioteca nativa com as funções do bridge expostas em C. O binding Dart e o
empacotamento ficam em P02b.

## Decisão necessária

Perguntar **antes de começar**: o app vai (a) gerar o `.vsb` em runtime no
dispositivo, (b) consumir `.vsb` pré-gerado (servidor/build), ou (c) os dois?
Isso muda o que precisa ser empacotado — a `libverovio.so` mais os dados de
fonte do Verovio pesam; um `.vsb` pré-gerado não pesa nada além de si mesmo.
Se a resposta for (b), **este passo e o P02b não são executados** — registre
a decisão e siga.

## Ler antes (só isto)

- `../verovio_lottie/docs/plano/E01-bindings-dart-ffi.md` — o caminho já foi
  percorrido uma vez (build da `.so`, wrapper C, pacote Dart). Reaproveite,
  trocando as funções Lottie pelas de `.vsb`.
- `verovio/tools/c_wrapper.cpp` L296-L340 (o padrão de wrapper C do projeto).
- `verovio/src/toolkit.cpp`, as funções de saída `.vsb` (S06/S07).

## Contexto que você precisa (não vá procurar, está aqui)

- O `Toolkit` já expõe a geração de `.vsb` (S06/S07); o wrapper C é uma casca
  fina sobre ela, no mesmo estilo das funções já existentes.
- `verovio/data` é obrigatório em runtime (`--resource-path`): são as fontes
  SMuFL e as métricas de texto. Empacotar isso num app Flutter tem uma
  armadilha conhecida — o bundler **não recursa** em subdiretórios de assets;
  o `verovio_lottie` resolveu com um zip único (ver
  `../verovio_lottie/verovio_viewer/README.md`, "Por que um zip, não arquivos
  crus"). Isso é P02b, mas decida o formato aqui, porque muda o wrapper.
- O `verovio_lottie` tem `tools/build-android-*` como precedente de build
  Android — confira antes de inventar.
- **`xml:id` auto-gerado não é determinístico entre processos** (nota de
  S04). Isso afeta diretamente o critério de "byte-idêntico ao da CLI": só
  vale para peças cujos elementos têm `xml:id` explícito no MEI, ou
  comparando o **mesmo processo**. Escolha o caso de teste com isso em mente e
  registre.

## O que fazer

1. Fazer a pergunta ao usuário e registrar a resposta com data (README do
   plano + `CLAUDE.md`).
2. Expor no wrapper C:

   ```c
   bool vrvToolkit_renderToBridgeFile(void *tk, const char *path);
   const char *vrvToolkit_renderToBridgeJson(void *tk);
   ```

   Seguindo exatamente o padrão de vida útil de string do wrapper existente
   (buffer interno reutilizado — documente).
3. Build da `libverovio.so` para as plataformas decididas (Linux desktop e
   Android arm64 no mínimo), com o comando registrado nas notas.
4. Teste de fumaça nativo: gerar um `.vsb` pela biblioteca, fora do Flutter,
   e abri-lo com o parser Dart (ou com Python) para confirmar que é válido.

## Fora de escopo

- Binding Dart, isolate e empacotamento de dados (P02b).
- iOS/Windows/macOS, a menos que o usuário peça na decisão.

## Critérios de aceite

1. A decisão D-RUNTIME está registrada, com data, no README do plano e no
   `CLAUDE.md`. Se for (b), o passo termina aqui.
2. `libverovio.so` compila para Linux desktop e Android arm64; comandos nas
   notas.
3. As duas funções novas aparecem nos símbolos exportados
   (`nm -D libverovio.so | grep Bridge`).
4. Teste de fumaça: `.vsb` gerado pela biblioteca abre no parser sem erro e
   tem o mesmo número de páginas que o gerado pela CLI.
5. Tamanho da biblioteca por plataforma registrado — é insumo da conta de
   tamanho do app em P02b.

## Notas de execução

- **2026-09-20 — D-RUNTIME resolvida: opção (a), o app gera o `.vsb` no
  dispositivo** (decisão do usuário). Registrada no `CLAUDE.md` ("Decisões
  registradas e itens abertos") e na tabela "Decisões pendentes" do
  [README do plano](README.md). Consequência aceita: a `libverovio.so` e os
  dados de `verovio/data` vão no app (números abaixo).

### Wrapper C

- `verovio/tools/c_wrapper.h` / `.cpp` ganharam, na posição alfabética entre
  `renderData` e `renderToExpansionMap` (o arquivo é ordenado):

  ```c
  bool vrvToolkit_renderToBridgeFile(void *tkPtr, const char *filename);
  const char *vrvToolkit_renderToBridgeJson(void *tkPtr);
  ```

  Assinaturas exatamente as do passo. `renderToBridgeJson` não recebe
  intervalo de páginas: usa o padrão de `Toolkit::RenderToBridgeJson()`
  (`fromPage = 1`, `toPage = -1`), ou seja, o documento inteiro, o mesmo que
  a CLI com `-a`. Vida útil da string: o ponteiro é do buffer interno da
  instância (`SetCString`/`GetCString`), válido só até a próxima chamada que
  devolva string **na mesma instância**; o chamador copia e nunca libera —
  documentado no `.cpp` e igual a todas as outras funções de lá.
- **Achado (bug pré-existente que bloqueava o passo):** `-DBUILD_AS_LIBRARY=ON`
  **não compilava** neste fork, antes de qualquer mudança minha.
  `c_wrapper.h` declarava `bool vrvToolkit_renderToExpansionMap(void *)`
  enquanto `c_wrapper.cpp` define `const char *` — `error: conflicting
  declaration of C function`. O alvo CLI (`tools/main.cpp`) não inclui
  `c_wrapper.h`, então o erro nunca apareceu nos passos S06/S07. O `.cpp`
  é que está certo (`Toolkit::RenderToExpansionMap()` devolve `std::string`)
  e o binding Dart já assumia `const char *`; corrigi a declaração no header.
  Uma varredura comparando todas as declarações do header com as definições
  do `.cpp` não achou nenhum outro par divergente.

### Build

- **Linux x86_64** (`bindings/dart/build_linux_so.sh`, CMake
  `-DBUILD_AS_LIBRARY=ON -DCMAKE_BUILD_TYPE=Release`, gcc 13): limpo, sem
  nenhum aviso vindo de `c_wrapper.cpp` (os avisos `-Warray-bounds` do log
  são de `stl_algobase.h`, pré-existentes e não vêm do bridge).
- **Android arm64-v8a** (`bindings/dart/build_android_so.sh arm64-v8a`,
  `-DBUILD_AS_ANDROID_LIBRARY=ON`, NDK 29.0.13846066 / clang 21, `android-21`):
  limpo. O `.so` sai com `ARM aarch64` confirmado por `file` e os dois
  símbolos do bridge presentes (`llvm-nm -D`). Strip obrigatório: o
  `.so` cru tem **191 MB** de informação de depuração.
- **Critério 5 — tamanho por plataforma** (insumo da conta de tamanho do app
  em P02b):

  | Plataforma | `.so` sem strip | `.so` com strip |
  | --- | --- | --- |
  | Linux x86_64 | 20 364 400 B (19,4 MB) | **17 796 992 B (17,0 MB)** |
  | Android arm64-v8a | 200 512 776 B (191,2 MB) | **19 374 472 B (18,5 MB)** |

- **Dados de `verovio/data`** (o outro lado da conta de P02b): 4 188 309 B
  (4,0 MB) de conteúdo em **2 685 arquivos** e 6 subdiretórios — 14 MB *em
  disco*, porque quase todo arquivo é um XML de glifo menor que um bloco.
  `Resources::InitFonts` (`src/resources.cpp` L61) carrega obrigatoriamente
  **Bravura** (a tabela codepoint→nome sai dela), **Leipzig** (fonte padrão,
  `Options::m_font.Init("Leipzig")`) e a família **Times** de `data/text`:
  2 389 018 B (2,3 MB) em 1 553 arquivos. Gootville, Leland e Petaluma
  (1,8 MB) só entram se o app trocar de fonte.
- **Formato de empacotamento dos dados (o passo pedia decidir aqui porque
  "muda o wrapper"): não muda.** `Resources` só aceita um caminho de
  diretório (`Resources::SetPath`, `include/vrv/resources.h` L53; o
  `ZipFileReader` de `LoadFont` serve só para *fonte customizada* avulsa, não
  para o diretório de dados). Logo, qualquer que seja o formato do asset, o
  app precisa extrair para um diretório real e passar o caminho a
  `vrvToolkit_constructorResourcePath`. A armadilha do bundler (não recursa
  em subdiretórios de asset) continua valendo e o zip único segue sendo a
  forma recomendada — mas é decisão de **P02b**, sem efeito no wrapper.

### Binding Dart (`verovio/bindings/dart`)

Estava **quebrado** ao começar o passo: herdado do `verovio_lottie`, ainda
fazia `lookupFunction('vrvToolkit_renderToDotLottieFile')` e mais quatro
símbolos Lottie que F01/S02 removeram do wrapper — qualquer uso do pacote
falhava no construtor de `VerovioBindings`. Trocados pelos dois do bridge em
`verovio_bindings.dart` e por `renderToBridgeFile`/`renderToBridgeJson` em
`VerovioToolkit`; README, `pubspec.yaml`, `example/main.dart` e `.gitignore`
atualizados junto (e as referências mortas a `swift-toolkit`, `iOS/` e
`E00`/`E01`, que não existem neste repositório). `dart analyze` sem avisos,
`dart format` aplicado.

### Critérios de aceite

1. **Decisão registrada** ✔ — `CLAUDE.md` e README do plano, com data.
2. **Compila** ✔ — Linux x86_64 e Android arm64-v8a, comandos acima.
3. **Símbolos exportados** ✔:

   ```
   $ nm -D libverovio.so | grep -i bridge
   00000000004b1270 T vrvToolkit_renderToBridgeFile
   00000000004b13a0 T vrvToolkit_renderToBridgeJson
   ```

   (mais os símbolos C++ de `BridgeDeviceContext`/`BridgeWriter`/`Toolkit`,
   visíveis porque o alvo não usa version script.)
4. **Teste de fumaça** ✔, e mais forte que o critério pedia. Grieg
   (`corpus/mei/Grieg_Little_bird_Op43_No4.mei`, 2 páginas) exportado pela
   biblioteca via FFI, fora do Flutter, com `resetXmlIdSeed(42)` para casar
   com o `-x 42` da CLI (sem isso os `xml:id` auto-gerados não batem entre
   processos — nota de S04). Comparado com o `.vsb` da CLI:

   | Entrada do zip | Resultado |
   | --- | --- |
   | `scene.json` (872 003 B) | **byte-idêntico** |
   | `glyphs.json` (17 151 B) | **byte-idêntico** |
   | `timemap.json` (44 347 B) | **byte-idêntico** |
   | `manifest.json` (174 B) | difere **só** em `generator` |

   A diferença do `generator` é esperada e não é defeito: o hash do commit é
   compilado no binário, e o binário da CLI em `verovio/tools/verovio` foi
   construído em `ee4b9fe` enquanto a `.so` saiu de `22f946d`. Contagem de
   páginas: 2 na CLI, 2 no FFI (`getPageCount()` e `len(scene.pages)`).
   Os dois arquivos passam pelo parser Dart real (`VsbDocument.fromBytes`)
   sem erro:

   ```sh
   cd score_bridge && CORPUS_DIR=../compare/out/p02a \
       flutter test tool/measure_parse_time.dart
   # grieg-cli.vsb  140290 B  75,36 ms   |   grieg-ffi.vsb  140291 B  62,82 ms
   ```

   O script que gerou o `.vsb` pelo FFI era descartável (`smoke_p02a.dart`,
   apagado depois); o caminho permanente equivalente é
   `dart run example/main.dart <mei> <saida.vsb> ../../data`.
5. **Tamanho registrado** ✔ — tabela acima.

- **`dart test` do binding**: 4/4 passando contra a `.so` recém-construída
  (contagem de páginas, SVG, pacote `.vsb` com magic `PK` + as três entradas
  obrigatórias, e `vsb-json` com `len(scene.pages) == getPageCount()`). Os
  dois testes de dotLottie viraram esses dois. `score_bridge` precisa de
  `dart:ui` e não pode ser importado de um `dart test` puro, por isso a
  checagem com o parser de verdade é a do critério 4, acima, e não um teste
  do pacote.
- **Fora de escopo, como o passo manda:** nenhum projeto Gradle/JNI, nenhum
  isolate, nenhum empacotamento de `verovio/data` — tudo isso é P02b. Só
  `arm64-v8a` foi construído (o mínimo que o passo pede); o
  `build_android_so.sh` já aceita as outras ABIs por argumento.
- **`verovio/tools/verovio` (CLI) não foi reconstruído**: nada em `src/` ou
  `include/` mudou, só `tools/c_wrapper.*`, que o alvo CLI não compila.
