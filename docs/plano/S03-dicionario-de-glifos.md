# S03 — Dicionário de glifos + instâncias

**Depende de:** S02 · **Decisão necessária:** não

## Objetivo

Parar de "assar" o contorno de cada glifo em cada ocorrência (herança do
Lottie, que não tem `<use>`) e passar a emitir **um contorno por glifo** num
dicionário, com cada ocorrência virando uma referência `{glyphId, x, y, sx, sy}`
— o equivalente exato do `<use>` do SVG. É o que torna o arquivo pequeno **e**
mantém cor por nota possível (a cor fica na instância, não no dicionário: foi
exatamente essa incompatibilidade que travou o D06 do projeto anterior).

## Ler antes (só isto)

- `verovio/src/bridgedevicecontext.cpp`: `MakeGlyphShape` (busque o símbolo; era
  L388-L429), `GetGlyphAdvance` (L431-L444) e os três pontos de chamada
  (`DrawText` no ramo SMuFL, o ramo de run inteiramente SMuFL do D01-6, e
  `DrawMusicText`).
- `verovio/include/vrv/glyph.h` — `GetXML`, `GetUnitsPerEm`, `GetHorizAdvX`,
  `GetBoundingBox`, `GetCodeStr`.
- `verovio/include/vrv/resources.h` — `GetGlyph`, e como se descobre a família
  de fonte corrente (`FontInfo::GetFaceName()` / `Resources::GetCurrentFont()`).
- Seções 4 e 5.3 da [especificação](../formato/especificacao-v1.md).

## O que fazer

1. Em `bridgegeometry.h`, acrescentar:

   ```cpp
   struct BridgeGlyphDef {          // uma entrada do dicionário
       std::string font;            // "Leipzig"
       std::string codepoint;       // "E0A4"
       int unitsPerEm = 0;
       int horizAdvX = 0;
       int bbox[4] = { 0, 0, 0, 0 };
       std::vector<BridgeBezier> paths;   // unidades de fonte, scale(1,-1) já aplicado
   };

   struct BridgeGlyphUse {          // uma ocorrência
       std::string glyphId;         // "Leipzig:E0A4"
       double x = 0.0, y = 0.0, sx = 1.0, sy = 1.0;
   };
   ```

   e um terceiro tipo de filho em `BridgeChild` (ao lado de `group`, `text` e
   `shape`): `std::optional<BridgeGlyphUse> glyphUse;`.

2. No `BridgeDeviceContext`:
   - trocar `m_glyphCache` (hoje `map<const Glyph *, vector<Bezier>>`, cache só
     de CPU) por `std::map<std::string, BridgeGlyphDef> m_glyphs`, indexado pelo
     `glyphId`, que é **a saída** do exportador e não só um cache.
   - `MakeGlyphShape` vira `MakeGlyphUse(const Glyph *, const FontInfo *, x, y)`:
     registra o glifo no dicionário se ainda não existir (parseando o XML com o
     `svgpathparser`, exatamente como hoje) e devolve um `BridgeGlyphUse` com
     `sx`/`sy` calculados **com a mesma fórmula de hoje**:

     ```
     sy = pointSize / unitsPerEm * DEFINITION_FACTOR
     sx = sy * (widthToHeightRatio != 1 ? widthToHeightRatio : 1)
     ```

   - `GetGlyphAdvance` **não muda** (a aritmética inteira é o que mantém o
     avanço idêntico ao do SVG — não "melhore" para ponto flutuante).
   - expor `const std::map<std::string, BridgeGlyphDef> &GetGlyphs() const`.

3. O `glyphId` é `"<faceName>:<codepoint hex maiúsculo>"`. Se duas fontes
   diferentes forem usadas na mesma partitura (fonte principal + fallback), elas
   **têm** que gerar entradas distintas — teste isso explicitamente (critério 4).

4. Ajustar os três pontos de chamada para empilhar um `BridgeChild` com
   `glyphUse` em vez de um `shape`.

## Fora de escopo

- Serializar (S05) — aqui a IR só passa a carregar o dicionário.
- Reuso de qualquer outra coisa que não glifo (formas geométricas repetidas não
  se repetem o suficiente para valer; não invente).
- Caminho de render por TTF no Flutter (o formato carrega os metadados, mas o
  render canônico é por contorno — ver `CLAUDE.md`).

## Critérios de aceite

1. Compila.
2. **A geometria não mudou.** Escreva um teste temporário que, para cada glifo
   usado numa página do corpus, expanda a instância (`contorno * s + (x,y)`) e
   compare com o que `MakeGlyphShape` produzia antes — diferença máxima
   admitida: `1e-9` por coordenada. Rode em pelo menos 2 peças e registre o
   valor máximo observado nas notas.
3. **Redução real de dados.** Para cada peça do corpus, registre nas notas:
   nº de usos de glifo, nº de glifos distintos e a razão entre os dois. Pelo
   histórico (5444 `<use>` no corpus inteiro), a razão deve ficar bem acima de
   10:1 na maioria das peças.
4. Duas famílias de fonte na mesma peça geram `glyphId` distintos: force com
   `--font Bravura` numa peça que tenha algum glifo fora da Bravura (ou um MEI
   com `@fontname`), e confirme duas chaves diferentes para o mesmo codepoint.
5. Nenhum `BridgeShape` remanescente é criado a partir de glifo:
   `grep -n "MakeGlyphShape" verovio/src` retorna vazio.

## Notas de execução

- 2026-09-17: adicionados `BridgeGlyphDef`, `BridgeGlyphUse` e o terceiro filho
  `glyphUse`; `m_glyphCache` virou o dicionário `m_glyphs`, `MakeGlyphShape` virou
  `MakeGlyphUse`, e as três chamadas de texto/música agora empilham usos de glifo.
- O `glyphId` usa a fonte que realmente forneceu o `Glyph` (`Resources::GetGlyphFontName`),
  preservando entradas distintas para o mesmo codepoint em fontes diferentes.
- Compilação: `cmake ../cmake && make -j4` concluída com sucesso.
- Verificação geométrica temporária em 10 peças do corpus: todos os usos foram expandidos com
  `x + sx * contorno`/`y + sy * contorno`; diferença máxima observada: `0.0` (limite `1e-9`).
- Contagem por peça (usos / distintos / razão): Chopin Etude `1792/34/52.71`, Chopin Mazurka
  `1434/30/47.80`, Grieg Butterfly `1594/24/66.42`, Grieg Little Bird `1109/23/48.22`,
  Scarlatti C-major `1064/25/42.56`, Nocturne `2665/37/72.03`, Clair de Lune `2458/31/79.29`,
  Gymnopédie `417/16/26.06`, Maple Leaf Rag `2045/21/97.38`, Prelude BWV 846 `835/16/52.19`.
- Teste de duas fontes: render com `Gootville` na Chopin Etude produziu chaves `Gootville:*` e
  `Leipzig:*` (`1791` usos, `32` defs, razão `55.97`); uma verificação direta do mesmo codepoint
  `E0A4` retornou `Leipzig` e `Gootville` como donos distintos.
- `rg -n "MakeGlyphShape" verovio/src` sem resultados; `git diff --check` limpo.
- SVG de fumaça gerado para as 10 peças; `RenderToDeviceContext` percorreu todas sem crash/assert.
- `clang-format` não estava instalado no ambiente; o build e `git diff --check` passaram.
- Bloqueios: nenhum.
