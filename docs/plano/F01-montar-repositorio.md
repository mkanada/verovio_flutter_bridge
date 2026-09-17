# F01 — Montar o repositório a partir do fork validado

**Depende de:** — · **Decisão necessária:** não

## Objetivo

Trazer para cá o fork do Verovio já validado no `verovio_lottie`, removendo
tudo que é específico de Lottie, e provar que o binário resultante continua
produzindo **exatamente o mesmo SVG** de antes.

## Ler antes (só isto)

- `../verovio_lottie/README.md`, seção "Build".
- `../verovio_lottie/verovio/cmake/CMakeLists.txt` L180-L195 (o glob de fontes).
- A tabela "O que o projeto anterior provou que funciona" em
  [`docs/licoes-do-verovio-lottie.md`](../licoes-do-verovio-lottie.md).

## O que fazer

1. Copiar o fork, sem artefatos de build:

   ```sh
   cd /home/mauricio/rust_projects/verovio_flutter_bridge
   rsync -a --exclude 'tools/build-*' --exclude 'tools/verovio' \
         --exclude '*.o' --exclude 'CMakeCache.txt' --exclude 'CMakeFiles' \
         ../verovio_lottie/verovio/ verovio/
   ```

2. **Remover** os arquivos específicos de Lottie (a animação some do formato —
   ver `CLAUDE.md`):

   - `verovio/src/lottiewriter.cpp`, `verovio/include/vrv/lottiewriter.h`
   - `verovio/src/lottiehighlight.cpp`, `verovio/include/vrv/lottiehighlight.h`
   - `verovio/include/vrv/lottiepageturn.h`, `verovio/include/vrv/lottiestatemachine.h`

   **Manter** (são a base dos passos S02-S05): `lottiedevicecontext.{h,cpp}`,
   `lottiegeometry.h`, `svgpathparser.{h,cpp}`, o `ZipFileWriter` em
   `filereader.{h,cpp}`.

   > O `verovio_lottie` continua no disco: quando S05 precisar da resolução de
   > CSS por classe (`lottiewriter.cpp` L426-L530) ou de `ComputePageMetrics`
   > (L597-L620), leia de lá. Não recrie do zero.

3. Desconectar o que restou do código removido, sem inventar API nova:

   - `verovio/src/toolkit.cpp`: apagar `RenderToLottie*`/`RenderToDotLottie*` e
     seus helpers estáticos (`ParseLottieHighlightColor`, `CountTextRuns`,
     `WarnIfTextRunsSkipped`, embed de fonte), e os `#include` de
     `lottiehighlight.h`/`lottiepageturn.h`/`lottiewriter.h`. Manter o include
     de `lottiedevicecontext.h` (vira `bridgedevicecontext.h` em S02).
   - `verovio/include/vrv/toolkit.h`: apagar as declarações correspondentes.
   - `verovio/include/vrv/toolkitdef.h`: remover `LOTTIE`, `DOTLOTTIE`,
     `DOTLOTTIE_HIGHLIGHT` do enum `FileFormat`.
   - `verovio/src/options.cpp`: remover os ramos `"lottie"`, `"dotlottie"`,
     `"dotlottie-highlight"` de `SetOutputTo` e as 5 opções `m_lottie*`
     (registro + declaração em `include/vrv/options.h` L652-L656).
   - `verovio/tools/main.cpp`: remover os formatos da lista de validação
     (L284-L292) e o ramo de saída correspondente.
   - `verovio/tools/c_wrapper.cpp`: remover `vrvToolkit_renderToLottie*` e
     `vrvToolkit_renderToDotLottie*` (L296-L340) e, se existir, a entrada em
     `emscripten/exports.txt`.

4. Inicializar o repositório git (o diretório já tem um `.git` vazio, na
   branch `main` e **sem nenhum commit** — `git init` só reinicializa, é
   seguro) e escrever o `.gitignore` (mínimo: `verovio/tools/verovio`,
   `verovio/tools/build-*/`, `compare/out/`, `compare/build/`,
   `compare/svg_render/target/`, `**/.dart_tool/`, `build/`):

   ```sh
   git init && git add -A && git status --short | head
   ```

   Não faça commit sem o usuário pedir.

5. Compilar:

   ```sh
   cd verovio/tools && cmake ../cmake && make -j4
   ```

## Fora de escopo

- Renomear classes/arquivos `Lottie*` → `Bridge*` (é S02; aqui eles só
  continuam compilando com o nome antigo).
- Copiar `corpus/` e `compare/` (é F02).
- Qualquer mudança de comportamento no SVG.

## Critérios de aceite

1. `cd verovio/tools && cmake ../cmake && make -j4` compila sem erro e sem
   avisos novos em relação ao build do `verovio_lottie`.
2. Nenhuma referência pendente ao código removido:

   ```sh
   grep -rniE "dotlottie|lottiewriter|lottiehighlight|lottiepageturn|lottiestatemachine" \
        verovio/src verovio/include verovio/tools verovio/emscripten | grep -v Binary
   ```

   Deve retornar **vazio**.
3. **SVG byte-idêntico ao do fork original** — a prova de que nada quebrou:

   ```sh
   for f in corpus/mei/*.mei; do  # use ../verovio_lottie/corpus enquanto F02 não rodou
     n=$(basename "$f" .mei)
     ./verovio/tools/verovio -t svg -a --resource-path verovio/data -o /tmp/new-$n "$f"
     ../verovio_lottie/verovio/tools/verovio -t svg -a \
       --resource-path ../verovio_lottie/verovio/data -o /tmp/old-$n "$f"
     diff -r /tmp/new-$n* /tmp/old-$n* && echo "OK $n"
   done
   ```

   Todas as peças devem imprimir `OK`.
4. `verovio/tools/verovio -h` roda e **não** lista mais nenhuma opção `lottie*`.
5. `git status --short` mostra só arquivos versionáveis (nenhum `build-*`,
   nenhum binário).

## Notas de execução

- 2026-09-17: bloqueado. A cópia foi feita com os excludes prescritos e os seis arquivos listados foram removidos. A busca prescrita retornou 3 ocorrências, todas em `verovio/src/lottiepageturn.cpp` (nome, include e comentário).
- `cmake ../cmake` configurou com sucesso. `make -j4` falhou em `verovio/src/lottiepageturn.cpp:8`: `lottiepageturn.h` não existe. O passo manda remover esse cabeçalho, mas não lista `src/lottiepageturn.cpp` para remoção; o CMake o coleta por `file(GLOB ../src/*.cpp)`.
- Uma primeira tentativa de build foi interrompida pelo limite de 120 s em 36%; a repetição com 600 s chegou à falha acima.
- Comparação SVG do corpus, `--help`, criação do `.gitignore`/preparação git e status final não foram executados após o bloqueio. Nenhum commit ou push foi feito.
- 2026-09-17 (continuação): `verovio/src/lottiepageturn.cpp` já estava ausente no início desta execução; nenhuma outra fonte foi removida. Confirmados presentes `lottiedevicecontext.{h,cpp}`, `lottiegeometry.h` e `svgpathparser.{h,cpp}`.
- Limpos os artefatos conhecidos de build/binário e refeitos `cmake ../cmake` e `make -j4` em `verovio/tools`: configuração e compilação concluíram sem erro. O build emitiu avisos GCC em `iohumdrum.cpp` (código não alterado neste passo).
- Busca prescrita em `verovio/src verovio/include verovio/tools verovio/emscripten`: vazia.
- `verovio/tools/verovio -h`: executou com sucesso e não listou opções Lottie.
- Corpus MEI disponível em `../verovio_lottie/corpus/mei`: 5 peças, 15 SVGs de saída. A comparação byte a byte literal falhou somente nos metadados de versão/IDs: o binário atual embeda `Verovio 6.3.0-460cfd1-dirty`, o original `6.3.0-4f68a7c-dirty`. Com `-x 1` os IDs ficam iguais e, normalizando apenas esse hash no `<desc>`, todos os 15 SVGs coincidem; portanto não há diferença de renderização observada, mas o critério F01 de byte-idêntico literal permanece bloqueado por metadados de build.
- Criado `.gitignore` na raiz com os caminhos mínimos do passo; após a limpeza, não há `CMakeCache.txt`, `CMakeFiles`, `Makefile`, `cmake_install.cmake`, `verovio` ou `.o` gerados. Nenhum commit ou push foi feito.
