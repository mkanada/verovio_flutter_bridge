# R01 — Pacote `score_bridge`: modelo Dart + parser

**Depende de:** S05 (ou só S01, usando `docs/formato/exemplo-minimo.json`)
· **Decisão necessária:** não

## Objetivo

Criar o pacote Flutter que o app vai consumir e fazer ele **ler** o formato:
modelo imutável, parser de `.vsb` (zip) e do JSON único, índice por `xml:id`.
Nada de desenho ainda.

## Ler antes (só isto)

- A [especificação](../formato/especificacao-v1.md), seções 2 a 5.
- `docs/formato/exemplo-minimo.json` (o fixture de S01).
- Um `scene.json` real do corpus, se S05 já existir.

## O que fazer

1. `flutter create --template=package score_bridge` na raiz do repositório.
   Dependências: `archive` (ler o zip). Nada além do necessário — este pacote
   vai para dentro de um app; cada dependência é peso.

2. Modelo (`lib/src/model.dart`), imutável, com `const` onde der:

   ```dart
   class VsbDocument { final VsbManifest manifest; final Map<String, GlyphDef> glyphs;
                       final List<ScenePage> pages; final Timemap? timemap; }
   class ScenePage { final int index; final double widthPx, heightPx;
                     final Rect viewBox; final PageFit fit; final Offset origin;
                     final SceneNode root; final Map<String, SceneNode> byId; }
   sealed class SceneChild {}
   class SceneNode extends SceneChild { id, className, color, hidden, rotate, bbox, children }
   class ScenePath extends SceneChild { subpaths, fill, stroke, ... }
   class SceneRect / SceneEllipse / SceneGlyphUse / SceneText extends SceneChild
   ```

   Geometria em `Float64List` (os arrays planos do formato), **sem** converter
   para `List<Offset>` — é o que mantém o parse rápido e a memória baixa.

3. Parser (`lib/src/parser.dart`):
   - `VsbDocument.fromBytes(Uint8List)` — detecta zip (assinatura `PK`) ou JSON;
   - `VsbDocument.fromJson(Map<String, dynamic>)`;
   - constrói `byId` durante o percurso (uma passada só);
   - **rejeita** `version` desconhecida com uma exceção clara
     (`UnsupportedVsbVersionException`), nunca renderiza parcial;
   - **ignora** chaves desconhecidas (seção 7 da especificação).

4. Erros: uma exceção `VsbFormatException` com caminho JSON do campo culpado
   (ex.: `pages[2].children[17].v`). Depurar formato sem isso é sofrimento.

## Fora de escopo

- Qualquer `Canvas`/`Path`/pintura (R02).
- Widget (A01).
- Cache de `Picture` (A01).

## Critérios de aceite

1. `cd score_bridge && flutter analyze` sem avisos; `dart format --set-exit-if-changed .` limpo.
2. `flutter test` com, no mínimo:
   - parse do `exemplo-minimo.json` conferindo **todos** os campos contra
     valores escritos à mão no teste (não `toString()`);
   - parse de um `.vsb` real do corpus (fixture copiado para
     `score_bridge/test/fixtures/`), conferindo nº de páginas, nº de glifos e
     alguns ids conhecidos;
   - `version: 999` lança `UnsupportedVsbVersionException`;
   - JSON com chave desconhecida em nó/forma **não** lança;
   - JSON com `"v"` de comprimento ímpar lança `VsbFormatException` citando o
     caminho do campo.
3. **Ida e volta de contagem**: para uma peça do corpus, o nº de nós, formas,
   usos de glifo e runs de texto contados no Dart bate exatamente com o contado
   por um script Python sobre o mesmo JSON (teste que roda os dois e compara).
4. `byId` contém todos os ids do índice exportado em S04 (compare os conjuntos).
5. Tempo de parse de cada peça do corpus registrado nas notas (`Stopwatch`,
   3 execuções, mediana) — insumo do gate de P01.

## Notas de execução

- 2026-09-18: `flutter create --template=package score_bridge` na raiz do
  repositório (Flutter 3.47.4 / Dart 3.13.3). Única dependência adicionada:
  `archive: ^4.3.0` (leitura do zip). Estrutura: `lib/src/model.dart` (classes
  imutáveis + `VsbFormatException`/`UnsupportedVsbVersionException`),
  `lib/src/parser.dart` (funções de parse), `lib/score_bridge.dart` (barrel).
- **Modelo segue a especificação seção a seção**, com estas escolhas de
  design não ditadas literalmente pelo esboço do passo (registradas aqui por
  serem decisões, não por serem desvio de um contrato já fechado):
  - `fill`/`stroke` viram uma classe `sealed ScenePaint` de 3 estados
    (`inherit`/`none`/`ColorPaint(hex)`) em vez de `String?` cru — deixa a
    regra de herança do §5.2 explícita no tipo, não em convenção de string.
  - `bbox`/`viewBox`/`origin`/`rotate.origin` usam `dart:ui Rect`/`Offset`
    (o pacote já depende de `flutter`, então `dart:ui` está disponível);
    `v`/`i`/`o` dos beziers continuam `Float64List` plano, como o passo pede
    explicitamente (maior volume de números do formato).
  - `fillOpacity`/`strokeOpacity` ausentes viram `1.0` e `lineCap`/`lineJoin`
    ausentes viram o próprio enum `defaultCap`/`defaultJoin` — em ambos os
    casos a ausência já tem um significado único e documentado no §5.2
    (dash) e no texto (é o "não fizemos nada de especial aqui").
  - **`strokeWidth` fica cru (`double?`, sem sintetizar `1.0`) para os
    quatro tipos de forma, inclusive `p`/`r`/`e`.** A especificação (§8)
    documenta "padrão IR 1.0" para `BridgeShape.strokeWidth`, mas o efetivo a
    aplicar diverge por tipo — `1.0` para forma, `sy` para glifo (§5.3) — e
    decidir isso é decisão de pintura (fora de escopo do R01, "Nada de
    Canvas/Path ainda"). Conferido no corpus real (10 peças de S07): formas
    `p`/`r`/`e` sempre emitem `strokeWidth` explícito (nunca omitido), usos de
    glifo (`u`, 15413 ocorrências) **nunca** emitem `fill`/`stroke`/
    `strokeWidth` no corpus de teste. R02/R03 decidem o default a aplicar
    quando renderizarem.
  - Discriminante `t` de filho desconhecido (nem `g`/`p`/`r`/`e`/`u`/`t`)
    lança `VsbFormatException` — diferente de "chave desconhecida ignorada"
    (§9): é um *tipo* de elemento que o leitor não sabe desenhar, não um
    campo aditivo.
  - `VsbDocument.fromBytes`/`.fromJson` são factory constructors em
    `model.dart` que delegam para funções de nível superior em `parser.dart`
    (`parseVsbDocumentBytes`/`parseVsbDocumentJson`); os dois arquivos se
    importam mutuamente (`model.dart` → `parser.dart` para as factories,
    `parser.dart` → `model.dart` para os tipos) — válido em Dart (não é
    `part of`), confirmado sem erro pelo analyzer.
- **Fixtures**: `docs/formato/exemplo-minimo.json` é lido **direto** de
  `docs/formato/` (caminho relativo `../docs/formato/exemplo-minimo.json`,
  válido porque os testes rodam com cwd em `score_bridge/`), não copiado, para
  nunca divergir do fixture normativo de S01. O `.vsb` real do corpus é
  `Erik_Satie_-_Gymnopedie_No.1.vsb` (S07, `-x 42`, o menor do corpus a
  90.837 bytes), copiado para `score_bridge/test/fixtures/erik-satie.vsb`.
- **Critério 3 (ida e volta de contagem)**: script de referência
  `score_bridge/test/scripts/count_elements.py` (extrai `scene.json` de
  dentro do `.vsb` e conta nós/`p`/`r`/`e`/`u`/`t` por percurso recursivo,
  implementação independente do parser Dart) chamado via `Process.runSync`
  em `test/roundtrip_count_test.dart`. Contagens no fixture batem
  exatamente: 1606 nós, 981 `p`, 0 `r`, 88 `e`, 417 `u`, 21 `t`.
- **Critério 4**: para as 2 páginas do fixture, `Set(byId.keys) ==
  Set(elements[].id)` (1055 ids na página 0, 170 na página 1) e cada
  `byId[id]` aponta para um nó com o mesmo `id`/`class` da entrada do índice.
- **Critério 5 (tempo de parse)**: `score_bridge/tool/measure_parse_time.dart`
  (Stopwatch, 3 execuções, mediana). Precisa rodar sob o Flutter Tester, não
  o Dart SDK puro — `VsbDocument` usa `dart:ui` (`Rect`/`Offset`), que só
  existe no engine Flutter — então a invocação é `flutter test
  tool/measure_parse_time.dart` (`main()` sem argumentos; diretório do
  corpus configurável por `CORPUS_DIR`, default `../compare/out/s07`).
  Medido uma vez, debug/JIT sob `flutter test` (não é número de release/AOT;
  é só a primeira leitura de ordem de grandeza para o gate de P01):

  | Peça | Bytes do `.vsb` | Mediana de parse (ms) |
  | --- | ---: | ---: |
  | Erik_Satie_-_Gymnopedie_No.1 | 90 837 | 29.14 |
  | Grieg_Little_bird_Op43_No4 | 139 008 | 51.59 |
  | Prelude_I_BWV_846 | 145 958 | 45.47 |
  | Scarlatti_Sonata_in_C-major | 169 399 | 75.16 |
  | Grieg_Butterfly_Op43_No1 | 218 336 | 85.97 |
  | Chopin_Mazurka_Op6_No1 | 221 367 | 89.52 |
  | Maple_Leaf_Rag_Scott_Joplin | 310 849 | 106.90 |
  | Clair_de_Lune__Debussy | 381 747 | 150.41 |
  | Chopin_-_Nocturne_Op._9_No._1 | 471 450 | 141.63 |
  | Chopin_Etude_Op10_No9 | 286 268 | 127.81 |

  Sem relação clara e monotônica só com bytes do `.vsb` (o parse decodifica o
  zip + 3 JSONs, então o custo depende também da forma da árvore, não só do
  tamanho comprimido) — dado bruto para P01 comparar contra o encoding
  binário, sem conclusão tirada aqui.
- **Critérios 1/2 (compilação/testes)**: `flutter analyze` sem avisos,
  `dart format --set-exit-if-changed .` limpo, `flutter test` com 21 testes,
  todos passando (`exemplo_minimo_test.dart`, `parser_errors_test.dart`,
  `corpus_fixture_test.dart`, `roundtrip_count_test.dart`).
- Bloqueios: nenhum.
