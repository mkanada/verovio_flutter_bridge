# Plano de implementação — exportador `.vsb` + renderizador Flutter

Este diretório divide o trabalho em passos pequenos, cada um executável por um
modelo com contexto limitado. Leia **só** este README, o [`CLAUDE.md`](../../CLAUDE.md)
da raiz, a [especificação do formato](../formato/especificacao-v1.md) e o
arquivo do passo que for executar.

Contexto de por que este projeto existe:
[`docs/licoes-do-verovio-lottie.md`](../licoes-do-verovio-lottie.md).

## Como executar um passo

1. Leia `CLAUDE.md`, as seções **Convenções** e **Mapa do código** abaixo, e o
   arquivo do passo.
2. Confira na tabela de passos se as dependências estão concluídas.
3. Se o passo tiver um bloco **Decisão necessária**, pare e pergunte ao usuário
   antes de escrever código. Não decida sozinho.
4. Implemente só o escopo do passo (a seção "Fora de escopo" existe para isso).
5. Rode **todos** os critérios de aceite. Um passo só está concluído quando
   cada critério foi executado e o resultado registrado.
6. Marque o passo como `concluído` na tabela abaixo e registre em "Notas de
   execução" (no fim do arquivo do passo) qualquer desvio, número medido ou
   descoberta que afete passos seguintes.
7. Não faça commit nem push sem o usuário pedir.

## Convenções

- **Build do Verovio** (a partir da raiz): `cd verovio/tools && cmake ../cmake
  && make -j4`. Sempre que criar um `.cpp` novo, rode `cmake ../cmake` de novo
  (o CMake coleta `../src/*.cpp` por glob no momento da configuração).
- **Binário**: `verovio/tools/verovio`, sempre com `--resource-path verovio/data`.
- **Ferramenta de comparação**: `cd compare && flutter build linux --release`
  → `compare/build/linux/x64/release/bundle/compare`; e
  `cd compare/svg_render && cargo build --release` →
  `compare/svg_render/target/release/svg_render`. O binário Flutter precisa de
  display: rode sob `xvfb-run -a` quando `DISPLAY` estiver vazio (os scripts
  em `compare/scripts/` já fazem isso).
- **Pacote Flutter**: `cd score_bridge && flutter test` (unitários e goldens).
- **Saídas temporárias** vão em `compare/out/` (git-ignorado). Nunca em
  `verovio/` nem em `score_bridge/`.
- **Estilo C++**: imite `verovio/src/svgdevicecontext.cpp` (namespace `vrv`,
  cabeçalho de arquivo, separadores `//----`). Use o `.clang-format` do fork.
- **Estilo Dart**: `dart format` + `flutter analyze` sem avisos.
- **Unidades**: tudo que chega ao `DeviceContext` está em unidades de definição
  (`DEFINITION_FACTOR = 10`), com o eixo y já apontando para baixo.
- **Corpus de teste**: `corpus/mei/*.mei` e `corpus/musicxml/*.mxl`.
- **Tolerância de diff**: 32/255 por canal, a mesma do `verovio_lottie` — todo
  número de paridade citado no plano usa essa tolerância.

## Arquitetura alvo

```
verovio -t vsb partitura.mei -o partitura.vsb
  └─ Toolkit::RenderToBridgeFile()
       └─ por página: RenderToDeviceContext(p, &bridgeDc)      (já existe)
            └─ View::DrawCurrentPage(dc)                       (já existe)
                 └─ BridgeDeviceContext monta a IR de cena + coleta glifos
       └─ BridgeWriter serializa IR → scene.json / glyphs.json
       └─ ZipFileWriter empacota → .vsb (+ timemap.json)

Flutter:
  VsbDocument.parse(bytes)            → modelo imutável (score_bridge)
    └─ ScenePainter(page, colors)     → Canvas (paths, glifos, texto)
         └─ ScorePageView             → CustomPaint em camadas
              └─ ScoreController      → cor/animação por xml:id
```

## Mapa do código (verificado em `../verovio_lottie`, Verovio 6.3.0)

Referências para o código que **vem junto** na cópia do fork (F01). Se uma
linha "andou", localize o símbolo por `grep -rn "<símbolo>" verovio/src`.

| Conceito | Onde |
| --- | --- |
| API abstrata de desenho | `include/vrv/devicecontext.h` L99-L337 |
| `DEFINITION_FACTOR` | `include/vrv/vrvdef.h` L457 |
| `Pen`/`Brush`/`FontInfo`, `COLOR_NONE` | `include/vrv/devicecontextbase.h` |
| Implementação de referência (SVG) | `src/svgdevicecontext.cpp`: `StartGraphic` L251, `StartPage` L484 (viewBox/`page-margin`/CSS global), primitivas L686-L1017, texto L1019-L1167, `DrawMusicText` L1174, `GetColor` L1295 |
| Device context a renomear | `src/lottiedevicecontext.cpp` (980 linhas), `include/vrv/lottiedevicecontext.h` |
| IR de cena | `include/vrv/lottiegeometry.h` (`LottieVec`, `LottieBezier`, `LottieShape`, `LottieTextRun`, `LottieNode`, `LottiePage`) |
| Baking de glifo (vira referência em S03) | `src/lottiedevicecontext.cpp` `MakeGlyphShape` L388-L429, `GetGlyphAdvance` L431-L444, cache `m_glyphCache` |
| Parser de path de glifo | `src/svgpathparser.cpp`, `include/vrv/svgpathparser.h` |
| Métricas de página / ajuste `meet` | `src/lottiewriter.cpp` `ComputePageMetrics` L597-L620 |
| Resolução de CSS por classe (bold/italic) | `src/lottiewriter.cpp` L426-L530 |
| Glifos SMuFL (dados) | `Resources::GetGlyph` (`include/vrv/resources.h`), `Glyph::GetXML` (`src/glyph.cpp` L150-L161), dados em `data/<fonte>/*.xml` |
| Toolkit | `include/vrv/toolkit.h`, `src/toolkit.cpp` (`RenderToDeviceContext` L1674-L1730; funções Lottie L1912+ servem de modelo) |
| Timemap | `include/vrv/timemap.h`, `src/timemap.cpp`, `Toolkit::RenderToTimemap` |
| Formatos de saída | `include/vrv/toolkitdef.h` L13-L37 (`FileFormat`), `src/options.cpp` L2027-L2060 (`SetOutputTo`), `tools/main.cpp` L284-L292 (validação), L350-L390 (laço de páginas) |
| Escrita de zip | `ZipFileWriter` em `include/vrv/filereader.h` / `src/filereader.cpp` |
| Bindings C (modelo para P02) | `tools/c_wrapper.cpp` L296-L340 |

Fatos do corpus que orientam o plano (medidos no projeto anterior):

- Contagem de elementos no SVG do corpus inteiro: `path` 8025, `use` (glifos)
  5444, `polygon` 1526, `tspan` 398, `ellipse` 339, `rect` 250, `text` 160,
  `polyline` 52, `image` 0.
- Primitivas praticamente sem chamadas: `DrawEllipticArc`, `DrawSpline`,
  `DrawRotatedText` (0 ocorrências), `DrawSvgShape` (1), `DrawGraphicUri` (1),
  `RotateGraphic` (2).
- `data/text/Times*.xml` só tem métricas: **não há contornos de texto comum**
  no Verovio. Texto comum depende de TTF no lado do renderizador.

## Decisões pendentes

| Id | Pergunta | Bloqueia | Recomendação |
| --- | --- | --- | --- |
| D-NOME | Nome do formato, extensão e flags de CLI | — | Resolvida em S01 (2026-09-17): `.vsb`, `-t vsb`, `-t vsb-json`; timemap embutido quando disponível |
| D-BIN | Vale trocar JSON por encoding binário? | P01 | medir primeiro; só decidir com números reais na mão |
| D-RUNTIME | O app gera `.vsb` em runtime (FFI) ou consome pré-gerado? | P02 | depende do zywny; perguntar |

Decisões **já tomadas** (não reabrir): ver "Decisões arquiteturais já tomadas"
no [`CLAUDE.md`](../../CLAUDE.md).

## Riscos conhecidos

1. **Paridade de texto comum** — foi a maior fonte de divergência no projeto
   anterior (de 0,36% média caiu para 0,13% só depois de 4 passos sobre texto).
   Aqui o renderizador é o Flutter, com a mesma TTF que o `resvg` usa, mas
   shaping/hinting podem divergir. **Mitigação:** R04 é um passo inteiro só
   para isso, com medição antes/depois, e o R06 mede o corpus.
2. **Backend gráfico** — Impeller e Skia antialiasam diferente do `tiny-skia`
   (do `resvg`). **Mitigação:** R05 mede os dois e registra o escolhido; a
   tolerância 32/255 absorve diferença de AA de borda, que é o que o projeto
   anterior já observava.
3. **Desempenho com página inteira em `CustomPaint`** — uma página do corpus
   tem ~2.000 formas. **Mitigação:** A01 separa estático (compilado uma vez em
   `ui.Picture`) de dinâmico; P03 mede em dispositivo.
4. **Tamanho do JSON** — o dicionário de glifos remove a maior repetição, mas
   o corpus é pequeno (5-16 compassos/peça). **Mitigação:** P01 mede tamanho e
   tempo de parse antes de qualquer otimização.
5. **`zip_file.hpp` é header-only com o miniz embutido** — incluí-lo em mais de
   uma unidade de tradução gera símbolos duplicados no link. O escritor de zip
   fica em `src/filereader.cpp`, que já o inclui.

## Passos

| Passo | Título | Depende de | Decisão | Status |
| --- | --- | --- | --- | --- |
| [F01](F01-montar-repositorio.md) | Montar o repositório a partir do fork validado | — | — | concluído com ressalva |
| [F02](F02-corpus-e-referencia-svg.md) | Corpus + referência SVG→PNG reproduzível | F01 | — | concluído |
| [S01](S01-especificacao-do-formato.md) | Fechar a especificação do formato `.vsb` | F01 | D-NOME resolvida | concluído |
| [S02](S02-bridge-device-context.md) | `BridgeDeviceContext`: renomear e limpar a IR | F01, S01 | — | concluído |
| [S03](S03-dicionario-de-glifos.md) | Dicionário de glifos + instâncias (substitui o baking) | S02 | — | concluído |
| [S04](S04-bboxes-e-indice.md) | Bounding boxes e índice de elementos endereçáveis | S02 | — | concluído com ressalva |
| [S05](S05-writer-json.md) | `BridgeWriter`: IR → `scene.json`/`glyphs.json` | S01, S02, S03, S04 | — | concluído |
| [S06](S06-toolkit-e-cli.md) | `Toolkit` + CLI (`-t vsb-json`, todas as páginas) | S05 | D-NOME resolvida | concluído |
| [S07](S07-pacote-vsb.md) | Pacote `.vsb` (zip) com timemap embutido | S06 | — | concluído |
| [R01](R01-pacote-dart-e-parser.md) | Pacote `score_bridge`: modelo + parser | S05 | — | concluído |
| [R02](R02-scene-painter-primitivas.md) | `ScenePainter`: primitivas, cor herdada, ajuste de página | R01 | — | a fazer |
| [R03](R03-glifos.md) | Glifos: `Path` por `glyphId`, cache e instâncias | R02, S03 | — | a fazer |
| [R04](R04-texto-comum.md) | Texto comum: TTF, alinhamento, bold/italic | R02 | — | a fazer |
| [R05](R05-harness-de-comparacao.md) | Harness cena→PNG + diff no `compare/` | R02, F02 | backend gráfico | a fazer |
| [R06](R06-varredura-do-corpus.md) | Varredura do corpus e relatório de paridade (> 99,9%) | R03, R04, R05, S06 | — | a fazer |
| [A01](A01-camadas-e-controller.md) | Camadas, cache de `Picture` e `ScoreController` | R06 | — | a fazer |
| [A02](A02-cor-e-animacao-por-nota.md) | Cor e animação individual por nota | A01 | — | a fazer |
| [A03](A03-paginas-e-navegacao.md) | Páginas: navegação, virada e rolagem | A01 | — | a fazer |
| [A04](A04-overlay-de-widgets.md) | Overlay de widgets por bbox (cursor, toque, gestos) | A01, S04 | — | a fazer |
| [A05](A05-host-simulado-timemap.md) | Host simulado com `timemap` (playback automático) | A02, A03, S07 | — | a fazer |
| [P01](P01-medicao-e-encoding.md) | Medição (tamanho, parse, frame) e gate de encoding binário | R06, A02 | D-BIN | a fazer |
| [P02](P02-geracao-em-runtime.md) | Geração em runtime: `libverovio` + FFI Dart | S07 | D-RUNTIME | a fazer |
| [P03](P03-desempenho-e-app-exemplo.md) | Desempenho em dispositivo + app de exemplo + docs finais | A05, P01 | — | a fazer |

Ordem sugerida: F01 → F02 → S01 → S02 → S03 → S04 → S05 → S06 → S07, com
R01-R02 começando em paralelo assim que S05 produzir o primeiro `scene.json`
de uma página. A fase A só começa depois que R06 fechar o número de paridade.
