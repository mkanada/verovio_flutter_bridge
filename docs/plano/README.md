# Plano de implementação — exportador `.vsb` + renderizador Flutter

Este diretório divide o trabalho em passos pequenos, cada um executável por um
modelo com contexto limitado. Leia **só** este README, o [`CLAUDE.md`](../../CLAUDE.md)
da raiz, a [especificação do formato](../formato/especificacao-v1.md) e o
arquivo do passo que for executar.

Os passos das fases R, A e E têm sufixo de letra (`R02a`, `R02b`, …). O
número indica o tema (R02 = primitivas, A03 = páginas, E02 = repetições no
Dart) e a letra, a ordem dentro dele. Cada arquivo traz, numa seção **"Contexto que você precisa"**,
os fatos medidos e as armadilhas conhecidas daquele tema — a intenção é que
executar um passo não exija abrir mais nada além dos arquivos listados em
"Ler antes".

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
   descoberta que afete passos seguintes. Se um número medido contradisser um
   fato citado neste README ou no arquivo do passo, **corrija o documento** —
   os números aqui existem para poupar medição, e um número errado custa mais
   caro que nenhum.
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
- **Tolerância de diff**: 128/255 por canal, percentuais com 6 casas
  (decisão do usuário em 2026-09-19; antes era 32/255 como no
  `verovio_lottie` — números antigos continuam citados como "medidos a 32"
  e não são comparáveis aos novos) — todo
  número de paridade citado no plano a partir de R06b usa a nova tolerância.

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

## Mapa do código (estado real do repositório)

O que **já existe** e foi escrito pelos passos concluídos. Se uma linha
"andou", localize o símbolo com `grep -rn "<símbolo>" verovio/src` ou
`score_bridge/lib`.

### Lado C++ (exportador, fases F e S — concluído até S08)

| Conceito | Onde |
| --- | --- |
| Device context do bridge | `src/bridgedevicecontext.cpp`, `include/vrv/bridgedevicecontext.h` (renomeados de `lottie*` em S02) |
| IR de cena | `include/vrv/bridgegeometry.h` (`BridgeVec`, `BridgeBezier`, `BridgeShape`, `BridgeGlyphDef`, `BridgeGlyphUse`, `BridgeTextRun`, `BridgeNode`, `BridgePage`) |
| Serializador JSON | `src/bridgewriter.cpp`, `include/vrv/bridgewriter.h` (S05): `ApplyClassStyleRule` L166 (CSS por classe), `ComputePageMetrics` L202 (ajuste `meet` de §3) |
| Uso de glifo e dicionário | `src/bridgedevicecontext.cpp` `MakeGlyphUse` L616 (fórmula de `sx`/`sy`), `GetGlyphAdvance` L670 |
| Bbox de nó | `src/bridgedevicecontext.cpp` `GlyphBBox` L221, `CalculateNodeBBox` L269 (S08: bbox de glifo convertida de `Glyph::SetBoundingBox` para a escala/eixo dos contornos). O índice de elementos não é mais gravado nem construído no exportador: é derivado no parse (`ScenePage.elements`, spec §5.5) |
| Toolkit | `include/vrv/toolkit.h`: `RenderToBridgeJson` L460, `RenderToBridgeJsonFile` L472, `RenderToBridgeFile` L486 |
| CLI | `tools/main.cpp` L286 (lista de formatos), L552 (`vsb`), L566 (`vsb-json`); `include/vrv/toolkitdef.h` L35-L36 (`VSB`, `VSB_JSON`) |
| Escrita de zip | `ZipFileWriter` em `include/vrv/filereader.h` / `src/filereader.cpp` (header-only com miniz: só pode ser incluído nessa unidade) |
| Timemap | `include/vrv/timemap.h`, `src/timemap.cpp`, `Toolkit::RenderToTimemap` |
| Parser de path de glifo | `src/svgpathparser.cpp`, `include/vrv/svgpathparser.h` |
| Glifos SMuFL (dados) | `Resources::GetGlyph` (`include/vrv/resources.h`), `Glyph::GetXML` (`src/glyph.cpp`), `Glyph::SetBoundingBox` L95 (a bbox ×10 de S08), dados em `data/<fonte>/*.xml` |
| Bindings C | `tools/c_wrapper.cpp`: `vrvToolkit_renderToBridgeFile` L296, `vrvToolkit_renderToBridgeJson` L307 |
| Binding Dart FFI | `verovio/bindings/dart/`: `VerovioToolkit` (`lib/src/verovio_toolkit.dart`), assinaturas em `lib/src/verovio_bindings.dart`, builds em `build_linux_so.sh` / `build_android_so.sh` |
| Padrões do bridge (P01b) | `Toolkit::ApplyBridgeDefaults` (`toolkit.cpp`), chamado no início de `LoadData` |
| Título sem cabeçalho (P01a) | `Toolkit::ReadBridgeMeta` (`toolkit.cpp`): cai no `<pgHead func="first">` codificado ou gera um descartável com `GenerateFromMEIHeader` quando não há cabeçalho renderizado |
| Pontos de chegada de repetição (P02b, fase P) | `include/vrv/bridgealternates.h` + `src/bridgealternates.cpp`: `BridgeAlternates::FindAlternateStarts` (função pura); `Toolkit::ComputeMeasureDocOrder`/`ComputeMeasureExecutionOrder`/`ComputeAlternateStarts` (`toolkit.cpp`) montam os três insumos a partir do `Doc` e do timemap. Debug-only por enquanto: `--debug-alternate-starts` grava `_executionOrder`/`_alternateStarts` só em `-t vsb-json` |
| Renderização das páginas alternativas + `alternates.json` (P02c, fase P) | `Toolkit::RenderAlternatesToBridge`/`SelectFromMeasureToEnd` (`toolkit.cpp`): `Select`/`RedoLayout` por ponto de chegada de P02b, no mesmo `BridgeDeviceContext` das páginas normais; `BridgeWriter::WriteAlternates`/`BridgeAlternateSequence` (`bridgewriter.h`/`.cpp`). Opção `--no-vsb-alternates` desliga (padrão é gerar) |
| Referência SVG das páginas alternativas (P02d, fase P) | CLI `--select-from <xml:id>` (`tools/main.cpp`, `options.h`/`.cpp`: `m_selectFrom`) chama `Toolkit::SelectFromMeasureToEnd`, o mesmo mecanismo de P02c; `compare scene-to-png --alternate <xml:id>` (`compare/lib/src/scene_to_png.dart`) lê pelo `score_bridge` (P03a); `compare-page.sh --alternate`/`compare-corpus.sh SWEEP_ALTERNATES=1` varrem as duas |
| Modo debug do `.vsb` (§2.6, 2026-09-24) | `--vsb-debug` (`options.h`/`.cpp`: `m_vsbDebug`) embute `debug-options.json`/`debug-source.txt` no pacote (`Toolkit::RenderToBridgeFile`/`RenderToBridgeJson`, `m_debugSourceData` capturado em `Toolkit::LoadData`); `--options-file <caminho>` no CLI (`tools/main.cpp`) reaplica esse JSON via `Toolkit::SetOptions` (depois de `--resource-path`, antes de carregar a partitura). `compare/scripts/compare-page.sh` aceita um `.vsb` em modo debug como `<arquivo>` sozinho — sem a partitura original nem as flags que o geraram |

Fora do exportador, únicos pontos do fork que a fase E tocou: geração de
expansão (repetições), em `src/expansionmap.cpp`/`include/vrv/expansionmap.h`
(E04a) — `GenerateExpansionFor` atravessa várias `<section>` e grupos de
`<ending>`; `EndingHasRepeatEnd` é novo; `Expand()` ganhou um fallback de
busca pelo `Score` ancestral quando o id referenciado não é descendente da
seção onde a expansão vive — e o importador de MusicXML, em
`src/iomusxml.cpp` (E04b) — `CreateExpansion` trata uma casa 1 sozinha com
repeat como casa 1 + casa 2 implícita (o que vem a seguir), e o fechamento
de uma `<ending>` para de descartar `m_repeatInfo`.

### Referência de verdade (não alterar — é o que a paridade compara)

| Conceito | Onde |
| --- | --- |
| API abstrata de desenho | `include/vrv/devicecontext.h` L99-L337 |
| `DEFINITION_FACTOR` | `include/vrv/vrvdef.h` L457 |
| `Pen`/`Brush`/`FontInfo`, `COLOR_NONE` | `include/vrv/devicecontextbase.h` |
| Implementação de referência (SVG) | `src/svgdevicecontext.cpp`: `StartGraphic` L251, `StartPage` L484 (viewBox, `page-margin`, CSS global, `font-family="Times, serif"`), primitivas L686-L1017, texto L1019-L1167, `DrawMusicText` L1174 (o `<use>` do glifo), `GetColor` L1295 |

### Lado Dart (renderizador, fases R e A)

| Conceito | Onde |
| --- | --- |
| Modelo imutável | `score_bridge/lib/src/model.dart` (R01): `VsbDocument`, `ScenePage`, `SceneNode`, `ScenePath`/`SceneRect`/`SceneEllipse`/`SceneGlyphUse`/`SceneText`, `ScenePaint`, `GlyphDef`, `TimemapEntry`, `IndexEntry` |
| Parser | `score_bridge/lib/src/parser.dart` (R01): `parseVsbDocumentBytes`, `parseSceneDocument`, `_asRect` para bboxes da cena e `_parseGlyphBBox` para os metadados brutos de glifo (S08) |
| API pública | `score_bridge/lib/score_bridge.dart` (só o que o app pode importar) |
| Testes existentes | `score_bridge/test/`: `exemplo_minimo_test.dart`, `corpus_fixture_test.dart`, `parser_errors_test.dart`, `roundtrip_count_test.dart`, `alternates_test.dart` (P03a), `score_view_pageref_test.dart` (P03b); fixtures reais em `test/fixtures/erik-satie.vsb` e `test/fixtures/maple-leaf-rag.vsb` (com `alternates.json`) |
| Medição de parse | `score_bridge/tool/measure_parse_time.dart` (roda com `flutter test`, não com `dart run`) |
| Já criados nas fases R/A | `geometry.dart` (R02a), `scene_painter.dart` (R02b/c), `dash.dart` (R02c), `glyph_cache.dart` (R03a), `text_font.dart` (R04a), `scene_walk.dart` (A01a: percurso único, extraído do `scene_painter.dart`), `segmentation.dart` (A01a), `page_layers.dart` + `score_page_view.dart` (A01b), `score_controller.dart` (A01c/A02b), `highlight_engine.dart` (A02a). `score_view.dart` (A03a/b/c: `ScoreView`, `ScoreViewController`, `SweepCurtain`), `hit_test.dart` (A04a: `ScoreGeometry`, via `VsbDocument.geometry`), `score_cursor.dart` (A04b), `score_timeline.dart` + `score_player.dart` (A05a/b). Fase A **concluída** |
| Ids expandidos (`-rendN`) | `expansion.dart` (E02a): `IdExpansion`, exposto como `VsbDocument.sceneIdOf`/`passOf` — regra do sufixo de D-EXPMAP, usada por `ScoreController`, `ScoreGeometry.elementOf`/`pageOf`/`rectForId` e `animatableIdsFromTimemap(..., document: ...)` |
| Ocorrências e toque num elemento repetido | `score_timeline.dart` (E02b/E02c): `MeasureInfo.pass`/`.timemapId`, `ScoreTimeline.occurrencesOf`/`onsetsOf`; `score_player.dart`: `ScorePlayer.seekToElement` |
| Haste com página de destino | `score_view.dart` (E03a): `SweepCurtain.targetPageIndex`, `ScoreViewState._targetOf`/`_isValidCurtain` |
| Modelo/parser/geometria das páginas alternativas (P03a, fase P) | `model.dart`: `PageRef`, `AlternateSequence`, `VsbDocument.alternates`/`pageAt`/`geometryOf`/`alternateStartingAt` (parse preguiçoso: `alternates` é `late final`); `parser.dart`: `parseAlternatesDocument`; `hit_test.dart`: `ScoreGeometry.forPages` (geometria por conjunto de páginas, não só por documento) |
| Vista exibe um `PageRef` (P03b, fase P) | `score_page_view.dart`: `ScorePageView.sequence`; `score_view.dart`: `SweepCurtain.sequence`/`.targetSequence`/`.page`/`.target`, `ScoreViewState._shown`/`.displayedPage`/`.showPage`/`._keyOf`/`._fit`/`._centered`/`._page`/`._endX` (todos migrados de `int` para `PageRef`), `ScoreViewController.showPage`/`.displayedPage`. Testado em `test/score_view_pageref_test.dart` (7 critérios) |
| Rota de exibição na timeline (P04a, fase P) | `score_timeline.dart`: `MeasureInfo.view`/`.isJump`, `ScoreTimeline(document, {useAlternates})`, `restViewAt`, `_resolveJump`/`_pageInView`/`_firstMeasurePage` (regra de P00); `curtainAt`/`SweepCurtain` passam `sequence`/`targetSequence` de `_Run.view` (migrado de `int page`). Testado em `test/score_timeline_route_test.dart` e `test/score_timeline_jump_curtain_test.dart` (atualizado) |
| `ScorePlayer` segue a rota (P04b, fase P) | `score_player.dart`: `ScorePlayer({..., useAlternates})`, `_publish` usa `restViewAt`/`v.showPage` no lugar de `restPageAt`/`v.goToPage`. Testado em `test/score_player_alternates_test.dart` |
| Evidências visuais (P04c, fase P) | `tool/generate_examples.dart`: `_repeticaoAlternativaExample`, gera `docs/exemplos/repeticao-alternativa/{MapleLeafRag,Mazurka}/`; fixture nova `test/fixtures/mazurka.vsb` (`-x 42`, 1 sequência alternativa) |
| Portão da fase P (P05) | `test/paginas_alternativas_test.dart`: invariantes de P04a e `ScorePlayer` de ponta a ponta sobre as 23 fixtures de `repeticoes/`, regeneradas com `-x 42` (agora com `alternates.json`: 7 das 23 têm sequência). Custo de tamanho/tempo em [`relatorio-paginas-alternativas.md`](../relatorio-paginas-alternativas.md); nota para o host em [`nota-para-zywny-fase-p.md`](../nota-para-zywny-fase-p.md) |

### Comparação visual

| Conceito | Onde |
| --- | --- |
| App de diff (Flutter/Linux) | `compare/lib/main.dart` (comando `diff`; `scene-to-png` entra em R02d), `compare/lib/src/diff.dart` |
| SVG → PNG de referência | `compare/svg_render/src/main.rs` (resvg 0.48 + tiny-skia): fontes em L100-L125, `set_serif_family` L119 |
| Scripts | `compare/scripts/compare-page.sh` (R05b reescreve), `compare/scripts/compare-corpus.sh` (R06a reescreve) |
| Pacotes `.vsb` já gerados | `compare/out/s08/*.vsb` (10 peças, 34 páginas) — é deles que saem os números desta página |

## Fatos do corpus

Medidos no projeto anterior, sobre a saída SVG:

- Contagem de elementos no SVG do corpus inteiro: `path` 8025, `use` (glifos)
  5444, `polygon` 1526, `tspan` 398, `ellipse` 339, `rect` 250, `text` 160,
  `polyline` 52, `image` 0.
- Primitivas praticamente sem chamadas: `DrawEllipticArc`, `DrawSpline`,
  `DrawRotatedText` (0 ocorrências), `DrawSvgShape` (1), `DrawGraphicUri` (1),
  `RotateGraphic` (2).
- `data/text/Times*.xml` só tem métricas: **não há contornos de texto comum**
  no Verovio. Texto comum depende de TTF no lado do renderizador.

### Fatos medidos nos `.vsb` do corpus (S08, `compare/out/s08/*.vsb`)

Estes números vêm dos pacotes gerados pelo próprio projeto e orientam quase
todos os passos das fases R e A. Cada passo repete os que lhe interessam, para
que ninguém precise ler este README inteiro para executar um passo.

| Medida | Valor |
| --- | --- |
| Peças / páginas | 10 / **34** |
| Nós da árvore | 50 544, dos quais 39 290 têm `id` |
| Profundidade máxima da árvore | 9 |
| Formas | `p` 26 469 · `r` 1 401 · `e` 911 |
| Usos de glifo (`u`) | 15 413, com apenas **16 a 37 glifos distintos por peça** |
| Runs de texto (`t`) | 417 (12 a 89 por peça) |
| Formas com `strokeWidth` | **todas** trazem o campo; 6 604 (22,9%) trazem `"stroke":"none"` (pena 0 — feixes, `r`/`e` cheios —, R06b) e o restante herda a cor (nenhuma traz cor explícita) |
| `fill` | `"none"` em 20 440, explícito em 58, herdado no restante |
| `fillOpacity`/`strokeOpacity` | **nenhuma ocorrência** |
| `lineCap` | `default` 27 285 · `round` 1 331 · `square` 165 |
| `dash` | 8 ocorrências, todas `[36, 72]`, classe `octave` (Chopin Étude e Clair de Lune) |
| `rotate` | 8 ocorrências, todas `arpeg` a −90° (Nocturne e Clair de Lune) |
| `hidden` | 116 nós, todos `note` |
| `letterSpacing` | 0,0 em 100% dos runs |
| `family` do texto | só `"Times"` (294) e `"Times, serif"` (123) — os dois significam Liberation Serif |
| Alinhamento do texto | `center` 195 · `left` 191 · `right` 31 |
| Tamanhos de texto | 405 (229×), 324 (175×), 303 (8×), 607 (5×) |
| Estilos de texto | 268 itálicos, 122 negritos, 50 bold+italic (todos no Clair de Lune) |
| Classes com `id` mais frequentes | `note` 10 068 · `stem` 7 792 · `accid` 5 795 · `chord` 1 686 · `beam` 1 519 · `measure` 615 |
| Formas desenhadas por página | mediana 1 345, máximo 2 463 |
| Nós dinâmicos (ids do timemap) por página | mediana 308, máximo 719 |
| Segmentos alternados por página (A01a) | mediana **196**, máximo **545** |
| Ids do timemap **ausentes** da cena | Gymnopédie 180, Maple Leaf Rag 883 (sufixo `-rend2`, repetição/expansão) — resolvidos pela regra do sufixo desde E02a (`VsbDocument.sceneIdOf`/`passOf`); a fase E inteira (E01a-E05) fechou a execução dessas repetições de ponta a ponta |
| `measureOn` no timemap | preenchido desde E01b (`includeMeasures: true`); Gymnopédie 78 entradas com `measureOn` (31 `-rend2`), igual ao nº de ocorrências de compasso |

### Repetições no corpus (medido em 2026-09-21, base da fase E)

A cena é desenhada do documento **notado**. O timemap vem de uma cópia
expandida (`Toolkit::SetMidiDoc`), em que cada trecho repetido é um clone com
ids `<id>-rend<N>` (N-ésima execução). Compassos em ordem de documento, base 1:

| Peça | Marcação | Verovio em 2026-09-21 | Verovio depois de E04a/E04b | Ocorrências de compasso |
| --- | --- | --- | --- | --- |
| Gymnopédie (MusicXML) | 1 ritornelo, casas 1 (32-39) e 2 (40-47) | correto | correto | 78 |
| Maple Leaf Rag (MusicXML) | 4 ritornelos, 4 casas 1, 3 casas 2 | perde o 1º ritornelo (casa 1 sem casa 2) | **corrigido em E04b** | 130 → 145 |
| Mazurka (MEI, 3 `section`) | 2 ritornelos | não expandia (várias `section`) | **corrigido em E04a** | 75 → 117 |
| Butterfly (MEI, 2 `section`) | 1 ritornelo | não expandia | **corrigido em E04a** | 42 → 48 |
| Little bird (MEI, 3 `section`) | 2 ritornelos | não expandia | **corrigido em E04a** | 39 → 69 |
| Scarlatti (MEI, 2 `section`) | 1 ritornelo | não expandia | **corrigido em E04a** | 68 → 99 |
| Étude, Nocturne, Clair de Lune, Prelude | nenhuma | — | — | = nº de compassos |

- No Dart de antes da fase E, as notas `-rend2` eram ignoradas (nada acendia
  na 2ª passagem) e `ScoreTimeline` só conhecia a 1ª ocorrência de cada
  compasso — resolvido em E02a-E02c. A paginação e os saltos abaixo são os
  de antes de P01b/P01c (sem os padrões `--header none --footer none
  --no-instrument-labels`); **ver "Saltos e pontos de chegada (P01c)"
  abaixo para os números atuais** — a paginação mudou (mais compassos cabem
  por página) e vários saltos que cruzavam página deixaram de cruzar.
- Saltos entre páginas (medido em 2026-09-21, **desatualizado, ver P01c**):
  Maple Leaf Rag 34 → 19 (página 1 → 0) e 67 → 52 (página 2, a última, → 1).
  Saltos na mesma página: Gymnopédie 39 → 1, Maple Leaf Rag 84 → 69 (a peça
  tem um compasso de anacruse antes do compasso 1 marcado no arquivo, que
  conta como ocorrência 1 na ordem de documento — por isso os índices de
  compasso ficam sempre uma unidade acima do atributo `number` do MusicXML;
  corrigido em E01a, que tinha herdado `83 → 69` de uma contagem sem a
  anacruse).
- Além desses três, `repeat-order.py` (E01a) lista mais três saltos "casa 1 →
  casa 2" na Maple Leaf Rag (33 → 35, 66 → 68, 83 → 85): a 2ª passagem de cada
  ritornello pula o compasso da casa 1 e salta direto para a casa 2, sempre na
  mesma página.
- Tirar o `-rendN` concorda com o `-t expansionmap` do Verovio em 2 933 de
  2 933 ids de timemap (com `--xml-id-seed`). O mapa completo tem 50-207 KB de
  JSON por peça.
- O corpus não tem D.C., D.S., coda, fine, `times` nem casas em MEI (E01a cria
  partituras mínimas para esses casos). `--expand-never` **não** é "tocar sem
  repetição": toca a ordem notada, com as duas casas.

### Saltos e pontos de chegada (P01c, medido em 2026-09-22)

Mesmo método de `repeat-order.py` (E01a), sobre os `.vsb` regenerados com os
padrões do bridge (`--header none --footer none --no-instrument-labels`,
D-VSB-PADRAO/P01b). A paginação mudou (mais compassos cabem por página), mas
o total de páginas do corpus continua **34**: nenhuma peça ganhou nem perdeu
página, só os pontos de quebra andaram. É a entrada de P02b (pontos de
chegada das repetições).

| Peça | Páginas | Salto (origem → destino) | Página origem → destino | Destino é 1º compasso de página normal? |
| --- | --- | --- | --- | --- |
| Gymnopédie | 2 | 39 → 1 | 0 → 0 (mesma página) | sim (compasso 1) |
| | | 31 → 40 | 0 → 0 (mesma página) | não |
| Maple Leaf Rag | 3 | 17 → 2 | 0 → 0 (mesma página) | não |
| | | 16 → 18 | 0 → 0 (mesma página) | não |
| | | 34 → 19 | 0 → 0 (mesma página) | não |
| | | 33 → 35 | 0 → 0 (mesma página) | não |
| | | 67 → 52 | 1 → 1 (mesma página) | não |
| | | 66 → 68 | 1 → 1 (mesma página) | não |
| | | **84 → 69** | **2 → 1** | não |
| | | 83 → 85 | 2 → 2 (mesma página) | não |
| Mazurka | 3 | 17 → 1 | 0 → 0 (mesma página) | sim (compasso 1) |
| | | **42 → 18** | **1 → 0** | não |
| Butterfly | 3 | 6 → 1 | 0 → 0 (mesma página) | sim (compasso 1) |
| Little bird | 2 | 9 → 1 | 0 → 0 (mesma página) | sim (compasso 1) |
| | | **30 → 10** | **1 → 0** | não |
| Scarlatti | 3 | **31 → 1** | **1 → 0** | sim (compasso 1) |

Negrito = salto que cruza página: 5 no total (Maple Leaf Rag, Mazurka, Little
bird, Scarlatti; Butterfly não tem nenhum). A medição de 2026-09-21 (acima,
"Repetições no corpus") não é comparável número a número com esta: além da
paginação nova (P01b), ela foi feita **antes** de E04a/E04b corrigirem a
expansão (a Maple Leaf Rag daquele dia perdia o 1º ritornelo, 130 em vez de
145 ocorrências) — ainda assim, o padrão geral bate: a Maple Leaf Rag
continua sendo a peça com mais saltos (8) e menos deles cruzando página (1
de 8, contra 2 de 6 antes). Destino já sendo o 1º compasso de uma página
normal (Gymnopédie, Mazurka, Butterfly, Little bird, Scarlatti - o compasso 1
de cada peça, sempre) descarta a alternativa ali: a página normal já serve.
Os saltos em negrito cujo destino **não** é o 1º compasso de página normal
(Maple Leaf Rag 84 → 69) são candidatos reais a página alternativa (P02b).

## Decisões pendentes

| Id | Pergunta | Bloqueia | Recomendação |
| --- | --- | --- | --- |
| D-NOME | Nome do formato, extensão e flags de CLI | — | Resolvida em S01 (2026-09-17): `.vsb`, `-t vsb`, `-t vsb-json`; timemap embutido quando disponível |
| D-BIN | Vale trocar JSON por encoding binário? | — | Em aberto, sem passo no plano: só decidir com números reais do `zywny` na mão (decisão do usuário) |
| D-RUNTIME | O app gera `.vsb` em runtime (FFI) ou consome pré-gerado? | — | Resolvida (2026-09-20): **(a) gera no dispositivo**, via FFI com `libverovio.so`. Biblioteca e wrapper C existem em `verovio/bindings/dart/`; empacotamento e isolate ficam no `zywny` |
| D-EXPMAP | Como o leitor chega do id `-rend<N>` do timemap ao nó da cena: regra do sufixo documentada na spec, ou `expansion.json` embutido? | E01b, E02a | Resolvida (2026-09-21): **regra do sufixo**, documentada em `especificacao-v1.md` §2.4 e implementada em `score_bridge` (`VsbDocument.sceneIdOf`/`passOf`, E02a); 0 divergências contra o `-t expansionmap` em 12 388 ids (10 peças + as 13 partituras de E01a); o mapa completo pesa 50-207 KB por peça e teria de ser filtrado |
| D-EXPAND | Corrigir a geração de expansão no fork (MEI com várias `section`/`<ending>`; MusicXML com casa 1 sem casa 2)? | E04a, E04b | Resolvida (2026-09-22): **sim, no fork, isolado** em `expansionmap.cpp`/`iomusxml.cpp`, sem tocar `View`/DCs; desenho byte-idêntico (E04a: as 4 peças MEI do corpus); patch pronto para PR upstream (enviar é decisão do usuário) |
| D-SALTO | O que a vista faz quando a execução salta para outra página? | E03a, E03b | Resolvida (2026-09-22): **haste generalizada** — a mesma regra de A05b com a página de destino atrás (`SweepCurtain.targetPageIndex`, E03a); salto na mesma página não mexe na vista; quando a haste anda nos saltos é E03b |
| D-TOQUE | Qual passagem `seekToElement` escolhe para um elemento tocado mais de uma vez? | E02c | Resolvida (2026-09-22): **a mesma passagem da posição atual, se existir; senão a primeira**; `pass:` explícito sempre ganha; implementada em `ScorePlayer.seekToElement` |
| D-ALT, D-ALT-INDICE, D-ALT-EXTENSAO, D-VSB-PADRAO, D-ALT-MECANISMO | Páginas alternativas do player nas repetições (fase P) | P01-P05 | Resolvidas pelo usuário (2026-09-22) — ver [`P00`](P00-visao-geral-paginas-alternativas.md): o `.vsb` carrega páginas normais + sequências alternativas (via `Toolkit::Select`), cada uma do compasso de chegada até o fim da peça; indexação do usuário inalterada, alternativas só no player; `.vsb` por padrão com `--header none --footer none --no-instrument-labels`. Fase P inteira fechada em P05 (2026-09-22): paridade das alternativas idêntica às normais (34/34 e 18/18 páginas ≥ 99,99%), custo de tamanho/tempo medido em [`relatorio-paginas-alternativas.md`](../relatorio-paginas-alternativas.md) (zero em 6/10 peças do corpus, até +330% no pior caso, 8 sequências) |
| D-META-TITULO | Com `--header none` por padrão, de onde vem `meta.title`? | P01a | Resolvida (2026-09-22, usuário): **(a)** o título que o cabeçalho `auto` mostraria (ou o codificado), sem desenhar; implementada em `Toolkit::ReadBridgeMeta` |
| D-BACKEND | Impeller ou Skia como backend oficial da comparação? | R05a | Resolvida em R05a (2026-09-19): Impeller (média 0,49% × 0,60% Skia); **revista em 2026-09-20 para Skia** (Impeller no Linux não aplica antialiasing — decisão do usuário; corpus re-medido: média 0,008800% Skia × 0,008456% Impeller); ver `compare/README.md` |
| D-RELOGIO | `midi.json` (fiel ao `.mid`) e `timemap.json` divergiam no Chopin Étude (144 bpm × 128 bpm — dois andamentos conflitantes na fonte, `Doc::ExportMIDI` reservava o tick 0 pro `scoreDef.midi.bpm` antes do `<tempo>` do compasso 1 ser lido, então o `.mid` real nunca ganhava o evento de 128) | G01 | Resolvida pelo usuário (2026-09-25): **corrigir no fork**. `Doc::ExportMIDI` (`doc.cpp`) passa a usar o andamento já calculado do 1º compasso (`CalculateTimemap`) em vez do valor do `scoreDef` puro, quando os dois existem — corrige o conflito (Chopin Étude: 2451 divergências → 0) sem mudar nada nas peças sem conflito. Afeta o `.mid` puro também (`-t midi`), não só o `.vsb` — mudança de comportamento em `Toolkit`/`Doc::ExportMIDI`, fora do bridge |

Decisões **já tomadas** (não reabrir): ver "Decisões arquiteturais já tomadas"
no [`CLAUDE.md`](../../CLAUDE.md).

## Riscos conhecidos

1. **Paridade de texto comum** — foi a maior fonte de divergência no projeto
   anterior (de 0,36% média caiu para 0,13% só depois de 4 passos sobre texto).
   Aqui o renderizador é o Flutter, com a mesma TTF que o `resvg` usa, mas
   shaping/hinting podem divergir. **Mitigação:** R04a-R04d são quatro passos
   só para isso, com medição antes/depois em R04d, e R06a-R06c medem o corpus.
   Armadilha específica já identificada: `t.family` vale `"Times"` ou
   `"Times, serif"`, e **nenhum** dos dois é o nome de uma fonte instalada —
   os dois querem dizer Liberation Serif (ver R04a).
2. **Backend gráfico** — Impeller e Skia antialiasam diferente do `tiny-skia`
   (do `resvg`). **Mitigação:** R05a mede os dois e registra o escolhido; a
   tolerância 128/255 ignora diferença de AA de borda por decisão do usuário
   (antes 32/255, que é o que o projeto anterior observava).
3. **Desempenho com página inteira em `CustomPaint`** — uma página do corpus
   tem 1 345 formas na mediana (máximo 2 463) e produz ~196 segmentos
   alternados (máximo 545). **Mitigação:** A01a/A01b separam estático
   (compilado uma vez em `ui.Picture`) de dinâmico, com o critério de
   byte-identidade; o perfil em dispositivo é feito no `zywny`.
4. **Tamanho do JSON** — o dicionário de glifos remove a maior repetição, mas
   o corpus é pequeno (5-16 compassos/peça). **Mitigação:** medir tamanho e
   tempo de parse no `zywny` (com uma peça de 20+ páginas, fora do corpus)
   antes de qualquer otimização; encoding binário é decisão do usuário.
5. **`zip_file.hpp` é header-only com o miniz embutido** — incluí-lo em mais de
   uma unidade de tradução gera símbolos duplicados no link. O escritor de zip
   fica em `src/filereader.cpp`, que já o inclui.
6. **Bbox de glifo** — `Glyph::GetBoundingBox()` devolve `[x, y, w, h]` multiplicado por 10 e com o eixo Y para cima, enquanto os contornos SMuFL estão divididos por 10 e com Y para baixo. O exportador agora faz essa conversão (S08) e o parser Dart representa o campo com `GlyphBBox`, evitando confundi-lo com um `Rect` de contorno.
7. **Divergir do Verovio upstream (fase E)** — E04a/E04b mudam o importador
   e o gerador de expansão, que não são código do exportador. Um erro ali
   muda o timemap (o que toca), mas não o desenho, porque para `svg`/`vsb`
   só o `m_midiDoc` é expandido. **Mitigação:** cada passo prova `scene.json`,
   `glyphs.json` e `-t svg` byte-idênticos, trava os timemaps das peças fora
   do escopo e deixa o patch pronto para PR upstream, para não carregar a
   divergência para sempre.

## Passos

| Passo | Título | Depende de | Decisão | Status |
| --- | --- | --- | --- | --- |
| [F01](F01-montar-repositorio.md) | Montar o repositório a partir do fork validado | — | — | concluído com ressalva |
| [F02](F02-corpus-e-referencia-svg.md) | Corpus + referência SVG→PNG reproduzível | F01 | — | concluído |
| [S01](S01-especificacao-do-formato.md) | Fechar a especificação do formato `.vsb` | F01 | D-NOME resolvida | concluído |
| [S02](S02-bridge-device-context.md) | `BridgeDeviceContext`: renomear e limpar a IR | F01, S01 | — | concluído |
| [S03](S03-dicionario-de-glifos.md) | Dicionário de glifos + instâncias (substitui o baking) | S02 | — | concluído |
| [S04](S04-bboxes-e-indice.md) | Bounding boxes e índice de elementos endereçáveis | S02 | — | concluído (ressalva resolvida em 2026-09-19, ver notas do passo) |
| [S05](S05-writer-json.md) | `BridgeWriter`: IR → `scene.json`/`glyphs.json` | S01, S02, S03, S04 | — | concluído |
| [S06](S06-toolkit-e-cli.md) | `Toolkit` + CLI (`-t vsb-json`, todas as páginas) | S05 | D-NOME resolvida | concluído |
| [S07](S07-pacote-vsb.md) | Pacote `.vsb` (zip) com timemap embutido | S06 | — | concluído |
| [S08](S08-corrigir-bbox-de-glifo.md) | **Corrigir a escala e o eixo da bbox de glifo** | S04, S07 | — | concluído |
| [R01](R01-pacote-dart-e-parser.md) | Pacote `score_bridge`: modelo + parser | S05 | — | concluído |
| [R02a](R02a-geometria-para-path.md) | Geometria: `v`/`i`/`o` → `ui.Path` | R01 | — | concluído |
| [R02b](R02b-percurso-e-ajuste-de-pagina.md) | Percurso da árvore, ajuste de página e cor herdada | R02a | — | concluído |
| [R02c](R02c-formas-traco-e-preenchimento.md) | Formas: traço, opacidade, cap/join, tracejado | R02b | — | concluído |
| [R02d](R02d-primeira-imagem.md) | Primeira imagem: `scene-to-png` mínimo e sobreposição | R02c, F02 | — | concluído |
| [R03a](R03a-cache-de-glifos.md) | `GlyphCache`: `glyphId` → `ui.Path` | R02a, S03 | — | concluído |
| [R03b](R03b-instancias-de-glifo.md) | Instâncias `u`: transformação, traço e herança | R03a, R02c | — | concluído |
| [R03c](R03c-paridade-de-glifos.md) | Paridade parcial só com formas e glifos | R03b, R02d | — | concluído |
| [R04a](R04a-fontes-e-familia.md) | Fontes: carregar as TTFs e resolver `family` | R02b | — | concluído |
| [R04b](R04b-baseline-e-tamanho.md) | Run de texto: linha de base, tamanho e cor | R04a | — | concluído |
| [R04c](R04c-alinhamento.md) | Alinhamento e `letterSpacing` | R04b | — | concluído |
| [R04d](R04d-estilos-e-paridade-de-texto.md) | Bold/itálico e paridade do texto | R04c, R03c | — | concluído |
| [R05a](R05a-backend-grafico.md) | Decisão: backend gráfico (Impeller × Skia) | R03c | backend gráfico | concluído |
| [R05b](R05b-script-ponta-a-ponta.md) | `compare-page.sh` no fluxo `.vsb`, ponta a ponta | R05a, R04d | — | concluído |
| [R05c](R05c-widget-vs-harness.md) | Prova widget-vs-harness (0 pixels) | R05b | — | concluído |
| [R06a](R06a-varredura-do-corpus.md) | Varredura do corpus: CSV das 34 páginas | R05b, R05c, S06 | — | concluído |
| [R06b](R06b-investigacao-de-divergencias.md) | Investigação das páginas acima de 0,1% | R06a | — | concluído |
| [R06c](R06c-relatorio-de-paridade.md) | Relatório de paridade e mesa de prova (**portão**) | R06b | — | concluído |
| [A01a](A01a-segmentacao.md) | Segmentação da página por ordem de documento | R06c | — | concluído |
| [A01b](A01b-cache-de-picture.md) | `ScorePageView`: camadas e cache de `ui.Picture` | A01a | — | concluído |
| [A01c](A01c-score-controller.md) | `ScoreController` (cor instantânea) e medições | A01b | — | concluído |
| [A02a](A02a-motor-de-animacao.md) | Motor de animação: um `Ticker`, fases e curvas | A01c | — | concluído |
| [A02b](A02b-api-de-destaque.md) | API de destaque e restauração da cor original | A02a | — | concluído |
| [A02c](A02c-evidencia-e-desempenho.md) | Evidência visual e orçamento de frame | A02b | — | concluído |
| [A03a](A03a-trilha-de-paginas.md) | `ScoreView`: trilha de páginas e navegação direta | A01b | — | concluído |
| [A03b](A03b-virada-animada.md) | Virada por haste: `pagedSweep` e `pagedSlide` | A03a, A02b, A04a | — | concluído |
| [A03c](A03c-rolagem-continua.md) | `continuousScroll`, `scrollToId` e cache de páginas | A03b | — | concluído |
| [A04a](A04a-coordenadas-e-hit-test.md) | Coordenadas e hit-test: `rectForId` e `idAt` | A01b, S04, S08 | — | concluído |
| [A04b](A04b-overlay-e-gestos.md) | Overlay de widgets, toque e `ScoreCursor` | A04a | — | concluído |
| [A05a](A05a-score-player.md) | `ScorePlayer`: relógio próprio e timemap → destaque | A02b, S07 | — | concluído |
| [A05b](A05b-virada-automatica-e-evidencias.md) | Virada automática por compasso e evidências | A05a, A03b | — | concluído |
| [E01a](E01a-corpus-de-repeticoes.md) | Corpus de repetições, roteiro esperado e diagnóstico | A05b | — | concluído |
| [E01b](E01b-timemap-com-compassos.md) | Timemap com `measureOn` no `.vsb` e contrato dos ids `-rendN` | E01a | D-EXPMAP resolvida | concluído |
| [E02a](E02a-ids-expandidos.md) | Ids expandidos (`-rendN`) chegam à nota desenhada | E01b | — | concluído |
| [E02b](E02b-linha-do-tempo-por-ocorrencia.md) | `ScoreTimeline` por ocorrência de compasso | E02a | — | concluído |
| [E02c](E02c-tocar-a-partir-de-elemento.md) | Tocar a partir de um elemento repetido (`seekToElement`) | E02b | D-TOQUE resolvida | concluído |
| [E03a](E03a-haste-com-pagina-de-destino.md) | Haste com página de destino (mecanismo) | E02b | D-SALTO resolvida | concluído |
| [E03b](E03b-regra-da-haste-nos-saltos.md) | Regra da haste nos saltos e evidências | E03a | — | concluído |
| [E04a](E04a-expansao-mei.md) | Expansão de MEI com várias `section` e `<ending>` (fork) | E01a | D-EXPAND resolvida | concluído |
| [E04b](E04b-expansao-musicxml-casa-unica.md) | MusicXML: casa 1 sem casa 2 (fork) | E04a | — | concluído |
| [E05](E05-portao-das-repeticoes.md) | Portão da fase E: repetições de ponta a ponta | E02c, E03b, E04b | — | concluído |
| [P00](P00-visao-geral-paginas-alternativas.md) | **Visão geral da fase P** (leitura obrigatória, não executável) | — | — | — |
| [P01a](P01a-titulo-sem-cabecalho.md) | `meta.title` sem depender do cabeçalho desenhado | — | D-META-TITULO resolvida | concluído |
| [P01b](P01b-padroes-do-vsb.md) | Padrões do `.vsb`: sem cabeçalho, rodapé e rótulo | P01a | D-VSB-PADRAO resolvida | concluído |
| [P01c](P01c-remedir-corpus.md) | Regenerar corpus e fixtures, re-medir paridade e fatos | P01b | — | concluído |
| [P02a](P02a-especificacao-alternates.md) | Especificação: `alternates.json` | — | D-ALT resolvida | concluído |
| [P02b](P02b-pontos-de-chegada.md) | C++: pontos de chegada das repetições | P01c, P02a | — | concluído |
| [P02c](P02c-render-das-alternativas.md) | C++: renderizar as sequências e gravar `alternates.json` | P02b | D-ALT-MECANISMO resolvida | concluído |
| [P02d](P02d-paridade-das-alternativas.md) | Referência SVG (`--select-from`) e paridade das alternativas | P02c, P03a | — | concluído |
| [P03a](P03a-modelo-e-parser-alternates.md) | Dart: modelo, parser e geometria das alternativas (`PageRef`) | P02a, P02c | — | concluído |
| [P03b](P03b-vista-com-pageref.md) | Dart: `ScorePageView`/`ScoreView` exibem um `PageRef` | P03a, P02d | D-ALT-INDICE resolvida | concluído |
| [P04a](P04a-rota-na-timeline.md) | Dart: rota de exibição na `ScoreTimeline` | P03b | — | concluído |
| [P04b](P04b-player-com-alternativas.md) | Dart: `ScorePlayer` segue a rota | P04a | — | concluído |
| [P04c](P04c-evidencias.md) | Evidências visuais das páginas alternativas | P04b | — | concluído |
| [P05](P05-portao-das-paginas-alternativas.md) | Portão da fase P: páginas alternativas de ponta a ponta | P02d, P04c | — | concluído |
| [G01](G01-gravador-de-notas-midi.md) | `midi.json` no `.vsb`: eventos do exportador MIDI (notas + pedal) com `xml:id` | — | D-RELOGIO resolvida | concluído |
| [G02](G02-notas-no-score-bridge.md) | `score_bridge`: modelo e parser de `midi.json` | G01 | — | concluído |

Ordem sugerida, a partir de onde o projeto está (S08 e R01 concluídos):

```
R02a → R02b → R02c → R02d → R03a → R03b → R03c
                ↘ R04a → R04b → R04c ↗
        R04d → R05a → R05b → R05c → R06a → R06b → R06c   ← portão
        A01a → A01b → A01c → A02a → A02b → A02c
                           ↘ A03a → A03b → A03c
                             A04a → A04b        (usa as bboxes corrigidas em S08)
                             A05a → A05b
        E01a → E01b → E02a → E02b → E02c ─────┐
            │                   ↘ E03a → E03b ─┤
            └→ E04a → E04b ────────────────────┴→ E05   (fase E: repetições)

        P01a → P01b → P01c ─┐                    (fase P: páginas alternativas;
        P02a ───────────────┴→ P02b → P02c ─┐     leia P00 antes de qualquer P*)
                              P03a ─────────┴→ P02d → P03b → P04a → P04b → P04c → P05

        G01 → G02                                 (fase G: notas MIDI para tocar,
                                                    independente das demais)
```

A fase G grava, num `midi.json` opcional do `.vsb` (G01, C++), os eventos
que o exportador MIDI do Verovio emite — notas (pitch já com
8va/transposição, ligaduras unidas, ornamentos expandidos) e pedal — em ms e
com o `xml:id` de origem, e os lê no `score_bridge` (G02, Dart). Não
depende de F/S/R/A/E/P nem é consumida por nenhuma delas — é o host (zywny)
quem usa `midi.json` para tocar a partitura por soundfont, mandar MIDI para
um teclado externo e avaliar o aluno (`docs/plano/N01`..`N03` do zywny,
cross-repo).

A fase P faz o player, num salto de repetição para outra página, mostrar uma
página **redesenhada** que começa no compasso de chegada, em vez da página
original. A visão geral, as decisões e as regras estão em
[`P00`](P00-visao-geral-paginas-alternativas.md).

A fase E corrige a execução de peças com repetição. E02-E03 são o lado Dart
(valem já para as peças MusicXML, que o Verovio expande). E04 é o lado C++
(faz as peças MEI e a Maple Leaf Rag expandirem certo). As duas trilhas são
independentes depois de E01a.

S08 já foi executado e o corpus em `compare/out/s08/` traz as bboxes
corrigidas; todo número de bbox medido antes dele (S07) está errado.
R06c fechou o portão de paridade em 2026-09-20 (média 0,008456%, ver
[`docs/relatorio-paridade.md`](../relatorio-paridade.md)) — a fase A está
liberada, começando por A01a. **Fase E concluída em 2026-09-22**
(E01a-E05): a varredura de paridade repetida em E05 sobre os `.vsb`
regenerados deu média **0,008800%** (Skia), idêntica à medição de
R06c/2026-09-20 — nenhuma página mudou de percentual, confirmando que
nenhuma mudança da fase E (toda em `score_bridge`/`expansionmap.cpp`/
`iomusxml.cpp`) afetou o desenho. **Fase P concluída em 2026-09-22**
(P01a-P05): páginas alternativas com a mesma paridade das normais (34/34 e
18/18 páginas ≥ 99,99%, médias 0,006402%/0,006514% — ver
[`relatorio-paridade.md`](../relatorio-paridade.md)); custo de
tamanho/tempo medido, não otimizado (D-BIN continua aberta), em
[`relatorio-paginas-alternativas.md`](../relatorio-paginas-alternativas.md).

**Passos pequenos de propósito.** Cada arquivo acima cabe numa sessão de
trabalho e tem critérios de aceite executáveis. Não junte dois passos "porque
são parecidos": a razão de existirem separados é que o critério de aceite de
cada um é verificável sozinho — é isso que impede um erro de percorrer três
passos antes de aparecer.
