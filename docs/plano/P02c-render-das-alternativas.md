# P02c — C++: renderizar as sequências alternativas e gravar `alternates.json`

**Depende de:** P02b · **Decisão necessária:** não

## Objetivo

Para cada ponto de chegada de P02b, gerar a sequência alternativa com o
`Select()` do Verovio (D-ALT-MECANISMO) e gravá-la em `alternates.json`
(spec §2.5). As páginas normais, o timemap e o `meta.json` não podem mudar
nem um byte.

## Ler antes (só isto)

- `docs/plano/P00-visao-geral-paginas-alternativas.md`, seções "O que já foi
  provado" e "Exportador (C++)".
- `verovio/src/toolkit.cpp`: `RenderPagesToBridge`, `RenderToBridgeJson`,
  `RenderToBridgeFile`, `Toolkit::Select` (L165) e `Toolkit::RedoLayout`
  (perto de L1640).
- `verovio/src/doc.cpp`: `InitSelectionDoc`, `ResetSelectionDoc`,
  `ReactivateSelection` (L1241-L1370).
- `verovio/src/bridgewriter.cpp`: `WriteScene`, `WriteManifest`,
  `WriteSingleJson`.
- `docs/formato/especificacao-v1.md` §2.5.

## Contexto que você precisa (não vá procurar, está aqui)

- `Select(json)` só marca a seleção como pendente. Ela é aplicada no próximo
  `RedoLayout()`. `Select("{}")` + `RedoLayout()` pede o reset
  (`docselection.cpp`: sem `start`/`end`/`measureRange` = reset). **Confira**
  que depois do reset `GetPageCount()` e o SVG da página 1 voltam
  byte-idênticos: é o critério 3.
- O `BridgeDeviceContext` acumula as páginas em `GetPages()` e o dicionário
  de glifos em `GetGlyphs()`, e o dicionário nunca é zerado entre páginas
  (achado de S06). Renderize as alternativas **no mesmo** DC, **depois** das
  normais, e separe as páginas pelo índice (`pages[0..N)` = normais, o resto
  = alternativas, por sequência). Um glifo que só aparece numa alternativa
  (clave de cortesia, por exemplo) entra no `glyphs.json` compartilhado.
- O timemap (`RenderToTimemap`) usa o `m_midiDoc` expandido, que é
  independente da paginação. Gere-o **antes** das seleções, como hoje.
- O `meta.json` lê `firstPage->GetHeader()`. Leia-o **antes** das seleções,
  para que ele saia do documento normal.
- Custo: cada sequência = um relayout do trecho + o reset (relayout do
  documento inteiro). D-RUNTIME (o `.vsb` é gerado no aparelho) torna esse
  custo relevante. **Meça.**
- `RenderToBridgeJson(from, to)` (o `-t vsb-json` com `-p`) exporta um
  intervalo de páginas. Alternativas só entram quando o intervalo é o
  documento inteiro (`-a`). Registre essa regra na spec, se precisar.

## O que fazer

1. Opção nova `--no-vsb-alternates` (bool, `options.h`/`options.cpp`, grupo
   geral, igual a `noInstrumentLabels` do commit `4663537`) que desliga a
   geração. Serve para os critérios e para depuração. O padrão é gerar.
2. Em `RenderToBridgeFile` (e em `RenderToBridgeJson` quando for o documento
   inteiro), depois das páginas normais, do timemap e do meta:
   1. `starts = pontos de chegada` (P02b);
   2. para cada `T`: `Select({"start": T, "end": <id do último compasso do
      documento>})`, `RedoLayout()`, renderize **todas** as páginas da
      seleção no mesmo `BridgeDeviceContext` e anote o intervalo de páginas
      da sequência `T`;
   3. `Select("{}")` + `RedoLayout()` para devolver o `Doc` ao estado
      normal (o `Toolkit` do FFI pode ser reaproveitado pelo host).
3. `BridgeWriter::WriteAlternates(...)` → `alternates.json` (§2.5), com as
   páginas serializadas exatamente como `WriteScene` faz (reuse o código;
   não duplique a serialização de página). `index` 0-based dentro da
   sequência.
4. Manifest com `files.alternates` quando houver sequências. JSON único com a
   propriedade `alternates`. Omitido quando não houver sequência.
5. Se a sequência de `T` sair com a página 0 **não** começando em `T` (a
   seleção falhou, `LogWarning("Selection could not be made")`), **não**
   grave a sequência e registre um aviso no log. Não aborte o arquivo.

## Fora de escopo

- Referência SVG e paridade das alternativas (P02d).
- Qualquer coisa no Dart.

## Critérios de aceite

1. Para cada peça com repetição: o número de sequências é igual ao de pontos
   de chegada de P02b, e a página 0 de cada sequência tem `start` como
   **primeiro** nó de classe `measure` (verificado por script sobre o
   `alternates.json`).
2. Todo `xml:id` de nota/acorde/pausa/compasso numa página alternativa existe
   nas páginas normais. Dentro de uma sequência, nenhum id se repete.
3. `scene.json`, `timemap.json`, `meta.json` e `manifest` (menos
   `files.alternates`) **byte-idênticos** com e sem `--no-vsb-alternates`
   nas 10 peças. `glyphs.json` com alternativas é um **superconjunto** do sem
   alternativas.
4. Depois do `RenderToBridgeFile`, o mesmo `Toolkit` renderizando `-t svg` da
   página 1 dá SVG byte-idêntico a um `Toolkit` novo: o estado foi
   restaurado (teste com um programa avulso contra a `libverovio.so`, como o
   da sessão de 2026-09-22, ou pelo binding Dart).
5. Tabela nas notas, por peça: páginas normais, sequências, páginas
   alternativas, tamanho do `.vsb` com e sem alternativas, e tempo de
   `RenderToBridgeFile` com e sem (média de 5 execuções, `--release`).
6. Peças sem repetição: nenhum `alternates.json`, `.vsb` byte-idêntico ao de
   P01c.
7. Build sem avisos novos.

## Notas de execução

**Mecanismo.** `Toolkit::RenderAlternatesToBridge(BridgeDeviceContext &bridge)`
(novo, `toolkit.cpp`/`.h`), chamado por `RenderToBridgeFile` (sempre) e por
`RenderToBridgeJson` (só quando o intervalo pedido é o documento inteiro —
`fromPage <= 1 && (toPage < 0 || toPage >= páginas normais)`; um intervalo
parcial não tem "resto da peça" para uma sequência ir até o fim, e
`ComputeAlternateStarts` deriva `firstOfNormalPage` do `Doc` inteiro,
independente do intervalo pedido). Para cada ponto de chegada de P02b:
`Select({"start": T, "end": <último compasso do documento>})` +
`RedoLayout()`, renderiza todas as páginas da seleção no mesmo
`BridgeDeviceContext` das páginas normais, confere que a página 0 realmente
começa com `T` (1º nó de classe `measure` em pré-ordem — `FindFirstMeasureNode`,
namespace anônimo em `toolkit.cpp`) e que `m_doc.HasSelection()` ficou
verdadeiro (é como `InitSelectionDoc` sinaliza "Selection could not be made"
sem lançar exceção: limpa `m_selectionStart`/`End` e retorna sem reativar).
Qualquer uma das duas falhas pula a sequência com `LogWarning`, sem abortar
o arquivo (item 5). No fim, sempre `Select("") + RedoLayout()` — usei string
vazia, não `"{}"`: o comentário de `docselection.cpp` ("Empty string - we
reset the selection") é o caminho que realmente reresulta em
`DocSelection::Parse` devolvendo sucesso; `"{}"` (objeto JSON vazio) cai no
`else if` de "Cannot extract a selection" e devolve falso (ainda reseta
`m_selectionStart`/`End`, mas loga um aviso espúrio) — P00 citava `"{}"`
informalmente, a nota lá deveria dizer string vazia.

**Achado importante (evitado, não só documentado): pointer invalidation.**
`BridgeDeviceContext::m_pages` é um `std::vector<BridgePage>`; qualquer
`push_back` (cada `Select`+render de uma sequência) pode realocar e invalida
todo `const BridgePage*` tirado antes. A primeira versão do código construía
o vetor de ponteiros das páginas normais logo após renderizá-las — antes de
chamar `RenderAlternatesToBridge` — o que corromperia silenciosamente
`scene.json` (ponteiros pendurados) assim que a 1ª sequência fosse
renderizada. Corrigido: `RenderAlternatesToBridge` só constrói seus próprios
`BridgeAlternateSequence::pages` **depois** de terminar todo o `Select`/
render (por índice, não por ponteiro, enquanto o vetor ainda pode crescer);
o chamador (`RenderToBridgeFile`/`RenderToBridgeJson`) só constrói o vetor
das páginas normais **depois** de `RenderAlternatesToBridge` retornar. Doc
comment de ambos os métodos deixa esse contrato explícito para não
reintroduzir o bug num passo futuro.

**Escrita.** `BridgeWriter::WriteAlternates` (novo) serializa
`{"sequences":[{"start", "pages":[...]}]}`, reusando `AppendPage` (mesmo
código de `WriteScene`, `index` 0-based dentro de cada sequência).
`WriteManifest`/`WriteSingleJson` ganham `hasAlternates`/`sequences`
(parâmetros com default, aditivo — nenhuma outra chamada existente
quebrou). `BridgeAlternateSequence` (struct novo, `bridgewriter.h`).

**Opção `--no-vsb-alternates`** (`m_noVsbAlternates`, grupo geral, análoga a
`--no-instrument-labels` de `4663537`): desliga a geração. Padrão é gerar.

**Critério 1** (nº de sequências == pontos de chegada de P02b; página 0
começa com `start`). Medido nas 6 peças com repetição — bate exatamente com
a tabela de P02b (Gymnopédie 1, Maple Leaf Rag 8, Mazurka 1, Little bird 1,
Butterfly 0, Scarlatti 0) e todo `start` confere com o 1º `measure` da
página 0 de sua sequência, checado por script Python sobre o `.vsb` real
(não uma reimplementação da regra — leitura direta do `scene`/`alternates`
serializados).

**Critério 2** (todo `xml:id` de nota/acorde/pausa/compasso numa página
alternativa existe nas páginas normais; nenhum se repete dentro de uma
sequência). Confirmado nas 4 peças com sequência de verdade (o script
inicial testou **todo** `id` da árvore, não só nota/acorde/pausa/compasso, e
"falhou" nos ids de `system`/`grpSym`/`label`/`clef`/`keySig`/`meterSig`
sintetizados pela seleção — exatamente o que o critério já esperava que
fossem novos, "Contexto" do passo e P00: "Os ids de system (e do
score/scoreDef sintetizados) são novos". Refiz filtrando por classe
`{note, chord, rest, measure}`: 0 ids faltando, 0 repetidos, em 11
sequências de 4 peças (2 284 a 24 ids por sequência).

**Critério 3** (`scene.json`/`timemap.json`/`meta.json`/manifest-menos-
`files.alternates` byte-idênticos com/sem `--no-vsb-alternates`; `glyphs.json`
com alternativas é superconjunto). Confirmado nas 10 peças do corpus
(script Python comparando os dois `.vsb`, ignorando só o sufixo `-dirty` do
`generator`). Isso só é garantido porque as páginas normais, o timemap e o
`meta.json` são lidos **antes** de `RenderAlternatesToBridge` rodar (doc
comment do método deixa isso como pré-condição).

**Critério 4 (medido, com uma ressalva registrada).** Programa Dart avulso
contra o binding FFI (`libverovio.so` reconstruído): um `Toolkit` que chama
`renderToBridgeFile` (com alternativas) e depois `renderToSVG(1)` **não** dá
SVG byte-idêntico a um `Toolkit` novo — mas só nos ids **auto-gerados** de
elementos sem `xml:id` codificado (`system`, `grpSym`, `label`/`tspan`,
`clef`, `keySig`, `keyAccid`, `meterSig`: todo elemento que o cast-off
sempre recria do zero). **Nenhuma nota/acorde/pausa/compasso muda** (291
`class="note"` idênticas, checado por diff). Com `--no-vsb-alternates` (ou
`{"noVsbAlternates": true}`), o mesmo teste dá SVG **exatamente** igual —
isolando a causa: `Object::s_xmlIDCounter` (`object.cpp`) é um contador
**global do processo**, não por `Doc`; cada `Select`/`RedoLayout` de uma
sequência cria um `Score`/`ScoreDef`/`System` novo (`Doc::ReactivateSelection`)
que consome ids desse contador, e o `Select("")` final refaz o cast-off do
documento normal a partir de um contador que avançou mais do que um
`Toolkit` novo veria — gerando uma sequência diferente (mas igualmente
válida) de auto-ids para os elementos sem id codificado. Isso é um efeito
de qualquer uso de `Select`/`RedoLayout` no Verovio, não específico deste
passo, e não corrigi (mexeria no contador estático de `Object`, fora do
escopo de "só mais um `DeviceContext`" que rege este fork) — registrado
aqui como achado, com o contorno já disponível: `ResetXmlIdSeed(seed)`
antes de qualquer render subsequente no mesmo `Toolkit` que precise bater
bytes com um `Toolkit` novo. O `.vsb` em si (critério 3) não é afetado,
porque as páginas normais são lidas antes de qualquer `Select`.

**Critério 5** — tabela (10 execuções por peça, 5 com e 5 sem
`--no-vsb-alternates`, `--xml-id-seed 42`, binário já em `-O3 -DNDEBUG`
— não há build separado de release neste fork):

| Peça | Páginas normais | Sequências | Páginas alternativas | `.vsb` com (bytes) | `.vsb` sem (bytes) | Tempo com (s) | Tempo sem (s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Gymnopédie | 2 | 1 | 1 | 56 911 | 49 371 | 0,166 | 0,121 |
| Maple Leaf Rag | 3 | 8 | 13 | 813 804 | 188 458 | 1,908 | 0,524 |
| Mazurka | 3 | 1 | 2 | 217 477 | 131 037 | 0,561 | 0,332 |
| Butterfly | 3 | 0 | 0 | 127 059 | 127 059 | 0,290 | 0,277 |
| Little bird | 2 | 1 | 2 | 142 427 | 85 830 | 0,351 | 0,206 |
| Scarlatti | 3 | 0 | 0 | 100 847 | 100 847 | 0,230 | 0,225 |

Custo cresce com o nº de sequências (cada uma é um relayout do trecho +
um relayout do documento inteiro no reset final, que roda de novo a cada
`T` já que `InitSelectionDoc` reseta antes de aplicar a próxima seleção).
Maple Leaf Rag (8 sequências) é o pior caso do corpus: 3,6× o tempo e 4,3×
o tamanho. D-RUNTIME (gerar no aparelho) torna esse custo real; relevante
para o `zywny` decidir se gera na entrada do usuário na peça ou em
background.

**Critério 6** (peças sem repetição: sem `alternates.json`, `.vsb`
byte-idêntico a P01c). Confirmado nas 4 peças sem repetição do corpus
(Étude, Nocturne, Clair de Lune, Prelude): nenhuma tem `alternates.json`
mesmo com o padrão (gerar) ligado, porque `ComputeAlternateStarts` já
devolve lista vazia para elas (P02b).

**Critério 7**: build sem avisos novos, conferido nas duas recompilações
completas que este passo disparou (mudar `options.h`/`toolkit.h`, este
incluído por quase todo o projeto).
