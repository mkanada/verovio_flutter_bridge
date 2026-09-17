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

(a preencher por quem executar)
