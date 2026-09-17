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

(a preencher por quem executar)
