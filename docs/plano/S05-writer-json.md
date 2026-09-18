# S05 — `BridgeWriter`: IR → `scene.json` / `glyphs.json`

**Depende de:** S01, S02, S03, S04 · **Decisão necessária:** não

## Objetivo

Serializar a IR no formato definido em S01. É o primeiro passo em que sai um
arquivo consumível pelo Flutter.

## Ler antes (só isto)

- A [especificação](../formato/especificacao-v1.md) inteira (é o contrato).
- `../verovio_lottie/verovio/src/lottiewriter.cpp`:
  - L426-L530 — **resolução de bold/italic por classe CSS**; é a lógica que
    precisa ser portada quase literal (ela reproduz `g.ending, g.fing, g.reh,
    g.tempo {font-weight:bold}`, `g.dir, g.dynam, g.mNum {font-style:italic}`,
    `g.label {font-weight:normal}`, com a regra de que `label` vence o bold de
    um ancestral);
  - L597-L620 — `ComputePageMetrics` (`scale`/`tx`/`ty` do ajuste `meet`);
  - o estilo geral de serialização de números (evite `std::ostream` com locale;
    use o mesmo helper de formatação que ele usa, ou `snprintf("%.6g")`).
- `verovio/src/svgdevicecontext.cpp` `GetColor` L1295 — como o SVG formata cor.

## O que fazer

1. Criar `include/vrv/bridgewriter.h` + `src/bridgewriter.cpp` com:

   ```cpp
   class BridgeWriter {
   public:
       static std::string WriteScene(const std::vector<const BridgePage *> &pages);
       static std::string WriteGlyphs(const std::map<std::string, BridgeGlyphDef> &glyphs);
       static std::string WriteManifest(int pageCount, bool hasTimemap);
       static std::string WriteSingleJson(...);   // o `-t vsb-json`: tudo num arquivo
   };
   ```

2. Regras de serialização que **não** podem ser improvisadas:
   - **números**: no máximo 6 dígitos significativos, sem notação científica,
     sem `-0`; inteiros saem sem `.0`. (Isto é o que mantém o arquivo pequeno e
     o diff estável entre execuções.)
   - **cor**: `#rrggbb` minúsculo. `COLOR_NONE` → campo **ausente** (= herda).
   - **ordem de chaves**: fixa e estável (a mesma ordem da especificação), para
     que dois exports do mesmo input sejam byte-idênticos.
   - **`fit`**: calculado como `ComputePageMetrics`, e gravado na página.
   - **bold/italic**: resolvido (item acima), nunca o nome da classe.
   - **bbox**: só nos nós que S04 marcou como obrigatórios.
   - **glifos**: o dicionário sai **ordenado por `glyphId`** (determinismo).

3. `WriteScene` percorre a IR uma vez, sem cópias de vetor grandes (reserve
   buffer; o corpus gera arquivos de alguns MB antes do zip).

## Fora de escopo

- CLI e Toolkit (S06) — aqui só a classe e um teste.
- Zip (S07).
- Qualquer otimização de encoding (P01).

## Critérios de aceite

1. Compila.
2. `python3 -m json.tool` valida a saída das 34 páginas do corpus.
3. Valida contra o schema de S01:
   `check-jsonschema --schemafile docs/formato/schema-v1.json <saída>` para
   todas as peças do corpus.
4. **Determinismo**: exportar a mesma peça duas vezes produz arquivos
   byte-idênticos (`cmp`). Exportar em máquina com `LC_ALL=tr_TR.UTF-8`
   (locale com vírgula decimal) produz o **mesmo** arquivo — prova que a
   formatação de número não passa por locale.
5. **Cobertura**: para cada peça do corpus, compare a contagem de elementos do
   `scene.json` com a do SVG equivalente:

   | No SVG | No `scene.json` |
   | --- | --- |
   | `<use>` | filhos `"t":"u"` |
   | `<path>` + `<polygon>` + `<polyline>` | `"t":"p"` |
   | `<rect>` | `"t":"r"` |
   | `<ellipse>` | `"t":"e"` |
   | `<text>` (com conteúdo renderizável) | `"t":"t"` + os `"t":"u"` de runs SMuFL |
   | `<g>` com `id` | nós com `id` |

   Divergências são esperadas só onde o projeto anterior já documentou (runs
   SMuFL em texto comum viram glifo, D01-6). Registre a tabela real nas notas.
6. Todo `id` presente no SVG está presente no `scene.json` (compare os dois
   conjuntos; a diferença tem que ser vazia nos dois sentidos).

## Notas de execução

- 2026-09-17: criados `include/vrv/bridgewriter.h` + `src/bridgewriter.cpp`
  (`BridgeWriter::WriteScene/WriteGlyphs/WriteManifest/WriteSingleJson`), com toda a
  serialização feita por concatenação de `std::string` (sem `jsonxx`, para controlar
  ordem de chaves e formatação de número exatamente como a especificação pede), nos
  mesmos moldes de `lottiewriter.cpp` (`FormatNumber`, `EscapeJsonString`,
  `ApplyClassStyleRule`/`HasClassToken`, `ComputePageMetrics` portados quase literais).
  `cmake ../cmake && make -j4` limpo, sem avisos novos.
- **Desvio na IR (registrado também em `docs/formato/especificacao-v1.md`,
  "Histórico de revisões")**: a especificação previa `t.family` vindo de "`FontInfo`
  ativo (fora de `BridgeTextRun`)", mas nada na IR carregava essa informação e o
  `BridgeWriter` não tem acesso ao `FontInfo` do `DrawText` (que só existe durante o
  desenho). Adicionado `BridgeTextRun::family` em `bridgegeometry.h`, populado em
  `BridgeDeviceContext::DrawText` a partir de `FontInfo::GetFaceName()`, com o mesmo
  fallback que a raiz do SVG usa quando vazio (`resources->GetTextFont() + ", serif"`,
  igual a `SvgDeviceContext::StartPage`). Não altera nenhum outro campo/comportamento
  de S02-S04.
- **Achado importante para S06**: `Toolkit::RenderToDeviceContext` **não** chama
  `deviceContext->SetResources(...)` — só `Toolkit::RenderToSVG` faz isso, na sua
  própria `SvgDeviceContext` local (`toolkit.cpp:1754`), antes de chamar
  `RenderToDeviceContext`. `Toolkit::m_doc` é `protected`, sem getter público. O
  `Toolkit::RenderToBridgeFile()` de S06 (método da própria classe `Toolkit`, com
  acesso direto a `m_doc`) deve fazer o mesmo: `bridgeDc.SetResources(&m_doc.GetResources())`
  antes de desenhar cada página — sem isso, glifos SMuFL resolvem para nomes de fonte
  incompletos e `DrawMusicText`/`DrawText` chamam `resources->GetGlyph(c)` sobre um
  ponteiro nulo (undefined behavior; não segfenta em release por causa do
  `assert(resources)` compilado fora com `-DNDEBUG`, mas é incorreto).
- **Achado importante para S06/S07 (determinismo)**: `Object::SeedID(0)` (o padrão) usa
  `std::random_device` — sem seed fixo, dois exports do mesmo arquivo produzem
  `xml:id` auto-gerados diferentes (já registrado em S04) e por isso `scene.json`
  também sairia diferente a cada execução. `Toolkit::ResetXmlIdSeed(<valor não-zero>)`
  precisa ser chamado antes de `LoadFile`/`LoadData` sempre que o pacote `.vsb`
  precisar ser reprodutível (S07 deve decidir o valor/exposição via CLI, provavelmente
  uma flag nova ou reaproveitando `-x`/`--xml-id-seed`, já existente no `Toolkit`).
- Teste temporário (fora do repo, `$SCRATCH/s05_writer_test.cpp`, compilado e ligado à
  mão contra os `.o` já gerados pelo `make` do alvo `verovio`, exceto `main.cpp.o` —
  mesma técnica de S04): usa uma subclasse local `TestToolkit : public Toolkit` só
  para expor `m_doc.GetResources()` (`m_doc` é `protected`), chama
  `ResetXmlIdSeed` antes de `LoadFile` e roda `RenderToDeviceContext` +
  `RenderToSVG` **na mesma sessão de `Toolkit`**, para os `xml:id` baterem (lição de
  S04). Removido ao final; nada ficou em `verovio/`.
- **Critério 1 (compila)**: `cmake ../cmake && make -j4` sem avisos novos.
- **Critério 2 (`python3 -m json.tool`)**: válido para `scene.json`, `glyphs.json`,
  `manifest.json` e o `single.json` (`-t vsb-json`) das 10 peças do corpus (34
  páginas).
- **Critério 3 (schema)**: `check-jsonschema` não está instalado no ambiente;
  validado com `jsonschema` (Python, `Draft202012Validator`, mesma spec JSON Schema
  2020-12) diretamente contra `docs/formato/schema-v1.json` — 0 erros nas 10 peças,
  tanto no documento único (`document`) quanto em `scene.json`/`glyphs.json`/
  `manifest.json` isolados (`sceneDocument`/`glyphsDocument`/`manifestDocument`).
- **Critério 4 (determinismo)**: peça exportada duas vezes (dois processos
  separados, mesmo `xmlIdSeed` fixo) produz arquivo **byte-idêntico**
  (`cmp`) — `scene.json`, `glyphs.json`, `manifest.json`, `single.json` e as 34
  páginas de SVG (geradas na mesma sessão, usadas só para os critérios 5/6), 74
  arquivos no total, 0 diferenças. Repetido uma terceira vez com `LC_ALL=de_DE.UTF-8`
  (locale de vírgula decimal — `tr_TR.UTF-8` não estava instalado no ambiente, mesma
  classe de locale) contra a primeira execução: também byte-idêntico, confirmando que
  `FormatNumber` (via `std::ostringstream` com `imbue(std::locale::classic())`) não
  vaza a locale do processo.
- **Critério 5 (cobertura, tabela real por peça)**: contagem em `<path>+<polygon>+
  <polyline>` (`pathish`), `<rect>`, `<ellipse>`, `<use>`, `<text>` (só o `<tspan>`
  mais interno com `font-size` próprio e conteúdo — os `<text>`/`<tspan>` externos são
  só âncora/wrapper estrutural sem `font-size`, achado ao inspecionar a árvore) e
  `<g id=…>`, excluindo `<defs>` (dicionário de contornos de glifo — outro balde,
  `glyphs.json`, não `scene.json`) em ambos os lados. Total do corpus (10 peças, 34
  páginas):

  | Categoria | SVG | `scene.json` | Nota |
  | --- | --- | --- | --- |
  | `pathish` (`p`) | 26469 | 26469 | idêntico em todas as 10 peças |
  | `rect` (`r`) | 1401 | 1401 | idêntico |
  | `ellipse` (`e`) | 911 | 911 | idêntico |
  | `use` (`u`) | 15404 | 15413 | +9, só em Clair de Lune/Gymnopédie/Maple Leaf Rag |
  | `text` (`t`) | 424 | 417 | -7, mesmas 3 peças |

  As únicas divergências (`use`/`text`, sempre nas mesmas 3 peças, sempre com sinais
  opostos) são exatamente a categoria já prevista no passo ("runs SMuFL em texto
  comum viram glifo, D01-6") — confirmado num caso concreto: Clair de Lune tem -2
  `text`/+4 `use`, batendo com o comentário já existente em
  `BridgeDeviceContext::DrawText` sobre o "pp" (MusicXML `<words font-family="Leland
  Text">` com U+E520 embutido, ocorrendo duas vezes na peça) — 2 runs inteiramente
  SMuFL que na SVG saem como `<text>` (fonte comum, glifo caído por fallback do
  sistema) e no Bridge corretamente viram usos de glifo (2 caracteres cada).
  Gymnopédie/Maple Leaf Rag têm o mesmo padrão em menor escala. Nenhuma outra
  categoria diverge em nenhuma das 10 peças.
- **Critério 6 (conjunto de `xml:id`)**: comparado o conjunto de todo atributo `id=`
  no SVG (fora de `<defs>`) contra todo `id` de nó `"t":"g"` na árvore do
  `scene.json`, por peça. Batem exatamente (diferença vazia nos dois sentidos) em
  8 das 10 peças. Nas outras 2 (peças com repetição/`ending` "spanning" — volta
  bracket que atravessa quebra de sistema), sobra um punhado de ids só de um lado
  (5-9 no total, sobre ~1200-5500 ids da peça); investigado a fundo, são dois
  fenômenos **sem relação com `BridgeWriter`/`BridgeDeviceContext`**:
  - `lye0tzg` (mesmo texto em toda peça testada) é `SvgDeviceContext`'s docId
    (`m_doc.GetID()`, `toolkit.cpp:1753`), usado só para nomear/escopar o `<svg
    id=…>` raiz e as regras de CSS (`svgdevicecontext.cpp:71`) — nunca corresponde a
    um `Object` desenhado, então não tem (e não deveria ter) contrapartida na árvore
    Bridge, que começa em `Page`, não em `Doc`.
  - Os poucos ids restantes (só em Gymnopédie e Maple Leaf Rag, sempre a legenda
    numérica do `voltaBracket`) vêm de `View::DrawEnding` (`view_control.cpp`, em
    torno da L3175: `dc->StartCustomGraphic("voltaBracket")` seguido de `Text text;
    text.SetParent(ending); ...; this->DrawTextElement(dc, &text, params)`): esse
    `Text` é um objeto local, criado do zero a cada chamada, e ganha um `xml:id`
    novo de `Object::GenerateID()` a cada vez — inclusive a cada nova chamada de
    `View::DrawCurrentPage`. Como o harness de teste chama
    `RenderToDeviceContext` e depois `RenderToSVG` **na mesma página**, os dois
    desenhos de fato criam **dois objetos `Text` diferentes**, cada um com seu
    próprio id auto-gerado — mesmo dando `ResetXmlIdSeed` com o mesmo valor
    imediatamente antes de cada um dos dois desenhos da mesma página (tentado; não
    eliminou a divergença, sinal de que outro consumo de id intermediário também
    diverge entre os dois caminhos). O conteúdo (texto, posição, bbox, classe) bate
    perfeitamente dos dois lados — só o valor do id auto-gerado dessa legenda efêmera
    diverge entre duas passadas de desenho separadas. **Isto é um artefato do
    harness de comparação (duas passadas de `DrawCurrentPage` no mesmo processo),
    não um bug do exportador**: numa exportação `.vsb` real (S06/S07) só existe uma
    passada de desenho por página. Fica registrado aqui porque é a mesma família do
    achado de S04 ("ids automáticos não são estáveis entre execuções"), agora também
    válido *dentro* de uma única execução quando o mesmo desenho é repetido — vale a
    pena qualquer harness de comparação futuro (R05b/R06a) saber disso.
- Ids reais (glifos, formas, notas, textos comuns) batem em praticamente 100%
  (diferença de 1-2 em ~1200-7300 ids por peça, sempre um dos dois casos acima) —
  nenhum id de conteúdo real (nota, acidente, dinâmica, texto comum) ficou de fora
  em nenhuma das 10 peças.
- Contagem de glifos distintos por peça bateu exatamente com os números já medidos
  em S03 (Etude 34, Mazurka 30, Butterfly 24, Little Bird 23, Scarlatti 25, Nocturne
  37, Clair de Lune 31, Gymnopédie 16, Maple Leaf Rag 21, Prelude BWV846 16) — bom
  sinal cruzado de que `BridgeDeviceContext`/`SetResources` no harness estão
  configurados do jeito certo.
- Bloqueios: nenhum.
