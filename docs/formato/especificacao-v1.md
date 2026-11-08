# Formato `.vsb` (Verovio Score Bridge) — especificação v1

**Status:** normativo, fechado em S01. Os passos S02-S07 (C++) e R01-R06
(Dart) devem implementar exatamente este contrato. Uma divergência encontrada
durante a implementação é resolvida editando este documento primeiro e
registrando a mudança em [Histórico de revisões](#histórico-de-revisões).

## 1. Princípios

1. O formato descreve **uma cena estática por página**, mais a identidade
   (`xml:id` e classe) de cada elemento desenhado. Não descreve animação:
   animação é responsabilidade do renderizador Flutter.
2. O formato é uma transcrição fiel do que o `View` do Verovio manda para o
   `DeviceContext` — o mesmo fluxo que gera o SVG. Nada é reinterpretado.
3. Estilo (bold/italic por classe CSS, `stroke:currentColor`) é **resolvido na
   exportação**. O leitor não interpreta CSS.
4. Cor é **herdada**, como no SVG: um nó pode declarar `color`; formas sem
   `fill`/`stroke` explícitos usam a cor herdada do ancestral mais próximo.
   Trocar a cor de uma nota em runtime = trocar uma cor só, no nó da nota.
5. Geometria repetida (glifos) aparece **uma vez** num dicionário; cada uso é
   uma referência com posição e escala.
6. As coordenadas são unidades de viewBox do Verovio (`DEFINITION_FACTOR = 10`
   por px lógico), com o eixo Y apontando para baixo.

## 2. Empacotamento e documentos JSON

O nome do formato é **Verovio Score Bridge**, a extensão é **`.vsb`**, e as
flags de saída são:

- `-t vsb`: pacote zip com extensão `.vsb`;
- `-t vsb-json`: um único JSON com extensão `.json`, destinado à depuração e a
  diffs.

| Formato de saída | Arquivo | Conteúdo |
| --- | --- | --- |
| `-t vsb` | `<nome>.vsb` (zip) | `manifest.json`, `scene.json`, `glyphs.json` e, quando disponíveis, `timemap.json`, `meta.json`, `alternates.json`, `midi.json`, `pitchpos.json` e `music.json` |
| `-t vsb-json` | `<nome>.json` | um objeto JSON com `manifest`, `glyphs`, `scene` e, quando disponíveis, `timemap`, `meta`, `alternates`, `midi`, `pitchpos` e `music` |

O `timemap.json` é **embutido no pacote** quando o Verovio produz um timemap
não vazio. Se a peça não produzir timemap, o arquivo e a entrada correspondente
no manifest são omitidos; nunca é gravado um timemap vazio. No JSON único, o
mesmo array é colocado na propriedade `timemap`.

O `meta.json` (§2.3) leva o título e os autores da peça e segue a mesma regra
de omissão: se o arquivo de origem não informa nenhum dos dois, o arquivo e a
entrada do manifest não existem.

O `alternates.json` (§2.5) leva as páginas alternativas do player, usadas só
em saltos de repetição (P00-P05). Segue a mesma regra de omissão: uma peça
sem nenhum salto que precise de página alternativa não tem o arquivo nem a
entrada do manifest.

O `midi.json` (§2.7) leva os eventos que o exportador MIDI do Verovio emitiria
para um `.mid` — notas (com ligadura e ornamentos já resolvidos) e pedal —
com o `xml:id` de origem e o tempo em milissegundos. Segue a mesma regra de
omissão: uma peça sem nenhuma nota tocável não tem o arquivo nem a entrada do
manifest.

O `pitchpos.json` (§2.8) leva o contexto de notação de cada nota e pausa
(clave, 8va/transposição, armadura, acidentes em vigor), que o host usa para
calcular onde uma nota **tocada** ficaria escrita na pauta (a nota fantasma,
§10). Segue a mesma regra de omissão: uma peça sem nenhuma nota nem pausa não
tem o arquivo nem a entrada do manifest.

O `music.json` (§2.9) leva a estrutura musical da partitura **notada** —
partes, compassos com fórmula, armadura e modo, casas, pautas, camadas e
eventos, cifras, direções e andamentos —, sem geometria, para o host ler a
música sem ler o MusicXML nem o MEI (M00). Segue a mesma regra de omissão: uma
peça sem nenhum compasso não tem o arquivo nem a entrada do manifest.

### 2.1 `manifest.json`

```json
{
  "format": "vsb",
  "version": 1,
  "generator": "verovio 6.3.0 / bridge 1",
  "pageCount": 4,
  "files": {
    "scene": "scene.json",
    "glyphs": "glyphs.json",
    "timemap": "timemap.json",
    "meta": "meta.json",
    "midi": "midi.json",
    "pitchpos": "pitchpos.json",
    "music": "music.json"
  }
}
```

- `format` é sempre `"vsb"`.
- `version` é o inteiro `1`.
- `generator` identifica a versão do Verovio e do bridge que produziu o
  documento.
- `pageCount` é o número de páginas em `scene.pages` (as páginas **normais**;
  não conta nenhuma página de `alternates.json`).
- `files.scene` e `files.glyphs` são obrigatórios. `files.timemap`,
  `files.meta`, `files.alternates`, `files.midi`, `files.pitchpos` e
  `files.music` existem somente quando o pacote contém `timemap.json`,
  `meta.json`, `alternates.json`, `midi.json`, `pitchpos.json` e `music.json`,
  respectivamente (§2.4, §2.3, §2.5, §2.7, §2.8, §2.9).
- No JSON único, `manifest.files` mantém os nomes lógicos acima mesmo sem
  arquivos físicos separados.

### 2.2 JSON único

A raiz de `-t vsb-json` é:

```json
{
  "manifest": { "...": "manifest.json" },
  "glyphs": { "...": "dicionário de glifos" },
  "scene": { "pages": [] },
  "timemap": [],
  "meta": { "title": "..." },
  "alternates": { "sequences": [] },
  "midi": { "notes": [], "pedal": [] },
  "pitchpos": { "events": {} },
  "music": { "version": 1, "parts": [], "measures": [], "ornaments": [],
             "harmonies": [], "directions": [], "tempi": [] }
}
```

`timemap`, `meta`, `alternates`, `midi`, `pitchpos` e `music` são opcionais e
seguem exatamente o conteúdo de `timemap.json`, `meta.json`, `alternates.json`,
`midi.json`, `pitchpos.json` e `music.json`. O parser deve aceitar tanto a raiz
única quanto os documentos individuais `scene.json`, `glyphs.json`,
`manifest.json`, `timemap.json`, `meta.json`, `alternates.json`, `midi.json`,
`pitchpos.json` e `music.json`.

### 2.3 `meta.json`

Título e autores da peça — do documento inteiro, nunca por página — num
arquivo pequeno e à parte do `scene.json`, para o host listar uma biblioteca
sem ler nenhuma página.

```json
{
  "title": "Etude in F Minor",
  "creators": [
    { "name": "Frédéric Chopin", "role": "composer" }
  ]
}
```

- `title` (string, opcional): título da peça, **como aparece no cabeçalho
  renderizado** da primeira página (regras abaixo).
- `creators` (array, opcional): pessoas creditadas na ordem do arquivo de
  origem, sem pares `(name, role)` repetidos. `name` é obrigatório; `role`
  (`composer`, `lyricist`, `arranger`, `translator`, `harmonizer`, `author`,
  `poet`) é omitido quando o arquivo não o informa.
- Todo campo vazio é omitido, e o documento inteiro é omitido quando não sobra
  nenhum (um `{}` nunca é gravado). Chaves desconhecidas devem ser ignoradas
  pelo leitor.
- Os textos têm o espaço em branco normalizado (sequências viram um espaço,
  sem espaços nas pontas).

#### Título: o que o cabeçalho mostraria com `--header auto`

`title` **não depende de `--header`** (P01a, D-META-TITULO opção (a)): é
calculado como se `--header` fosse `auto`, sem desenhar nada. Isso evita que o
host perca o título quando o `.vsb` é gerado com `--header none` (o padrão,
D-VSB-PADRAO).

A regra, em `Toolkit::ReadBridgeMeta`: se a página 1 tem cabeçalho desenhado
(`Page::GetHeader()`, que só acontece com `--header auto` ou `encoded`),
`title` vem dele, como antes. Senão (`--header none`, ou `encoded` numa peça
sem cabeçalho codificado):

1. se o `scoreDef` da primeira `Score` visível já traz um `<pgHead
   func="first">` codificado, usa-o;
2. senão, monta um `PgHead` descartável do mesmo jeito que
   `Doc::GenerateHeader()` faria (`GenerateFromMEIHeader`, sem anexá-lo ao
   documento nem depender de layout) e usa esse.

Dentro do cabeçalho (real ou descartável), o título é o texto do primeiro item
de topo que não está encostado num lado nem é uma pessoa creditada:

- no cabeçalho gerado, o bloco rotulado `title`; a primeira linha é o título
  principal e as demais (subtítulos, outras línguas) ficam de fora;
- no cabeçalho codificado, que não traz rótulo, o primeiro texto centralizado ou
  sem alinhamento — por convenção o compositor fica à direita e o letrista ou o
  número de catálogo (`BWV 846`) à esquerda.

Como vem do desenho (ou do que o desenho mostraria), uma peça MusicXML que
guarda o título só em `<credit-words>` (comum em arquivos do MuseScore e do
Finale) também tem `title`. Medido nas 10 peças do corpus, `title` é **igual**
com `--header none`, `auto` e `encoded` (30/30): as 5 peças MusicXML já batem
o `<credit>` como `<pgHead>` codificado na importação, então `encoded` sempre
tinha `title`; as 5 peças MEI não trazem `<pgHead>` codificado, então
`encoded` caía na mesma regra de "sem cabeçalho desenhado" que `none` — e por
isso ganha o `title` gerado, igual ao de `auto`, desde este passo (antes dele,
`encoded` saía sem `title` nessas 5).

#### Autores: sempre do cabeçalho MEI

`creators` **não** depende de `--header`. Vem do `<meiHead>` que o Verovio
mantém para qualquer entrada — o próprio cabeçalho MEI, ou o que o importador
MusicXML monta a partir de `identification/creator`: os elementos `composer`,
`lyricist`, `arranger` e `author` de `titleStmt` (o papel é o nome do elemento)
e os `respStmt/persName` cujo `@role` é um dos papéis acima. Um `encoder`,
`editor` ou `dedicatee` **não** é autor da peça e não entra.

Limites conhecidos: o nome vem como está no arquivo, e pode diferir do que o
cabeçalho desenha — no Clair de Lune, `creator` é `Claude Debussy(1862 – 1918)`
e o SVG mostra `Claude Debussy`. Uma peça MusicXML que credita o compositor só
em `<credit-words>` (4 das 5 do corpus) não tem `creator` e sai sem `creators`,
mesmo com `title`.

### 2.4 `timemap.json`

O conteúdo é o timemap do próprio `Toolkit` do Verovio (um array de
instantes, cada um com `tstamp`/`qstamp`, `on`/`off` de notas, `restsOn`/
`restsOff`, `tempo` quando muda naquele instante), sem reinterpretação — o
formato só decide **quando** embutir (regra acima) e com quais opções chamar
o exportador de timemap.

Desde 2026-09-21, o timemap é sempre pedido com `includeMeasures: true`
(`Toolkit::RenderToBridgeFile`), o que preenche `measureOn` com o `xml:id` do
compasso que começa naquele instante — presente mesmo quando nenhuma nota
começa exatamente ali (só ligaduras, ou só pausas). `useFractions`
continua desligado (mudaria outras colunas que o `score_bridge` já lê).

Desde G04c (2026-09-29, D-FANT-PAUSA-TEMPO) o timemap também é pedido com
`includeRests: true`: cada instante ganha, quando há pausas começando/
terminando nele, as chaves `restsOn`/`restsOff` (arrays de `xml:id` de
`rest`/`mRest`/`multiRest`, com a mesma regra de ids expandidos `-rend<N>` de `on`/`off`).
O host precisa delas para saber **quando** uma pausa está ativa (a nota
fantasma de uma tecla tocada durante uma pausa, §10). Só essas duas chaves
são novas: os instantes só com pausa já existiam (vazios), e `on`/`off`/
`tstamp`/`qstamp`/`measureOn`/`tempo` continuam iguais.

**Ids expandidos (`-rend<N>`).** Uma peça com repetição tem, no timemap, ids
que não existem em `scene.json`: a árvore desenhada é sempre a do documento
**notado** (sem repetição), enquanto o timemap vem de uma cópia expandida
internamente pelo Verovio para o cálculo de tempo (`Toolkit::SetMidiDoc`).
Cada trecho repetido vira um clone com o id `<id notado>-rend<N>` (`N` = a
N-ésima execução daquele elemento; `N` começa em 2, já que a 1ª execução usa
o id notado sem sufixo). Isso vale tanto para `measureOn` quanto para os ids
de `on`/`off`.

O leitor resolve um id do timemap ao nó da cena por uma **regra de sufixo**,
sem precisar de um arquivo extra:

1. Se o id existe em `scene.json`, ele é o próprio nó — na 1ª execução.
   (Isso vale mesmo que o id termine em `-rend<N>`: um host que desenhe a
   partitura já expandida, por exemplo com `--expand-always`, tem esses
   clones como nós próprios da cena, e a regra do sufixo nunca se aplica a
   um id que já existe.)
2. Senão, se o id casa com `^(.*)-rend([0-9]+)$` e a base (grupo 1) existe em
   `scene.json`, o id representa a base, na execução número do grupo 2.
3. Senão, o id não pertence à cena (ex.: um `xml:id` interno do documento
   expandido que não corresponde a nada desenhado).

Verificado sobre o corpus e sobre um conjunto de partituras de teste com
todo tipo de repetição (D.C./D.S./coda, casas, `times`, repetição aninhada
num compasso só): a regra concorda com o `-t expansionmap` do Verovio em
100% dos ids de timemap (2 933 ids checados inicialmente, `docs/plano/
E01a-corpus-de-repeticoes.md`/`E01b-timemap-com-compassos.md`), então o
formato não ganha um `expansion.json` à parte — o mapa completo do Verovio
lista todo elemento clonado (pauta, camada, haste…), não só os ids do
timemap, e pesa 50-207 KB por peça no corpus.

### 2.5 `alternates.json`

Páginas **alternativas**, usadas só pelo player quando um salto de repetição
muda de página (`docs/plano/P00-visao-geral-paginas-alternativas.md`): em vez
de voltar para a página normal de destino (onde o compasso de chegada pode
estar no meio), o player mostra uma página redesenhada que começa exatamente
nele.

```json
{
  "sequences": [
    {
      "start": "d1e3853",
      "pages": [ { "index": 0, "...": "igual a scene.pages[i] (§5)" } ]
    }
  ]
}
```

- `start`: `xml:id` **notado** (sem sufixo `-rendN`; §2.4) do compasso de
  chegada, que é o primeiro compasso da página `0` da sequência.
- `pages`: a paginação do trecho `start` → fim da peça (D-ALT-EXTENSAO: uma
  sequência nunca é cortada antes do fim, mesmo que páginas do meio nunca
  sejam exibidas por nenhum salto real). Cada página tem exatamente a forma
  de `scene.pages[i]` (§5): mesmos campos, mesma árvore, mesmos glifos do
  **mesmo** `glyphs.json` (nenhum dicionário próprio). `index` é 0-based
  **dentro da sequência**, não um índice global.
- Os `xml:id` de notas, acordes, compassos etc. dentro de uma sequência são
  os mesmos das páginas normais (o mesmo documento, apenas reselecionado e
  paginado de novo). Os ids de `system` e do `score`/`scoreDef` sintetizados
  pela seleção (`Doc::ReactivateSelection`) são **novos**: não correspondem a
  nada nas páginas normais nem em outra sequência.
- Dentro de **uma** sequência, cada id aparece uma vez (é uma paginação
  completa e independente do trecho). **Entre** sequências, e entre uma
  sequência e as páginas normais, os ids de nota/compasso se repetem **por
  construção** — não é uma inconsistência a resolver, é o motivo de existir
  uma sequência por ponto de chegada.
- `sequences` está em ordem de documento do `start` de cada uma, sem `start`
  repetido.
- **Regra de existência (normativa):** só existe sequência para um compasso
  que é destino de algum salto na execução (a ordem de `measureOn` do
  timemap, §2.4) **e** que não é já o primeiro compasso de alguma página
  normal — ali a página normal já serve, sem precisar de alternativa. Uma
  peça sem nenhuma sequência **omite o arquivo inteiro** e a entrada do
  manifest (mesma regra de omissão do timemap e do `meta.json`, §2.1).
- O arquivo **não** diz qual página exibir em qual momento: isso é decidido
  pelo leitor (regra em P00), a partir de `alternates` e da ordem de execução
  do timemap. `alternates.json` só oferece as páginas.

### 2.6 Modo debug (`--vsb-debug`)

Opcional, ligado por `--vsb-debug` (`OptionBool Options::m_vsbDebug`, desligado
por padrão). Embute no pacote os dois insumos que faltam para reproduzir a
renderização a partir **só** do `.vsb`, sem o arquivo de origem nem as flags
do Verovio usadas para gerá-lo — o caso de uso é rodar a comparação
Flutter×SVG (`compare/scripts/compare-page.sh`) tendo só o pacote em mãos.

| Formato de saída | Arquivo/propriedade | Conteúdo |
| --- | --- | --- |
| `-t vsb` | `debug-options.json` | saída de `Toolkit::GetOptions()`: todo valor de opção corrente, não só os explicitamente setados |
| `-t vsb` | `debug-source.txt` | o documento exatamente como chegou a `Toolkit::LoadData` (texto puro — um `.mxl` de entrada já sai descomprimido, um MEI/MusicXML UTF-16 já sai convertido para UTF-8; a farejada de formato do Verovio, `Toolkit::IdentifyInputFrom`, lê o conteúdo, não a extensão, então isso já basta para recarregar) |
| `-t vsb-json` | propriedade `debug` | `{"options": {...}, "source": "..."}`, mesmo conteúdo dos dois arquivos acima |

Segue a mesma regra de omissão do timemap/`meta.json`/`alternates.json`: sem
`--vsb-debug`, nem o arquivo/propriedade nem a entrada do manifest
(`files.debugOptions`/`files.debugSource`) existem.

**Reproduzindo um render a partir do `.vsb`:** `verovio` ganhou uma flag de
CLI companheira, `--options-file <caminho>` (`tools/main.cpp`), que lê um
JSON no formato de `Toolkit::GetOptions()`/`debug-options.json` e aplica via
`Toolkit::SetOptions` — depois de `--resource-path` ser resolvido (`SetOptions`
recarrega fonte quando o JSON tem `font`/`fontFallback`/etc., e fazer isso
antes do recurso path estar pronto falha) e **depois de todo o resto da linha
de comando**, então `--options-file` vence qualquer outra flag de opção da
mesma chamada, não importa a ordem em que aparecem — o uso pretendido é
`--options-file <caminho> <fonte>` sozinho, sem outras flags de opção
misturadas (`-t`/`-f`/`-p` não são afetadas: `GetOptions()` nunca emite
`inputFrom`/`outputTo`/`page`). Para gerar a referência SVG de uma sequência
alternativa (`--alternate` do `compare-page.sh`) é preciso `selectFrom` no
próprio JSON (não como flag separada) — o script monta essa cópia.

Limite conhecido: `xmlIdSeed` só é reproduzido quando a geração original já
usou `-x`/`--xml-id-seed` explícito. Sem isso, `Object::SeedID` sorteia a
semente internamente (`std::random_device`) e nunca a escreve de volta em
`m_options`, então `debug-options.json` grava o sentinel de "não setado" — os
`xml:id` sintéticos (elementos sem id na fonte) saem diferentes a cada
render, original ou reproduzido. Nunca afeta o critério de correção (§
"Critério de correção é visual" no `CLAUDE.md`), que compara pixels, não ids;
só importa se algo além do diff de pixel depender desses ids.

### 2.7 `midi.json`

O timemap (§2.4) diz **quando** cada id liga/desliga (para o destaque
visual), mas não **o que soa**: cada nota entra separada da sua ligadura, e
ornamentos entram como a nota escrita, não como as notas que o MIDI toca.
`midi.json` (G01, `docs/plano/G01-gravador-de-notas-midi.md`) é o fluxo de
eventos que `GenerateMIDIFunctor` — o mesmo código que gera um `.mid` — emitiria
para a peça, com o `xml:id` de origem de cada evento e o tempo já convertido
de semínimas para milissegundos.

```json
{
  "notes": [
    { "id": "n1a2b", "on": 0, "off": 500, "p": 64, "s": 1, "l": 1, "v": 90 },
    { "id": "n77-rend2", "on": 12000, "off": 14000, "p": 52, "s": 2, "l": 1, "v": 90,
      "tied": ["n9f-rend2"] },
    { "id": "n33", "on": 3000, "off": 3062.5, "p": 71, "s": 1, "l": 1, "v": 90, "orn": true },
    { "id": "n33", "on": 3062.5, "off": 3125, "p": 72, "s": 1, "l": 1, "v": 90, "orn": true }
  ],
  "pedal": [
    { "id": "pd12", "t": 1000, "dir": "down", "s": 1 },
    { "id": "pd13", "t": 4000, "dir": "up", "s": 1 }
  ]
}
```

**`notes[]`**, uma entrada por nota efetivamente tocada, ordenada por `on`
(critério de desempate: `s`, `l`, `p`):

- `id` (obrigatório): `xml:id` da nota — o mesmo id do timemap (expandido,
  `-rend<N>`, §2.4). Numa ligadura, é o id da **primeira** nota da cadeia; num
  ornamento (trinado/tremolo) expandido pelo MIDI em várias notas curtas, o
  mesmo id se repete numa entrada por sub-nota (`orn: true` em todas).
- `on`/`off` (obrigatórios, ms): mesmo relógio e mesma precisão do `tstamp` do
  timemap (§2.4) — não o tick do `.mid` (que arredonda para a resolução do
  arquivo); calculado por integração ao longo do andamento vigente, sem a
  quantização em ticks que o `.mid` tem. Numa nota ligada, `off` já é o fim da
  cadeia inteira (a soma de todas as continuações, como
  `note->GetScoreTimeTiedDuration()` já calcula) — o leitor não soma nada.
- `p` (obrigatório): altura MIDI 0-127, já com transposição de instrumento e
  8va/8vb (`Note::GetMIDIPitch(transSemi, octaveShift)` — nunca a variante sem
  argumentos, que ignora os dois).
- `s`/`l` (obrigatórios): número (`@n`) da pauta e da camada de origem (piano:
  1 = mão direita, 2 = mão esquerda, por convenção do corpus).
- `c` (opcional, padrão `0`): canal MIDI 0-15; omitido quando `0`.
- `pg` (opcional, padrão `0`): programa MIDI (General MIDI) do instrumento;
  omitido quando `0`.
- `v` (obrigatório): velocity 1-127 (`@vel` explícito, senão o padrão do
  Verovio). Uma nota silenciosa (`@vel="0"`) não gera evento — não é tocável
  nem pelo MIDI.
- `tied` (opcional, padrão `[]`): ids das notas de continuação da ligadura,
  na ordem em que aparecem — cada uma já está coberta pelo intervalo
  `on`-`off` desta entrada; o leitor as usa para destacar/silenciar sem exigir
  que o aluno as toque de novo. A cadeia segue os `<tie>` da partitura, então
  uma continuação pode estar em **outra camada ou outra pauta** que a cabeça
  (`s`/`l` são sempre os da cabeça). Numa repetição com casas, a cabeça da
  última passagem lista a nota ligada da casa que é de fato tocada em
  seguida (a da casa 2, sem sufixo `-rend<N>`, e não a da casa 1 para onde o
  `<tie>` aponta). Um id aparece em no máximo uma cadeia.
- `orn` (opcional, padrão `false`): `true` quando esta entrada é uma das
  notas curtas em que o MIDI expande um trinado/tremolo/mordente — várias
  entradas então compartilham o mesmo `id`. Ligadura não é rastreada através
  de um ornamento (`tied` não aparece nessas entradas).

**`pedal[]`**, uma entrada por evento de pedal de sustain, ordenada por `t`:

- `id` (obrigatório): `xml:id` do elemento `<pedal>` de origem. **Não**
  aparece no timemap (§2.4) — é um id novo, só neste arquivo.
- `t` (obrigatório, ms): mesmo relógio de `notes[].on`/`off`.
- `dir` (obrigatório): `"down"` ou `"up"`. Um `<pedal>` com `@dir="bounce"`
  (levanta e repressiona) gera duas entradas no mesmo `t` (o intervalo de
  0,1 tick que o `.mid` usa para separá-las some no arredondamento para ms).
  `@dir="half"` e um `<pedal>` sem `@dir` não geram evento — o exportador MIDI
  também não os trata.
- `s` (obrigatório): número da pauta a que o pedal se aplica.
- `c` (opcional, padrão `0`): canal MIDI; omitido quando `0`.

Limitações conhecidas, herdadas do exportador MIDI (`@func` do pedal — una
corda, sostenuto — não é distinguido de sustain; `TODO` em
`GenerateMIDIFunctor::VisitPedal`) e fora de escopo deste passo (dinâmica de
velocity, pedal de tablatura — não testado no corpus, que é de piano).

### 2.8 `pitchpos.json`

`midi.json` (§2.7) diz "o que soa" — ids expandidos, uma entrada por evento
MIDI. `pitchpos.json` (G04c, `docs/plano/G04c-contexto-por-evento.md`) diz
"como está escrito": para cada nota e pausa desenhada, o **contexto de
notação** de que o host precisa para calcular onde uma tecla qualquer
ficaria escrita naquele ponto da partitura (a nota fantasma, §10). A
geometria da pauta (linhas, unidade) **não** está aqui: depende do layout e
vai no nó `staff` da cena (§5.1), o que faz o mesmo arquivo servir às páginas
normais e às alternativas (§2.5).

```json
{
  "events": {
    "j97m9qh": { "t": "r", "co": -2, "key": { "c": 1, "f": 1 } },
    "orw55dt": { "t": "n", "co": -2, "key": { "c": 1, "f": 1 },
                 "pn": "b", "o": 3, "alt": 0, "loc": -3 },
    "f02-a": { "t": "n", "co": -2, "sh": 12, "pn": "c", "o": 5, "alt": 0, "loc": 5 },
    "f07-c": { "t": "n", "co": -2, "key": { "b": -1 }, "acc": { "b4": 0, "f4": 1 },
               "pn": "f", "o": 4, "alt": 1, "loc": 1 },
    "ex-pontuada": { "t": "n", "co": -2, "pn": "b", "o": 3, "alt": 0, "loc": -3,
                     "dur": 4, "dots": 1 },
    "ex-tercina": { "t": "n", "co": -2, "pn": "d", "o": 4, "alt": 0, "loc": -1, "dur": 8 },
    "ex-pausa": { "t": "r", "co": -2, "dur": 2 }
  }
}
```

(As duas primeiras entradas são do Satie — pausa e si3 na clave de Sol, armadura de
ré maior —, `f02-a` de `corpus/fantasma/f02-oitavas.mei`, um dó5 sob 8va, e `f07-c`
de `f07-acidentes.mei`, um fá#4 depois de um fá# e um si♮ escritos na outra camada.
As três últimas são **ilustrativas** — ids inventados, sem fixture — e mostram a
figura: uma semínima pontuada, uma colcheia de tercina e uma pausa de
mínima.)

- **Chave** = `xml:id` **notado** de nota ou pausa (`rest`, `mRest`). O
  contexto de notação é o mesmo em todas as passagens de uma repetição; para
  um id expandido do timemap (`-rend<N>`) o leitor usa `VsbDocument.sceneIdOf`
  (§2.4).
- `t` (obrigatório): `"n"` nota, `"r"` pausa.
- `co` (obrigatório): `clefLocOffset` da clave vigente **naquele ponto, na
  pauta onde o elemento é desenhado** (cross-staff incluído), o mesmo valor
  que `PitchInterface::CalcLoc` soma. Ex.: Sol na linha 2 = −2, Fá
  na linha 4 = 10. O leitor não deduz o valor.
- `sh` (opcional, padrão `0`): semitons entre som e escrita naquele ponto —
  transposição de instrumento + 8va/8vb vigentes. É a soma que
  `Note::GetMIDIPitch(transSemi, octaveShift)` faz: `som = escrita + sh`.
- `key` (opcional, padrão `{}`): alteração da **armadura vigente naquele
  ponto**, por letra minúscula (`"c"`…`"b"`, nessa ordem), valores −2…+2; só
  letras alteradas aparecem. Cobre armaduras não padronizadas e mudanças de
  armadura (a de um `<keySig>` dentro da camada, senão a da pauta no compasso).
- `acc` (opcional, padrão `{}`): alteração em vigor por letra+oitava
  (`"g4"`) **na coluna deste elemento**: acidentes escritos antes dele no
  mesmo compasso e na mesma pauta (todas as camadas) **mais** os escritos no
  mesmo instante e pauta (inclusive o do próprio elemento), −2…+2; `0` é um
  bequadro escrito. "Mesma pauta" é a pauta de desenho (cross-staff conta na
  pauta em que a nota aparece). Só entram as letras+oitavas cuja alteração
  **difere da armadura** (`key`); as demais valem a armadura. Todos os
  elementos do mesmo instante e pauta têm o mesmo `acc`. A regra é a da
  notação comum: um acidente vale só para a mesma oitava, até a barra.
- Só nota: `pn` (letra escrita, minúscula), `o` (oitava escrita), `alt`
  (alteração **sonora**, a que `Note::GetMIDIPitch` aplica: `accid.ges`, senão
  `accid`, senão 0 — o Verovio não aplica a armadura por conta própria; os
  importadores gravam `accid.ges` nas notas que a armadura altera), `loc` (o
  `loc` que o Verovio usou para desenhar a cabeça — cobre notas com `@loc`
  explícito). Invariante: `midi.p = altura(pn, o, alt) + sh` para toda nota
  com entrada em `midi.json` (§2.7; ornamentos expandidos à parte).
- `dur` e `dots` (opcionais; G08a, nota escondida, §11) — a **figura escrita**,
  para **nota e pausa**. `dur` é o denominador da figura, inteiro: `1`
  (semibreve), `2` (mínima), `4` (semínima), `8`, `16`, `32`, `64`, `128`, `256`,
  `512`, `1024`; é o valor de `DurationInterface::GetActualDur()`. `dots` é o
  número de pontos de aumento (`DurationInterface::GetDots()`, 0-4; ausente =
  `0`; só aparece com `dur`). Regras:
  - é o que está **escrito**: quiáltera, ligadura de prolongamento e fermata
    não a mudam (uma colcheia de tercina é `dur: 8`, não a duração sonora);
  - nota de acorde herda `dur`/`dots` do acorde;
  - **breve, longa, pausa de compasso inteiro (`mRest`) e figuras sem
    `@dur`** (notação mensural, nota sem duração na fonte) ficam **sem o
    campo**: o host trata a ausência de `dur` como "figura desconhecida";
  - o host não deve deduzir a figura do timemap (`qstamp` do `off` menos o do
    `on`): erra em quiáltera, em nota ligada e em fermata.
- Notas ocultas (`visible="false"`) têm entrada como as demais — o host pode
  esperá-las —, mas o nó delas na cena é `hidden`. Uma nota sem `@pname`
  (dado de origem incompleto) não tem entrada.
- **Layout (M05, §2.10; M05-P).** `loc` e `acc` dependem do layout das páginas.
  No carregamento, o layout só existe quando o documento é cortado (`--breaks`
  diferente de `none`, e não é MEI com layout codificado: `<pages>`). Sem esse
  corte, o `.vsb`, o JSON único e `renderToMusicJson` montam o layout antes de
  ler o `pitchpos` (só `renderToMusicJson` não chega a desenhar), e `loc`/`acc` saem preenchidos e
  iguais aos de `renderToBridgeJson` da mesma carga. Por isso, `loc` e `acc` **nunca**
  saem `null` numa saída do formato. Os demais campos não dependem de layout:
  medido no M05, a chamada sem nenhum layout de página dá `t`, `co`, `key`, `alt`,
  `pn`, `o`, `dur` e `dots` iguais aos do `.vsb` em `--breaks` auto (72 arquivos do
  corpus) e em line, smart e encoded (5 arquivos; em `line` a Mazurka não tem
  comparação, o HEAD cai nela); com `none` (72 arquivos), só `loc` e `acc`
  diferem do `.vsb`; num MEI com `<pages>` (`-t mei-pb`), `loc` difere (5 de 6
  notas no caso medido) e `co` é igual. O layout que faltava era só o de `loc`
  e `acc`, e é o que M05-P monta.
- **Som e notação podem divergir na fonte.** `alt` é o que soa; `key`/`acc`
  são o que a notação escrita diz. Numa fonte fiel os dois concordam
  (`alt == acc[<letra><o>] ?? key[<letra>] ?? 0` para toda nota sem acidente
  desenhado); medido em G04d, isso vale para 8 566 de 9 039 notas do corpus, e
  as 473 restantes são dados de origem em que o som não segue a notação
  (457 do Étude Op. 10 nº 9, cuja `<scoreDef>` não traz `key.sig`, só
  `accid.ges`; 16 em quatro peças, acidentes que o importador estende a
  outras oitavas ou notas sem acidente escrito).

### 2.9 `music.json`

A estrutura musical da partitura **notada**, sem geometria (M00,
`docs/plano/M00-dados-musicais-para-o-aprendizado.md`): partes, compassos, fórmula,
armadura e modo, casas, pautas, camadas e eventos, ornamentos, cifras, direções e
andamentos. Tudo sai do `Doc` do Verovio (não do desenho), então o mesmo conteúdo
serve ao `.vsb`, ao JSON único e, no M05, a uma chamada que não desenha página.

Trecho (um compasso e uma cifra; o arquivo completo é a fixture do M02, descrita no fim desta seção):

```json
{
  "version": 1,
  "parts": [ { "id": "P1", "name": "Piano", "staves": [1, 2] } ],
  "measures": [
    {
      "id": "yy2zfkq", "index": 1, "n": "1",
      "left": "rptstart", "right": null, "ending": null,
      "meter": { "count": 3, "unit": 4, "sym": null },
      "key": { "sig": "0", "fifths": 0, "mode": "major" },
      "staves": [
        { "n": 1, "layers": [
          { "n": 1, "events": [
            { "id": "orw55dt", "t": "n", "chord": null, "grace": "acc", "tuplet": null },
            { "id": "r1c5f34m", "t": "n", "chord": null, "grace": false, "tuplet": { "num": 3, "numbase": 2 } }
          ] }
        ] }
      ]
    }
  ],
  "ornaments": [ { "id": "wg8qvcs", "kind": "trill", "measure": 1, "startid": "vlc2j9p", "tstamp": null } ],
  "harmonies": [
    { "id": "j97m9qh", "measure": 1, "staff": 1, "tstamp": 1,
      "root": "C", "rootAlter": 0, "kind": "major-seventh", "kindText": null,
      "bass": null, "bassAlter": null, "degrees": [], "numeral": null, "text": "CMaj7" }
  ],
  "directions": [ { "id": "hp9pij7", "measure": 4, "staff": 1, "tstamp": 1, "place": "above", "text": "chg" } ],
  "tempi": [ { "id": "s2mypdb", "measure": 0, "bpm": 80, "text": "Andante" } ]
}
```

**Regras normativas.**

1. **Ordem e ids.** `measures` está na ordem do documento **notado**, sem
   desdobrar repetições: as casas aparecem uma depois da outra, como estão
   escritas. Entram a introdução (`n` como `"1i"`) e os compassos depois de uma
   barra final, que o timemap não toca. `index` é a posição 0-based nessa lista
   (a "ocorrência" do M00, base 1, menos 1). Todo `id` é um `xml:id` **notado**:
   o da cena, o do `pitchpos.json` e o da primeira passagem do timemap. Este
   arquivo não traz ids `-rend<N>`; quem precisa de uma ocorrência usa o timemap
   (§2.4) e o tempo dela (D-MUSICA-Q).
2. **`n`, `left`, `right`, `ending`.** `n` é o `@n` do compasso, sem
   interpretação (`"1"`, `"1i"` na introdução, `"0"` na anacruse). `left` e
   `right` são o `@left`/`@right` do MEI quando existem (`rptstart`, `rptend`,
   `rptboth`, `end`, `dbl`...), senão `null`. `ending` é `null`, ou `{"n": ...}`
   quando o compasso está dentro de uma casa (`<ending>`): o valor é o
   `@number` da casa, **como o MEI o grava**, isto é, a lista de números
   separada por vírgula (`"2,3,4"` no corpus medido; `"2, 3"` na fixture, com o
   espaço da fonte). Não é o texto impresso (`"2. 3. e 4."`), que o importador
   não guarda (`iomusxml.cpp` L428; M01). O leitor separa por vírgula e ignora
   os espaços.
3. **`meter` e `key`.** Todo compasso traz os dois, com os valores **vigentes no
   começo dele** na primeira pauta, mesmo quando não mudam: o leitor não compara
   com o compasso anterior. (A frase do M00, item 3, era ambígua
   nesse ponto; esta é a leitura fechada.) `meter.count` e `meter.unit` são sempre inteiros (C =
   4/4; C cortado = 2/2). `meter.sym` é `"common"` ou `"cut"` quando a fonte pede
   `symbol` (`<time symbol>`), senão `null`. `key.sig` é o `@sig` do MEI
   (`"0"`, `"2s"`, `"3f"`), `null` quando a armadura não tem nome padrão.
   `key.fifths` é a soma das alterações (sustenido +1, bemol −1), também para
   armadura fora do padrão. `key.mode` é o `@mode` do `keySig` (`"major"`,
   `"minor"`, `"dorian"`...), ou `null` quando a fonte não traz `<mode>`: o
   importador só lê `<mode>` no ramo `<fifths>` (M01).
4. **`staves`, `layers` e `events`.** Cada compasso lista as pautas com eventos,
   pelo `staff/@n` **global** da partitura (o `staffDef/@n` do MEI). Cada pauta
   lista as camadas pelo `layer/@n`, que é o `<voice>` da fonte (M01: 0
   divergências). Uma pauta pode ter várias camadas (fixture: camadas 5 e 6 na
   pauta 2). Dentro de uma camada, os eventos estão na ordem do documento:
   - `id`: o `xml:id` do evento (nota, pausa, `mRest` ou espaço);
   - `t`: `"n"` nota, `"r"` pausa, `"mr"` pausa de compasso, `"s"` espaço
     (`space`);
   - `chord`: o `xml:id` do `<chord>` a que a nota pertence (todas as notas do
     acorde trazem o mesmo id); `null` fora de acorde e em pausa;
   - `grace`: `false`, ou `"acc"`/`"unacc"` como vem do `@grace` do MEI da nota
     (ou do `<graceGrp>` pai); `false` em pausa. Ver a ressalva R1 (refutada no
     M07: o valor é o do MEI);
   - `tuplet`: `{"num": n, "numbase": b}` da quiáltera **mais interna** que
     contém o evento (`@num`/`@numbase` do MEI); `null` fora de quiáltera. A
     razão composta fica fora (ver "Fica fora").
   - **Pauta de um evento cruzado** (M01): uma nota que a fonte põe numa pauta e o
     Verovio desenha em outra fica na pauta do próprio nó: o `@staff` do `note`
     ou do `chord`, senão a pauta que o contém. A camada continua a que o Verovio
     guarda (o `layer` de origem). Medido: 123 notas em Clair de Lune e 2 em
     Nocturne.

   Todo evento traz os cinco campos (`id`, `t`, `chord`, `grace`, `tuplet`); em
   pausa, `chord` é `null` e `grace` é `false`. (O exemplo do M00 omitia esses
   campos na pausa; a spec os fixa.)
   **Implementação (M03):** uma camada que o notado tem sem nenhuma nota ou
   pausa sai com `"events": []` (12 casos no corpus: 2 no Clair de Lune e 10 na
   Gymnopédie). Cada pauta sai com as camadas que o notado tem; no corpus medido
   nenhuma pauta de compasso fica sem evento.
5. **`parts`.** Uma entrada por parte, conforme o formato da fonte (o `Doc` guarda
   o formato lido, `GetSourceFormat()`, que não sai em nenhuma saída):
   - **MusicXML:** uma entrada por `<part>`. `id` é o id da parte (`P1`, na fixture):
     o `xml:id` do `staffDef` quando a parte tem uma pauta, ou do `staffGrp` quando
     tem várias (M01: achado em todas as partes medidas). `staves` são as pautas dela.
   - **MEI:** uma entrada por `staffGrp` do primeiro `scoreDef`. Um `staffGrp` que
     tem `staffGrp` filhos dá uma entrada por filho; um `staffDef` solto nele dá uma
     entrada por `staffDef`. Um `staffGrp` **sem** `staffGrp` filho é uma entrada só,
     com todas as pautas dele: é o MEI sem partes (pauta dupla de um piano, por
     exemplo). `id` é o `xml:id` do `staffGrp` (ou do `staffDef`, sem grupo).
   - `name` é o `label` da parte (do `staffGrp` ou do `staffDef`), ou `null`. Uma
     entrada sem pauta não sai.
   **Implementação (M03, R-PARTES resolvida em 2026-11-08 pela decisão de origem):**
   o MusicXML sai como antes. No MEI, o `staffGrp` externo com duas `staffDef` (os 5
   MEI de `corpus/mei/`) sai com **uma** entrada e as duas pautas. Um MusicXML
   convertido por Humdrum (`MUSICXML_DEFAULT_HUMDRUM`) chega como MEI e segue a regra
   do MEI.
6. **`ornaments`.** Os controles `trill`, `mordent` e `turn`. `kind` é o nome do
   elemento. `measure` é o `index` do compasso que contém o controle (base 0, como em
   `measures`). `startid` é o `@startid` do MEI **sem o `#`**: o id da nota, ou o do
   `chord` quando a nota pertence a um acorde (medido na fixture: o trinado da nota
   C4 do acorde aponta para o `chord`), ou `null`. `tstamp` é o `@tstamp` do MEI
   (batida a partir de 1, na unidade do compasso), ou `null`. **Cada item tem
   `startid` ou `tstamp` não nulo** (pelo menos um dos dois; o esquema exige). Um
   controle sem os dois, ou fora de compasso, sai com aviso. Fermata e os demais
   controles ficam fora.
   **Implementação (M03, R-TRINADO resolvida em 2026-11-08, usuário: relaxar o
   esquema):** os 12 trinados do Scarlatti (só `@tstamp`, sem `@startid`) entram, com
   `startid` `null`. Os 2 com `@startid` ganham `measure` e `tstamp` (`null` quando o
   controle não tem `@tstamp`).
7. **`harmonies`** (D-MUSICA-CIFRA): uma por `<harmony>` da fonte. Medido no M01 e
   no M02: todo `<harmony>` chega ao MEI como `harm` (0 divergências nos arquivos
   com fonte MusicXML).
   - `id`: o `xml:id` do `harm`; `measure`: o `index` do compasso; `tstamp`: o
     `@tstamp` do MEI (batida a partir de 1, na unidade do compasso).
   - `staff`: a pauta da cifra é a **pauta da parte onde está o `<harmony>`**,
     que é o `@staff` do `harm`. O MusicXML não traz pauta em `<harmony>` (nenhum
     `<harmony>` do corpus tem `<staff>`). Medido: em todas as cifras dos arquivos
     com fonte MusicXML do M01, a pauta do `harm` é a única pauta da parte. Em
     parte de duas pautas, a regra não foi medida no corpus (ressalva R2). Um
     `harm` sem `@staff` (MEI que não o traz) sai com a primeira pauta do compasso
     (M04; o schema exige um inteiro).
   - `root` e `rootAlter`: `root/root-step` e `root/root-alter` (inteiro; `0`
     quando o elemento falta). `null` quando não há raiz (numeral, abaixo).
   - `kind`: o texto de `<kind>`, **sem tradução** (`"major-seventh"`,
     `"dominant"`); `null` se não houver. `kindText`: o atributo `kind/@text`, ou
     `null`. Quando `kindText` existe (49% das cifras do corpus), é ele que o
     desenho usa como qualidade.
   - `bass` e `bassAlter`: `bass/bass-step` e `bass/bass-alter` (`0` quando o
     elemento falta); `null` sem baixo.
   - `degrees`: uma entrada por `<degree>`, na ordem da fonte: `{"value",
     "alter", "type"}` de `degree-value`, `degree-alter` (`0` quando falta) e
     `degree-type` (`add`, `alter` ou `subtract`).
   - `numeral`: para numeração romana (sem `root`), `{"root", "alter"}`. `root` é
     o texto do `numeral-root` como o importador o lê (o atributo `text`, se
     houver, senão o conteúdo; ex.: `"V"`), e `alter` é o `numeral-alter` (`0`
     quando falta). **Sem caso real no corpus medido** (M01): não há fixture
     (ficam para o M07).
   - `text`: o texto que o Verovio desenha (o `Harm` montado pelo importador;
     ex.: `"CMaj7"`, `"G7(♭9)/B"`). Nunca vazio. Quando o `kind` não tem nome no
     mapa do importador e não há `kind@text`, o texto sai sem o sufixo de
     qualidade; o leitor deve consultar `kind` para não exibir uma cifra
     incompleta (o M01 não encontrou esse caso no corpus).
   - De um MEI, onde só há o texto, os campos estruturados saem `null` (com
     `degrees: []`) e `text` vale.
   - **Fica fora (M04):** o `harm` com `fb` (cifra de baixo cifrado, do
     `<figured-bass>` do MusicXML) não é `<harmony>`; e a cifra sem `@tstamp` ou
     fora de compasso sai com aviso, como o trinado sem `@startid`.
   - `text` sai do `Doc` (o `Harm` que o desenho usa), não do MEI, então é o texto
     exato que o Verovio desenha; o bemol sai como `♭` (U+266D).
8. **`directions`**: uma por `<direction>` com `<words>` que o importador grava
   como `dir`.
   - `text`: o texto de `<words>` **cru** (sem formatação), concatenado na ordem do
     documento, sem separador (como o desenho junta, `TextRendition`). Sai do `Doc`
     (M04), então `<words>` com formatação (`rend`) chega inteiro, sem o espaço de
     indentação que o MEI pode ter em volta do `<rend>`. Um `dir` sem texto (coda,
     segno) não entra.
   - `place`: `"above"` ou `"below"` (`@placement` da fonte); `null` sem ele.
   - `staff`: a pauta que o importador dá ao `dir` (o `<staff>` da `<direction>`,
     senão a primeira pauta da parte). `measure` e `tstamp` como nas cifras.
   - **Fica fora:** a direção com `<sound tempo>` ou `<metronome>` (vai a
     `tempi`, mesmo com `<words>`) e a de dinâmica (`dynam`, que o `midi.json` e
     a cena já levam; G10). Medido no M01: dos 137 `<words>` do corpus, 39 viram
     `dir`; os demais viram `tempo` ou `dynam`.
9. **`tempi`**: uma entrada por `tempo` do MEI (de `<sound tempo>`, de
   `<metronome>` ou de uma direção de andamento): `bpm` é o `@midi.bpm` (número) ou
   `null`; `text` é o texto desenhado (ex.: `"Andante"`) ou `null`.

`version` é `1`, o mesmo do manifest (§2.1); o leitor recusa valor maior (§9).

**Fica fora deste arquivo:**

- Layout, geometria e glifos (§5): nada disso entra em `music.json`.
- Tempo da partitura notada (`q`, `ql`): fica fora (D-MUSICA-Q); o app recompõe
  o tempo pelo timemap.
- Altura, figura e ligadura por nota: estão no `pitchpos.json` (§2.8) e no
  `midi.json` (§2.7); não se duplicam.
- Dinâmica, pedal, cunha, ligadura de expressão e articulação: `midi.json` e
  G10.
- Quiáltera com razões compostas: `tuplet` leva só a mais interna.
- Notação mensural, tablatura, percussão, e partes além da primeira (o app só
  usa a primeira; `parts` as lista todas).

**Ressalvas (abertas, medidas no M01 e no M02):**

- **R1 — `grace`: refutada no M07.** O importador do MusicXML grava o valor
  que o MEI pede: apojatura (sem barra) → `"acc"` (acentuada, como o MEI define
  `acc`); acciaccatura (com barra, `slash="yes"`) → `"unacc"` (`iomusxml.cpp`,
  L3370-3377). Não há inversão, e o importador não muda. O oráculo do M07 (que lê
  o MusicXML direto) confere os 6 364 eventos do corpus MusicXML e os 141 214 dos
  600 hinos com essa regra. A barra vem em `stem.mod="1slash"`, então o desenho também está certo.
- **R2 — pauta de cifra em parte de duas pautas.** Não medida no corpus (nenhum
  `<harmony>` em parte de duas pautas). A fixture mostra o caso sintético: a
  cifra sai na primeira pauta da parte.
- **R3 — notas invisíveis** (`print-object="no"`). O M01 supôs que não entram no
  `Doc`; o M07 mediu que a maioria entra (o Verovio as exporta com a invisibilidade
  perdida: 42 camadas do Clair de Lune). Descartam-se as pausas invisíveis da
  Gymnopédie n.º 1 (10 compassos) e 2 camadas do Clair de Lune; e notas invisíveis
  abrem ou fecham colchetes de quiáltera, o que muda o `tuplet` das notas em volta
  (4 eventos do compasso 22 do Clair de Lune). A conferência do M07 trata esses
  casos como causa conhecida, com a lista no M00 ("Notas de execução", M07). O
  `music.json` não traz a visibilidade: o leitor que precisa dela usa o notado.
- **R4 — `numeral`, `time symbol` e `orn`.** `time symbol` e `orn` (trinado) estão
  na fixture; `numeral` não tem caso real no corpus e fica para o M07.
- **R5 — `ending.n` com espaços.** Vem como a fonte o escreve (`"2, 3"`); o
  leitor separa por vírgula e tira os espaços (§2.9, regra 2).
- **R6 — espaços de preenchimento (M07).** O importador do MusicXML cria `space`
  para cobrir lacunas da camada (`FillSpace`, `iomusxml.cpp` L559): antes de cada
  nota ou pausa, se o fim da camada vem antes do início dela (um `<forward>`, ou
  uma voz que ainda não chegou). Esses `s` não são pausas escritas. O leitor trata
  o `s` como espaço, em qualquer posição da camada, e não como pausa. O `tuplet` de
  um `s` de preenchimento segue o colchete aberto no importador, não a partitura.
  Medido: 147 515 notas do corpus e dos hinos, todas com a camada de `<voice>`
  (`layer n` = voz em todas); só a pauta muda, em 131 notas cruzadas (o `@staff` do
  nó é o da nota).

**Fixture do M02.** `docs/formato/musica/m02-entrada.musicxml` (MusicXML 3.1
sintético, duas partes, seis compassos, legível) e
`docs/formato/musica/m02-esperado.json` (o `music.json` esperado). Foram escritos
à mão e conferidos contra o MusicXML e contra o MEI do Verovio gerado com
`verovio -x 42 -t mei` (semente fixa). Os `xml:id` da fixture são os que o
Verovio dá com essa semente nesta versão do fork: o M03 precisa reproduzi-los
para o teste. O schema é `$defs/musicDocument` em `schema-v1.json`.

Cobertura (compasso = `index`, 0-based):

| Item do aceite do M02 | Onde na fixture |
| --- | --- |
| Repetição com casas | barra de início no compasso 1 (`left` "rptstart"); compasso 2 dentro da casa 1 (`ending.n` "1") com `right` "rptend"; compasso 3 dentro da casa "2, 3" (`ending.n` "2, 3") |
| Anacruse | compasso 0: `n` "0", `implicit="yes"` (MEI `metcon="false"`), 1 semínima em 3/4; é o `index` 0 |
| Mudança de armadura | compasso 3: de Dó maior (`mode` "major") para Ré maior (`sig` "2s", `mode` null) |
| Mudança de fórmula | compasso 4: 3/4 → 4/4 com `sym` "common"; compasso 5: → 2/2 com `sym` "cut" |
| Apojatura | compasso 1: D5 sem barra antes de C5, `grace` "acc" (valor do MEI; R1, refutada no M07) |
| Acciaccatura | compasso 2: D5 com barra antes de E5, `grace` "unacc" (valor do MEI; R1, refutada no M07) |
| Quiáltera | compasso 1: E5-F5-G5 em 3:2, `tuplet` `{"num": 3, "numbase": 2}` |
| Acorde | compasso 1: C4+E4, `chord` "vlc2j9p" nas duas notas |
| Duas camadas numa pauta | compasso 1: pauta 2 com as camadas 5 e 6 (nos demais, a pauta 2 tem só a camada 5) |
| Cifra com `kind`, `degree` e baixo | compasso 3: G, `kind` "dominant" com `kindText` "7", `degree` 9 alter −1 add, baixo B; `text` "G7(♭9)/B" |
| Cifra sem `kindText` | compasso 1: C, `kind` "major-seventh", `text` "CMaj7" |
| Direção `chg` | compasso 4, pauta 1, `place` "above" |
| Pausa de compasso (`mr`) | compasso 4, pauta 2 |
| Direção excluída (dinâmica `p`) | compasso 1: não entra em `directions` |
| Andamento com texto | compasso 0: "Andante", 80 |
| Trinado | compasso 1, na nota C4 do acorde: `startid` "vlc2j9p" (o `chord`), `measure` 1, `tstamp` `null` |
| Partes | `P1` (pautas 1 e 2, "Piano"), `P2` (pauta 3, "Canto") |
| Não coberto | `numeral` (R4; M07) |

Conferência: `compare/out/m02/check_m02.py` (saída em `compare/out/`, não versionada)
confere o schema (Draft 2020-12), os eventos por (compasso, pauta, camada)
contra o MusicXML, os ids, as casas, as barras, as cifras, a alça do trinado e
a fórmula e a armadura de cada compasso.

### 2.10 `renderToMusicJson` (M05)

`Toolkit::RenderToMusicJson()` (C: `vrvToolkit_renderToMusicJson(tk)`; Dart:
`renderToMusicJson()`) devolve **um objeto JSON** com a estrutura do documento
notado, sem desenho (o layout das páginas, quando falta, é montado sem desenhar: M05-P):

```json
{ "timemap": [ ... ], "midi": { ... }, "pitchpos": { ... }, "music": { ... } }
```

- Cada chave tem o corpo de §2.4, §2.7, §2.8 e §2.9 e a regra de omissão de §2.2
  (a chave some quando o documento não tem o dado). Não há `manifest`, `glyphs`,
  `scene`, `alternates` nem `meta`: nada é desenhado.
- Os ids são os da carga: na mesma carga, os corpos de `timemap`, `midi`,
  `pitchpos` e `music` são iguais aos de `renderToBridgeJson` (medido nos 72
  arquivos do corpus, nas duas ordens de chamada).
- Não há `Select` nem `RedoLayout`. Quando o carregamento não cortou o documento
  (`--breaks none`, MEI com `<pages>`), a chamada monta o layout das páginas
  (`Toolkit::LayOutPagesWithoutDrawing`, M05-P) e não desenha nenhuma. `getMEI`,
  `renderToTimemap` e `renderToSVG` dão o mesmo resultado antes e depois da chamada.
- `pitchpos` segue §2.8: `loc` e `acc` saem preenchidos nos dois casos, iguais
  aos de `renderToBridgeJson` da mesma carga (M05-P; antes saíam `null` sem corte).
- Esquema: `$defs/musicJsonDocument` em `docs/formato/schema-v1.json`.

## 3. Unidades e ajuste de página

Todas as coordenadas de desenho estão em **unidades de viewBox** — exatamente
o que o `DeviceContext` recebe (unidades de definição do Verovio,
`DEFINITION_FACTOR = 10` por px lógico), com o eixo Y apontando para baixo.
Nenhum arredondamento adicional é aplicado; a serialização canônica limita os
números a no máximo 6 dígitos significativos.

Cada página carrega o ajuste já calculado, reproduzindo a semântica do
`<svg class="definition-scale">` do Verovio
(`preserveAspectRatio="xMidYMid meet"`, ver `src/svgdevicecontext.cpp`
`SvgDeviceContext::StartPage`):

```text
vw = width * viewBoxFactor
vh = contentHeight * viewBoxFactor
widthPx  = baseWidth  ou ceil(width  * userScaleX)
heightPx = baseHeight ou ceil(height * userScaleY)
scale = min(widthPx / vw, heightPx / vh)
tx = (widthPx  - vw * scale) / 2
ty = (heightPx - vh * scale) / 2
```

Em modo fac-símile, o `viewBox` do SVG usa `[0, 0, width, height]`; nos demais
modos usa `[0, 0, width * viewBoxFactor, contentHeight * viewBoxFactor]`. O
cálculo de `fit` usa as dimensões gravadas em `viewBox`, reproduzindo exatamente
essa escolha do `StartPage`.

O renderizador aplica `translate(tx, ty)`, `scale(scale)` e depois
`translate(origin)` uma vez por página, antes de percorrer a árvore. Os valores
de `fit` vão prontos no arquivo para que C++ e Dart nunca divirjam por
arredondamento.

## 4. `glyphs.json` — dicionário de glifos

```json
{
  "Leipzig:E0A4": {
    "font": "Leipzig",
    "codepoint": "E0A4",
    "unitsPerEm": 2048,
    "horizAdvX": 656,
    "bbox": [-10, -262, 552, 262],
    "paths": [
      {
        "closed": true,
        "v": [x0, y0, x1, y1],
        "i": [0, 0, 0, 0],
        "o": [0, 0, 0, 0]
      }
    ]
  }
}
```

- A chave é `"<fonte>:<codepoint hex maiúsculo>"`.
- `paths` está em **unidades de fonte**, já com o `transform="scale(1,-1)"` do
  XML do Verovio aplicado (é o que o `svgpathparser` faz hoje). O contorno já
  está no sistema de coordenadas de tela, bastando escalá-lo.
- `v`/`i`/`o` são arrays **planos** de números (pares x,y): `v` = vértices,
  `i` = tangente de entrada relativa ao vértice, `o` = tangente de saída
  relativa ao vértice. Os três arrays têm o mesmo comprimento e cada um tem
  comprimento par.
- `bbox` é `[x, y, largura, altura]`, vindo de `Glyph::GetBoundingBox()`. Ele
  usa a escala interna do Verovio: os valores são 10 vezes a escala dos
  contornos (`DEFINITION_FACTOR = 10`) e o eixo Y aponta para cima, conforme a
  convenção SMuFL. Portanto, `bbox` **não** é um `Rect` no sistema dos
  contornos. Para compará-lo com `paths`, converta para:
  `left = x / 10`, `top = -(y + altura) / 10`, `right = (x + largura) / 10`,
  `bottom = -y / 10`.
- **Glifos reservados.** O dicionário traz **sempre**, da fonte da peça,
  mesmo sem nenhuma instância `u` — 16 glifos:
  - `E0A4` (cabeça preta), `E260`/`E261`/`E262` (♭/♮/♯), `E511`/`E512`
    (8va/8vb) e `E515`/`E516` (15ma/15mb): a nota fantasma (§10) desenha só
    com eles, sem consultar a fonte;
  - `E4E3` (pausa de semibreve), `E4E4` (mínima), `E4E5` (semínima), `E4E6`
    (colcheia), `E4E7` (semicolcheia), `E4E8` (fusa), `E4E9` (semifusa) e
    `E1E7` (ponto de aumento): a pausa que substitui uma nota escondida
    (§11) é de uma figura qualquer, e o dicionário só traria as pausas que a
    peça usa. `E1E7` é reservado para um leitor que prefira desenhar o ponto
    como glifo; o caminho canônico é o círculo da §11, regra 6.
- `font`, `codepoint`, `unitsPerEm` e `horizAdvX` vêm dos metadados do `Glyph`
  do Verovio e permitem um segundo caminho de render por TTF no futuro. O
  caminho canônico — e o único que precisa bater a paridade — é o dos contornos.

### 4.1 Conversão para `Path` (normativo)

```text
moveTo(v[0])
para k de 0 até n-2:
    cubicTo(v[k] + o[k], v[k+1] + i[k+1], v[k+1])
se closed:
    cubicTo(v[n-1] + o[n-1], v[0] + i[0], v[0]); close()
```

## 5. `scene.json` — páginas e árvore

```json
{
  "pages": [
    {
      "index": 0,
      "width": 2100,
      "height": 2970,
      "contentHeight": 2970,
      "viewBoxFactor": 10.0,
      "viewBox": [0, 0, 21000, 29700],
      "baseWidth": 2100,
      "baseHeight": 2970,
      "userScaleX": 1.0,
      "userScaleY": 1.0,
      "widthPx": 2100,
      "heightPx": 2970,
      "fit": { "scale": 0.1, "tx": 0.0, "ty": 0.0 },
      "origin": [500, 500],
      "root": { "...": "nó" }
    }
  ]
}
```

Todos os campos vindos de `BridgePage` são serializados. `viewBox`,
`widthPx`/`heightPx` e `fit` são derivados, mas também são gravados para que o
leitor não refaça a métrica da página — são poucos números por página. O
índice plano de elementos endereçáveis **não** é gravado: o leitor o constrói
no mesmo percurso em que monta a árvore (§5.5).

### 5.1 Nó (grupo)

```json
{
  "t": "g",
  "id": "note-0000001386",
  "class": "note",
  "color": "#ff0000",
  "hidden": false,
  "rotate": { "angle": -45.0, "origin": [1200, 3400] },
  "bbox": [x0, y0, x1, y1],
  "children": []
}
```

- `id` — o `xml:id` do objeto (ausente quando o Verovio não emite um id
  primário). É a chave usada pelo host para colorir/animar.
- `class` — `Object::GetClassName()` (+ classes extras) ou o nome do grupo
  customizado, como no `class=` do SVG.
- `color` — cor CSS resolvida (`@color` ou `SetCustomGraphicColor`), normalizada
  para `#rrggbb` minúsculo. Ausente = herda do ancestral.
- `hidden` — `true` quando o grupo está invisível (`g.CSS_SHOW_HIDDEN` / opção
  `showHidden` desligada); o renderizador não desenha e não conta na bbox.
- `rotate` — presente somente quando `RotateGraphic` foi chamado; ângulo em
  graus e pivô em unidades de viewBox, na convenção do SVG
  `rotate(a, ox, oy)`.
- `bbox` — união das bboxes dos filhos em unidades de viewBox, depois das
  transformações locais, **no referencial de conteúdo, antes do
  `translate(origin)`** (o renderizador soma `origin` uma vez por página, ver
  §3 — portanto a comparação correta contra o `viewBox` é `bbox + origin`).
  É emitida para todo nó com `id` e para nós de classe
  `measure`, `staff`, `system` e `page`; é opcional nos demais.
- `children` — ordem de documento: o último pinta por cima.
- **Só nó `staff`** (G04b; geometria da pauta para a nota fantasma, §10; todos
  aditivos, no mesmo referencial que `bbox`):
  - `lines`: `[topY, unit, n]` — y da linha de cima, meio-espaço (`unit`, a
    distância entre uma linha e o espaço seguinte; o `loc` sobe 1 por
    `unit`) e número de linhas. A linha `k` (0 = de cima) está em
    `topY + 2·k·unit`. Coincide com os `n` primeiros filhos `p` do nó.
  - `ledger`: `[espessura, extensão]` das linhas suplementares de tamanho
    normal nessa pauta; `extensão` é quanto a linha ultrapassa a cabeça de
    cada lado. `ledgerCue`: o mesmo para notas cue/grace, presente só se
    diferente.
  - `gs`: `[sx, sy]` de um glifo de tamanho normal nessa pauta (é o que a
    cabeça preta da fantasma usa quando o alvo é uma pausa; para uma nota,
    cue/grace incluídos, ela herda a escala da cabeça esperada, §10).
- **Só nó `measure`** (G11, D-SUM-COMPASSO; aditivo, no mesmo referencial que
  `bbox`): `inner`: `[x0, x1]` — a faixa horizontal em que o Verovio centra a
  pausa de compasso (`mRest`), isto é, de onde começa o miolo do compasso até a
  borda esquerda da barra final. `x0` = `Measure::GetDrawingX() +
  GetLeftBarLineRight()` e `x1` = `GetDrawingX() + GetRightBarLineLeft()`: sem
  barra de repetição à esquerda, `x0` é o primeiro x do compasso **depois** de
  clave, armadura e fórmula de compasso (se o compasso as traz) mais uma margem
  que o Verovio reserva e que **não** está em nenhum outro lugar da cena (87 a
  90 unidades, e 125 quando só há clave: medido em G11). O centro que o
  Verovio usa é `x0 + ⌊(x1 − x0) / 2⌋` (divisão inteira). Ausente em `.vsb` de
  antes de G11: leitor antigo e referência tratam como "sem pausa de compasso".
- **Só nó de nota, acorde e pausa cross-staff:** `staff` = `id` do nó `staff`
  em que o elemento é desenhado. Ausente = a pauta ancestral na árvore.

### 5.2 Formas

Todas aceitam os campos de estilo comuns `fill`, `fillOpacity`, `stroke`,
`strokeWidth`, `strokeOpacity`, `lineCap`, `lineJoin` e `dash` (`[traço,
intervalo]`).

- `fill`/`stroke` ausentes significam **herdar** a cor corrente.
- `"none"` significa não pintar aquele canal.
- `fillOpacity`/`strokeOpacity` ficam no intervalo `[0, 1]`.
- `lineCap` usa `default`, `butt`, `round` ou `square`.
- `lineJoin` usa `default`, `arcs`, `bevel`, `miter`, `miter-clip` ou `round`.
- `dash` é omitido quando não há tracejado; quando presente, seus dois números
  são `dashLength` e `gapLength`.
- Por padrão o Verovio aplica `stroke:currentColor` a `path`, `polygon`,
  `polyline`, `rect` e `ellipse` (regra CSS global do SVG). O exportador resolve
  isso em `stroke` + `strokeWidth` — **exceto quando a largura da pena é 0**
  (`DrawFilledRectangle`, `DrawObliquePolygon`, `DrawDot`, `DrawVerticalDots`:
  feixes, colchetes de pedal, pontos de aumento/repetição). Pena 0 significa
  "só preenchimento" no `View`; o hairline de 1 unidade que o SVG mostra ali é
  um artefato da regra global, quase invisível no `resvg`, mas o Impeller o
  alarga em um pixel inteiro nas formas finas (R06b). Nesses casos o exportador
  emite `"stroke": "none"` (`hasStroke = false).

```json
{ "t": "p", "paths": [{ "closed": true, "v": [], "i": [], "o": [] }] }
{ "t": "r", "x": 0, "y": 0, "w": 100, "h": 20, "rx": 0 }
{ "t": "e", "cx": 0, "cy": 0, "rx": 50, "ry": 50 }
```

`BridgeShape.hasFill` e `hasStroke` controlam a presença de `fill` e `stroke`:
`false` vira `"none"`; `true` com cor `COLOR_NONE` omite o campo (herança);
`true` com cor explícita vira `#rrggbb`. `fillOpacity` e `strokeOpacity` são
omitidos quando valem `1.0`.

### 5.3 Uso de glifo

```json
{ "t": "u", "g": "Leipzig:E0A4", "x": 12000, "y": 4300, "sx": 3.2, "sy": 3.2 }
```

- `sx`/`sy` = `pointSize / unitsPerEm * DEFINITION_FACTOR`, com
  `widthToHeightRatio` aplicado em `sx` quando diferente de 1, exatamente como
  `MakeGlyphShape` calcula hoje.
- A largura de traço herdada do SVG para glifos é `strokeWidth = sy`; `fill` e
  `stroke` herdam a cor corrente. Um `fill`/`stroke` explícito no objeto
  sobrepõe.
- `u` substitui o baking de contorno no formato final: os contornos ficam no
  dicionário e cada ocorrência é uma referência.

### 5.4 Run de texto comum

```json
{
  "t": "t",
  "s": "Andante",
  "x": 8000,
  "y": 2100,
  "size": 360.0,
  "align": "left",
  "letterSpacing": 0.0,
  "bold": false,
  "italic": true,
  "family": "Liberation Serif"
}
```

- `s` vem de `BridgeTextRun.text`.
- `x`/`y` vêm de `origin`, antes do deslocamento de alinhamento.
- `align` usa `left`, `center` ou `right`, mapeados respectivamente para
  `text-anchor=start`, `middle` e `end`. `none` e `justify` são normalizados para
  `left` pelo exportador.
- `size` já está em unidades de viewBox.
- `letterSpacing` vem de `letterSpacing` e é `0.0` quando ausente no font state.
- `bold` e `italic` são o resultado final: `FONTWEIGHT_bold` vira `bold: true`,
  `FONTSTYLE_italic`/`oblique` vira `italic: true`, e as regras CSS por classe
  dos ancestrais já foram aplicadas.
- `family` vem do `FontInfo` ativo no momento do run; não é inventada pelo
  leitor. O valor é o nome da família/TTF que o renderizador deve usar.
- `color` segue a mesma regra de herança dos nós.
- Runs cujos caracteres são todos codepoints SMuFL cobertos pelas fontes do
  projeto não viram `t`: viram usos de glifo (`u`).

### 5.5 Índice de elementos endereçáveis (derivado, não gravado)

O formato **não** carrega o índice plano de elementos endereçáveis. Ele é
inteiramente derivável da árvore, e o leitor o constrói no mesmo percurso em
que monta `root` — custo desprezível, já que esse percurso acontece de
qualquer jeito. Até 2026-09-20 ele era gravado em `pages[].elements` como
redundância deliberada; medido no corpus, custava **20,5% do `scene.json`** e
**29,3% do `.vsb`**, e foi removido (decisão do usuário; ver
`docs/relatorio-paridade.md`).

A regra de derivação, que o leitor deve seguir para chegar ao mesmo índice:

```
nodePath = -1
percorrer(nó):
    nodePath += 1
    se nó.id existe:
        emitir { id: nó.id, class: nó.class, nodePath, bbox: nó.bbox ?? [0,0,0,0] }
    para cada filho do tipo "g" (só grupos, em ordem):
        percorrer(filho)
```

- Há uma entrada para **cada nó da árvore que tem `id`**, em ordem de percurso
  em pré-ordem, emitida **antes** de descer nos filhos.
- `nodePath` é a posição sequencial nesse percurso, contando **só nós de
  grupo** (formas, glifos e texto não consomem posição); a raiz é `0`. Vale só
  dentro desta exportação: não é estável entre exportações (o Verovio
  regenera `xml:id` a cada execução para objetos sem id na fonte) nem é um
  índice no array `children`.
- `bbox` é o `bbox` do nó (§5.1), nas mesmas unidades de viewBox (referencial
  de conteúdo, antes do `translate(origin)`). Um nó com `id` mas sem nenhum
  conteúdo desenhável (`hidden`, grupos `<g>` vazios que o Verovio emite sem
  filhos — ex. `accid` fantasma — milestones) não tem `bbox` na árvore e
  entra no índice como `[0, 0, 0, 0]`; no corpus de 10 peças / 34 páginas são
  5 653 de 39 290 entradas (tabela por classe nas notas de S04).

O pacote Dart `score_bridge` expõe o resultado em `ScenePage.elements`, ao
lado de `ScenePage.byId` (`xml:id` → nó), ambos construídos nessa passada.

O índice é sempre **por sequência**: as páginas normais (`scene.pages`) têm o
seu, e cada sequência de `alternates.json` (§2.5) tem o seu próprio, contado
do zero e independente das normais e de qualquer outra sequência — a mesma
regra de derivação, aplicada à árvore daquela página. Como os `xml:id` de
nota/compasso se repetem entre uma sequência e as páginas normais (por
construção, §2.5), **não existe** um índice único "de todo o documento": um
`xml:id` só identifica um nó dentro do escopo de uma página normal **ou**
de uma sequência específica, nunca dos dois ao mesmo tempo.


## 6. Ordem de pintura e estado herdado

O renderizador percorre a árvore em profundidade, na ordem de `children`,
mantendo uma pilha de:

- **cor corrente** (inicial: preto, `#000000` — o `color="black"` do
  `<svg class="definition-scale">`);
- **transformação** (só `rotate` altera; não há outras transformações de nó).

Nenhum outro estado é herdado. Não há clipping, máscara, gradiente ou filtro
no formato v1 (o Verovio não emite nenhum deles nas saídas do corpus).

## 7. Serialização canônica

Para que duas exportações da mesma peça sejam comparáveis:

- números usam no máximo 6 dígitos significativos, separador decimal `.` e
  não usam notação científica; inteiros são gravados sem `.0`, e `-0` vira `0`;
- cores explícitas usam `#rrggbb` minúsculo;
- `COLOR_NONE` remove o campo de cor correspondente;
- a ordem das chaves é a ordem apresentada nesta especificação;
- dicionários de glifos são ordenados por `glyphId`;
- `timemap` é omitido quando indisponível, em vez de receber um valor vazio.

## 8. Correspondência IR ↔ formato

A tabela abaixo cobre campo a campo a IR de
[`bridgegeometry.h`](../../verovio/include/vrv/bridgegeometry.h) (o arquivo se
chamava `lottiegeometry.h` até o renome mecânico de S02; os tipos abaixo já
usam os nomes atuais, `Bridge*`). Os campos derivados ou vindos de estruturas
auxiliares (`Glyph`, `FontInfo`, S03/S04 e empacotamento) estão indicados
explicitamente.

| Tipo/campo da IR | Campo JSON | Regra de correspondência |
| --- | --- | --- |
| `BridgeVec.x` | pares x em `v`/`i`/`o`, `origin`, `bbox`, `fit`, `viewBox` etc. | coordenada horizontal em unidades de viewBox ou de fonte, conforme o objeto |
| `BridgeVec.y` | pares y nos mesmos arrays/objetos | coordenada vertical; eixo Y para baixo |
| `BridgeBezier.v` | `paths[].v` | vértices em array plano de pares |
| `BridgeBezier.i` | `paths[].i` | tangentes de entrada relativas ao vértice |
| `BridgeBezier.o` | `paths[].o` | tangentes de saída relativas ao vértice |
| `BridgeBezier.closed` | `paths[].closed` | booleano de fechamento do subpath |
| `BridgeShape.kind` | `t` da forma (`p`, `r` ou `e`) | `Path` → `p`, `Rect` → `r`, `Ellipse` → `e` |
| `BridgeShape.paths` | `p.paths` | subpaths compartilhando o mesmo fill |
| `BridgeShape.center` | `r.x/y/w/h` ou `e.cx/cy` | centro convertido para canto superior esquerdo no retângulo; centro direto na elipse |
| `BridgeShape.size` | `r.w/h` ou `e.rx/ry` | tamanho direto no retângulo; metade do tamanho nos raios da elipse |
| `BridgeShape.radius` | `r.rx` | raio dos cantos; `0` quando não arredondado |
| `BridgeShape.hasFill` | presença/valor de `fill` | `false` → `"none"`; `true` + `COLOR_NONE` → ausente; `true` + cor → hex |
| `BridgeShape.fillColor` | `fill` | cor resolvida em `#rrggbb`, ou ausente para herança |
| `BridgeShape.fillOpacity` | `fillOpacity` | omitido quando `1.0` |
| `BridgeShape.hasStroke` | presença/valor de `stroke` | `false` → `"none"`; `true` + `COLOR_NONE` → ausente; `true` + cor → hex |
| `BridgeShape.strokeWidth` | `strokeWidth` | largura em unidades de viewBox; padrão IR `1.0` |
| `BridgeShape.strokeColor` | `stroke` | cor resolvida em `#rrggbb`, ou ausente para herança |
| `BridgeShape.strokeOpacity` | `strokeOpacity` | omitido quando `1.0` |
| `BridgeShape.lineCap` | `lineCap` | enum normalizado para `default`, `butt`, `round` ou `square` |
| `BridgeShape.lineJoin` | `lineJoin` | enum normalizado para `default`, `arcs`, `bevel`, `miter`, `miter-clip` ou `round` |
| `BridgeShape.dashLength` | `dash[0]` | presente somente quando maior que zero |
| `BridgeShape.gapLength` | `dash[1]` | intervalo correspondente; usa o valor resolvido da IR |
| `BridgeGlyphDef.font` | `glyphs[...].font` | família que forneceu o glifo (S03) |
| `BridgeGlyphDef.codepoint` | `glyphs[...].codepoint` | metade da chave do dicionário |
| `BridgeGlyphDef.unitsPerEm` | `glyphs[...].unitsPerEm` | metadado de `Glyph`, futuro caminho TTF |
| `BridgeGlyphDef.horizAdvX` | `glyphs[...].horizAdvX` | metadado de `Glyph`, futuro caminho TTF |
| `BridgeGlyphDef.bbox` | `glyphs[...].bbox` | `[x, y, width, height]` em escala interna do Verovio (10× os contornos), com Y para cima; não é uma bbox no sistema dos caminhos |
| `BridgeGlyphDef.paths` | `glyphs[...].paths` | contorno em unidades de fonte (S03) |
| `BridgeGlyphUse.glyphId` | `u.g` | chave no dicionário `glyphs`, `"<fonte>:<codepoint hex maiúsculo>"` (S03) |
| `BridgeGlyphUse.x` | `u.x` | posição horizontal em unidades de viewBox |
| `BridgeGlyphUse.y` | `u.y` | posição vertical em unidades de viewBox |
| `BridgeGlyphUse.sx` | `u.sx` | escala horizontal, `pointSize / unitsPerEm * DEFINITION_FACTOR` (+ `widthToHeightRatio`) |
| `BridgeGlyphUse.sy` | `u.sy` | escala vertical, `pointSize / unitsPerEm * DEFINITION_FACTOR` |
| `BridgeTextRun.text` | `t.s` | string UTF-8/JSON do run comum |
| `BridgeTextRun.origin` | `t.x`, `t.y` | âncora antes do offset de alinhamento |
| `BridgeTextRun.alignment` | `t.align` | `left`/`center`/`right`; `none` e `justify` normalizados para `left` |
| `BridgeTextRun.pointSize` | `t.size` | tamanho já convertido para unidades de viewBox |
| `BridgeTextRun.letterSpacing` | `t.letterSpacing` | espaçamento entre caracteres; `0.0` quando não usado |
| `BridgeTextRun.style` | `t.italic` | `italic`/`oblique` → `true`; `normal`/`none` → `false`, após CSS |
| `BridgeTextRun.weight` | `t.bold` | `bold` → `true`; `normal`/`none` → `false`, após CSS |
| `BridgeTextRun.color` | `t.color` | cor explícita ou ausente para `COLOR_NONE` (herança) |
| `BridgeChild.group` | item `children[]` com `t: "g"` | subgrupo; os campos do `BridgeNode` entram no mesmo objeto |
| `BridgeChild.text` | item `children[]` com `t: "t"` | run de texto comum |
| `BridgeChild.glyphUse` | item `children[]` com `t: "u"` | uso de glifo; substitui o baking de contorno (S03) |
| `BridgeChild.shape` | item `children[]` com `t: "p"`, `"r"` ou `"e"` | forma; o discriminante vem de `kind` |
| `BridgeNode.id` | `g.id` | `xml:id` primário; ausente quando vazio |
| `BridgeNode.className` | `g.class` | classes/nome do grupo |
| `BridgeNode.colorCss` | `g.color` | CSS color resolvido e normalizado; ausente quando vazio |
| `BridgeNode.hidden` | `g.hidden` | booleano de visibilidade |
| `BridgeNode.hasRotation` | presença de `g.rotate` | `false` → campo ausente; `true` → objeto presente |
| `BridgeNode.rotation` | `g.rotate.angle` | ângulo em graus |
| `BridgeNode.rotationOrigin` | `g.rotate.origin` | pivô `[x, y]` |
| `BridgeNode.hasBBox` (S04) | presença de `g.bbox` | `false` → campo ausente; `true` → array presente (regra de emissão em §5.1) |
| `BridgeNode.bbox` (S04) | `g.bbox` | união das bboxes dos filhos após transformações locais, unidades de viewBox |
| `BridgeNode.children` | `g.children` | ordem de documento; o último filho pinta por cima |
| `BridgePage.root` | `pages[].root` | raiz da árvore da página |
| `BridgePage.width` | `pages[].width` | largura lógica da página |
| `BridgePage.height` | `pages[].height` | altura lógica da página |
| `BridgePage.contentHeight` | `pages[].contentHeight` | altura usada no viewBox vertical |
| `BridgePage.baseWidth` | `pages[].baseWidth` | largura base usada por `ComputePageMetrics` |
| `BridgePage.baseHeight` | `pages[].baseHeight` | altura base usada por `ComputePageMetrics` |
| `BridgePage.userScaleX` | `pages[].userScaleX` | escala horizontal de entrada |
| `BridgePage.userScaleY` | `pages[].userScaleY` | escala vertical de entrada |
| `BridgePage.viewBoxFactor` | `pages[].viewBoxFactor` | fator de conversão para o viewBox |
| `BridgePage.originX` | `pages[].origin[0]` | translação `page-margin` em X |
| `BridgePage.originY` | `pages[].origin[1]` | translação `page-margin` em Y |
| derivado de `width/contentHeight/viewBoxFactor` | `pages[].viewBox` | `[0, 0, width * factor, contentHeight * factor]` |
| derivado de `baseWidth/baseHeight/userScale*` | `pages[].widthPx`, `heightPx` | tamanho de saída da página |
| derivado de todos os campos acima | `pages[].fit` | `scale`, `tx`, `ty` pré-computados |
| `BridgeTextRun.family` (S05) | `t.family` | face ativa (`FontInfo::GetFaceName()`) no momento do `DrawText`, com fallback para `resources->GetTextFont() + ", serif"` quando vazia (mesmo default do `font-family` da raiz `svg.definition-scale`); nunca vazia |
| empacotamento | `manifest`, `timemap` | nomes, versão, páginas e timemap embutido |
| `BridgeMeta.title` (`Toolkit::ReadBridgeMeta` via `BridgeWriter::ExtractMeta`) | `meta.title` | título como o cabeçalho mostraria com `--header auto`, independente do `--header` real (§2.3) |
| `BridgeMeta.creators` (`Doc::m_header`) | `meta.creators[].name`, `.role` | autores do `<meiHead>`, independentes de `--header` (§2.3) |
| `MIDIEventRecord`/`MIDIEventLog` (`GenerateMIDIFunctor::LogNoteEvent`/`LogPedalEvent`, via `Doc::ExportMIDI`'s optional `eventLog`) | `midi.notes[]`, `midi.pedal[]` | eventos do exportador MIDI com o `xml:id` de origem, convertidos de semínimas para ms por `BridgeWriter::WriteMidi` (§2.7) |

## 9. Compatibilidade

- `version` é inteiro. Um leitor que encontre `version` maior que o que conhece
  deve falhar com mensagem clara, nunca renderizar parcialmente.
- Chaves desconhecidas em nós/formas devem ser ignoradas pelo leitor (para
  permitir campos novos aditivos sem quebrar versões antigas).
- O schema JSON Schema draft 2020-12 que acompanha esta especificação é o
  critério mecânico de forma para o fixture e para as saídas dos passos
  seguintes.
- Um leitor que não conhece `alternates` (versões anteriores a P02a) o
  ignora: é uma propriedade/arquivo aditivo a mais, como `meta`. Um leitor
  que conhece `alternates` mas não encontra o arquivo/propriedade trata a
  peça como "sem páginas alternativas" — mostra sempre a página normal de
  destino num salto, o comportamento de antes da fase P (E03).
- Um leitor que não conhece `midi` (versões anteriores a G01) o ignora: é
  uma propriedade/arquivo aditivo a mais, como `meta`/`alternates`. Um leitor
  que conhece `midi` mas não encontra o arquivo/propriedade trata a peça como
  "sem áudio disponível" — o destaque visual (timemap) continua funcionando
  normalmente, já que os dois arquivos são independentes.
- Um leitor que não conhece `pitchpos` (versões anteriores a G04c) o ignora,
  assim como os campos novos de nó `staff` (`lines`, `ledger`, `ledgerCue`,
  `gs`) e `staff` (§5.1) e os glifos reservados (§4): tudo aditivo. Um
  leitor que conhece `pitchpos` mas não encontra o arquivo/propriedade trata
  a peça como "sem nota fantasma disponível" — nada mais muda.
- Um leitor que não conhece `dur`/`dots` em `pitchpos` (versões anteriores a
  G08a) os ignora, assim como os glifos reservados novos (§4): tudo aditivo.
  Um leitor que conhece a §11 mas encontra um `pitchpos.json` sem `dur`, ou um
  dicionário sem as pausas reservadas, esconde as notas normalmente e **não
  desenha a pausa substituta** (regra 4 e 5).
- Um leitor que não conhece `music` (versões anteriores a M02) o ignora: é uma
  propriedade/arquivo aditivo a mais, como `midi`/`pitchpos`. Um leitor que
  conhece `music` mas não encontra o arquivo/propriedade trata a peça como "sem
  dados musicais estruturados" — o desenho e os outros arquivos não mudam.

## 10. Nota fantasma (normativo)

A **nota fantasma** mostra, na pauta, onde uma tecla MIDI qualquer ficaria
escrita: na **coluna** (x) de um evento esperado, na **altura** (y) da nota
tocada, na clave e no contexto vigentes ali (G03,
`docs/plano/G03-visao-geral-nota-fantasma.md`). Tudo o que é musical vem do
Verovio (`pitchpos.json`, §2.8; nó `staff`, §5.1); o host só faz a conta
abaixo. A implementação de referência é `compare/scripts/ghost_ref.py` e os
vetores de teste são `docs/formato/fantasma/vetores.json` (G04d, +6 casos
cross-staff em G06).

**Entradas.** `E`: os ids **notados** das notas/pausas esperadas no instante
(o host converte os ids expandidos do timemap por `sceneIdOf`, §2.4, e decide
quais são os esperados — inclusive numa pausa, `restsOn`); `K`: as teclas
erradas (MIDI 0-127). **Saída:** uma fantasma por tecla de `K`.

**Notação.** Letra `pname` = 1…7 (c, d, e, f, g, a, b); `sem = [0, 2, 4, 5,
7, 9, 11]` (semitons da letra natural); `alt` ∈ {−1, 0, +1}; altura natural
`midi(pname, o) = 12·(o + 1) + sem[pname − 1]`; com alteração,
`midi(pname, o, alt) = midi(pname, o) + alt`. `n`, `topY`, `unit` = de
`staff.lines`.

**Unidade vertical.** O Verovio posiciona toda nota por um inteiro `loc`
(0 = linha de baixo, +1 por meio-espaço):

```text
loc = (o − 4)·7 + (pname − 1) + co            // co = clefLocOffset (§2.8)
y   = topY + (2·(n − 1) − loc)·unit           // eixo y da cena, para baixo
```

**Algoritmo**, para cada tecla `k`, nesta ordem:

1. **Alvo (pauta e coluna, G06).** Cada elemento de `E` é candidato, com
   pauta `S` (o nó de `staff` em `staff`, §5.1, ou o ancestral) e **altura de
   referência** `ref`: nota → `midi(pn, o, alt) + sh`; pausa → o som da linha
   do meio da pauta, `midi(pname', o') + sh` da letra natural de
   `loc = n − 1` (`pos = loc − co + 28`, `o' = ⌊pos / 7⌋`, `pname' = pos mod
   7 + 1`). Para cada pauta distinta em `E`, calcula-se o `loc` da tecla
   nessa pauta (passos 2-4 com o contexto da pauta — item abaixo) e as
   **linhas suplementares brutas** (antes de 8va, passo 5). A fantasma vai
   para a pauta com **menos suplementares**. Desempates, nesta ordem: menor
   `|k − ref|` (do candidato mais próximo daquela pauta); maior `ref` (o de
   cima). Dentro da pauta escolhida, o alvo é o candidato mais próximo em
   `|k − ref|` (empate: o de cima) — a coluna (x) é a dele. Se um instante
   tem notas e pausas, valem todas como candidatos. Com pauta única em `E`
   (ou em empate total), isto equivale à regra antiga: alvo global por
   proximidade.

   **Contexto da pauta (G06).** `co`/`sh`/`key`/`acc` (e `n`/`topY`/`unit` da
   geometria) são os do evento daquela pauta em `E` mais próximo de `k` —
   mesma coluna, mesma pauta: `key`/`acc`/`co` coincidem; `sh` pode divergir
   entre vozes, e vale o do candidato mais próximo. Grafia (passo 3) e
   acidente (passo 6) usam esse contexto.
2. **Altura escrita.** `w = k − sh` (do alvo). `wE` = a altura **escrita**
   do alvo: `ref − sh` (nota: `midi(pn, o, alt)`; pausa: a natural da linha
   do meio).
3. **Grafia.** Se `w == wE` (a tecla é a própria nota esperada — não é uma
   tecla errada, mas a regra fica total): a grafia do próprio alvo (`pn`,
   `o`, `alt`; numa pausa não ocorre). Senão, `w mod 12` ∈ {0, 2, 4, 5, 7, 9,
   11} (tecla branca): a letra natural (`alt = 0`; nunca Mi♯/Dó♭). Senão
   (tecla preta): sustenido se a
   armadura do alvo (`key`) tem alguma alteração positiva e nenhuma
   negativa; bemol se tem alguma negativa e nenhuma positiva; sem armadura
   (ou mista): sustenido se `w > wE`, bemol se `w < wE`. Sustenido: a letra
   natural de `w − 1`, `alt = +1`; bemol: a de `w + 1`, `alt = −1`. Saem
   `pname`, `o` (a oitava da letra natural escolhida) e `alt`.
4. **`loc`** pela fórmula acima, com o `co` do alvo.
5. **Alcance.** Linhas suplementares: acima, `⌊(loc − 2·(n − 1)) / 2⌋` se
   positivo; abaixo, `⌊−loc / 2⌋` se positivo (senão 0). O oráculo (G04d)
   confere esta contagem **antes** do deslocamento, contra o Verovio; o
   deslocamento é convenção do plano. Enquanto passar de **4**, e com
   `m < 2`: `loc −= 7` (acima) ou `loc += 7` (abaixo) e `m += 1`. (G06: entre
   pautas, o passo 1 já escolheu a de menos suplementares — o deslocamento só
   acontece se nem a melhor cabe, isto é, no extremo do sistema; com pauta
   única em `E`, vale a regra integral.) `m` = 0: sem
   marcador; 1: 8va (E511, acima) / 8vb (E512, abaixo); 2: 15ma (E515) /
   15mb (E516). Se ainda passar de 4 com `m = 2` (teclas a mais de duas
   oitavas além de 4 linhas, ex. lá 0 na clave de Sol), a fantasma fica
   **presa em 4 linhas** (`loc = 2·(n − 1) + 8` acima, `−8` abaixo) —
   limitação aceita, a posição deixa de representar a altura.
6. **Acidente.** Em vigor para a letra+oitava **antes do deslocamento de
   oitava**: `acc["<letra><o>"]` do alvo se existir, senão `key["<letra>"]`
   do alvo, senão 0. Se `alt` (passo 3) for diferente, desenha-se o
   acidente: `alt = +1` E262, `−1` E260, `0` E261 (bequadro).
7. **Cabeça e x.** Cabeça: glifo E0A4 (preta, sempre), com `sx`/`sy` da
   cabeça do alvo (a cabeça `u` dentro do nó `notehead` do alvo — cue/grace
   herdam a escala) ou, se o alvo é uma pausa, `staff.gs`. `x` = `x` dessa
   cabeça (ou do glifo da pausa). **Colisão:** enquanto o retângulo da
   fantasma (`[x, x + larg]`, `larg` = largura do contorno de E0A4 × `sx`;
   `loc`) tem `|loc − loc'| ≤ 1` **e** se sobrepõe horizontalmente a uma
   cabeça real de nota de `E` **na mesma pauta** (`loc'` = `loc` dessa nota
   em `pitchpos`, `x'` = `x` da cabeça dela), ou a uma fantasma já posta
   (mesma pauta, teclas processadas em ordem crescente), faz `x += larg`.
   Pausas não colidem.
8. **Peças.** Todas em unidades de viewBox, no referencial de conteúdo
   (§5.1 `bbox`):
   - cabeça: `{g: "<fonte>:E0A4", x, y, sx, sy}`;
   - acidente (se houver): glifo à esquerda da cabeça, na mesma linha de base
     `y`, com `xAcc = x − 0,5·unit − largura do contorno do acidente × sx`. A
     folga de `0,5·unit` é a que o Verovio deixa entre um acidente e a cabeça
     (G04d, mediana de 1 085 acidentes do corpus: 0,4996·unit, a mesma razão
     com `--unit` 60, 90 e 120);
   - linhas suplementares (uma por posição, de 1 até a contagem do passo 5,
     em `loc = 2·(n − 1) + 2j` acima ou `−2j` abaixo, no `loc` **já
     deslocado**): segmento horizontal em `y` de `x − ext` a `x + larg +
     ext`, com a espessura e a extensão `ext` de `staff.ledger` (ou
     `staff.ledgerCue` se a cabeça do alvo tem `sx` menor que `staff.gs[0]`
     e a pauta traz `ledgerCue`);
   - marcador de oitava (se `m > 0`): glifo E511/E512/E515/E516 centrado na
     cabeça (`x + larg/2 − largura do contorno × sx / 2`); linha de base
     `y_extremo − 3·unit` acima ou `y_extremo + 5·unit` abaixo, com
     `y_extremo` = y da linha suplementar mais distante (ou da cabeça, se não
     há). Convenção visual da v1: o Verovio não desenha 8va de fantasma, então
     não há oráculo; o host pode ajustar.

O host escolhe cor, fade e duração (G03, D-FANT-DURACAO); nada disso está no
formato.

**Limitações da v1** (G03): o acidente da fantasma pode colidir com
acidentes reais da coluna (a fantasma não entra no empilhamento do Verovio);
acidente trazido por ligadura através da barra de compasso não conta;
percussão, tablatura e notação mensural ficam fora (não têm `loc` de
altura); mudança de armadura no meio do compasso não zera `acc`.

### 10.1 Exemplos trabalhados (Erik Satie, Gymnopédie nº 1)

Todos com `docs/formato/fantasma/satie.vsb` (1ª pauta da página 1: `topY` 808,
`unit` 90, `n` 5, `co` −2, `ledger` [22, 48], `gs` [0,72, 0,72]; armadura de
ré maior: `key` = {c: 1, f: 1}). O acorde esperado é si3 `orw55dt` (`loc` −3,
`y` 1798), ré4 `q1t6l0ej` (`loc` −1, `y` 1618) e fá#4 `r1c5f34m` (`loc` 1,
`y` 1438), as três cabeças em `x` = 2629; a largura de E0A4 é
314 × 0,72 = 226,08. Os números batem com `vetores.json`.

**Ex. 1 — lá♯4 (tecla 70).** Alvo: o fá#4 (`ref` 66, distância 4; as outras
são 8 e 11). `w = 70 − 0`; tecla preta e a armadura só tem sustenidos →
sustenido: lá4 com `alt = +1`. `loc = (4 − 4)·7 + 5 − 2 = 3`; `y = 808 +
(2·4 − 3)·90 = 1258`. Em vigor para `a4`: `acc` não tem, `key` não tem →
0 ≠ +1 → desenha ♯ (E262), à esquerda da cabeça: `xAcc = 2629 − 0,5·90 −
197 × 0,72 = 2442,16`. Colisão: as cabeças reais estão em `loc` −3, −1, 1,
todas a mais de 1 de `loc` 3 → `x` fica 2629. Sem linhas suplementares
(`loc` 3 está dentro da pauta), sem marcador.

**Ex. 2 — dó♯4 (tecla 61), com colisão.** Alvo: o ré4 (`ref` 62, distância
1). Sustenido (armadura): dó4, `alt = +1`; `loc = 0 + 0 − 2 = −2`; `y = 808 +
(8 + 2)·90 = 1708`. Em vigor para `c4`: `key.c = +1` → igual → **sem
acidente**. `|−2 − (−3)| = 1` (si3) e `|−2 − (−1)| = 1` (ré4), com as
cabeças reais sobrepostas em `x` → `x += 226,08` → 2855,08 (sem mais
sobreposição: a borda direita das reais é 2855,08, e o teste é
estritamente menor). Uma linha suplementar abaixo (`⌊2/2⌋ = 1`) em `y` 1708,
de `x − 48` = 2807,08 a `x + 226,08 + 48` = 3129,16, espessura 22.

**Ex. 3 — mi7 (tecla 100), com 8va.** Alvo: o fá#4. Tecla branca: mi7;
`loc = (7 − 4)·7 + 2 − 2 = 21` → `⌊(21 − 8)/2⌋ = 6` linhas > 4 → `loc = 14`,
`m = 1` (8va, E511) → `⌊(14 − 8)/2⌋ = 3` linhas, em `loc` 10, 12, 14 →
`y` 628, 448, 268; a cabeça em `y = 808 + (8 − 14)·90 = 268`. Marcador:
E511 centrado (`x + 113,04 − 657 × 0,72 / 2 = 2505,52`), com linha de base
em `268 − 3·90 = −2`.

**Ex. 4 — lá2 (tecla 45) com as duas pautas em `E`, sem 8vb (G06).**
Pauta do baixo na mesma página: `topY` 3031, `unit` 90, `n` 5, `co` 10,
`ledger` [22, 48]; o sol2 `yw90mxt` (`loc` 0) tem a cabeça em `x` = 1856.
Na clave de sol, lá2 dá `loc = (2 − 4)·7 + 5 − 2 = −11` (5 suplementares);
na clave de fá, `loc = −14 + 5 + 10 = 1` (0) → a fantasma vai para o baixo.
`y = 3031 + (8 − 1)·90 = 3661`; tecla branca, sem acidente. Colisão:
`|1 − 0| = 1` com o sol2 real, sobreposto em `x` → `x += 226,08` → 2082,08.
Pela regra antiga (só a clave de sol em `E`), a mesma tecla dava `loc` −11
→ −4 com 8vb.

## 11. Nota escondida e pausa substituta (normativo)

A **nota escondida** é a da trilha do decorar: o host apaga da partitura as
notas de uma **coluna** — todas as notas de **uma pauta de desenho** que
começam no mesmo instante — e desenha no lugar **uma pausa**, de outra cor,
com a figura da nota mais curta da coluna (G07,
`docs/plano/G07-visao-geral-nota-escondida.md`). Tudo o que é musical vem do
Verovio (`pitchpos.json`, §2.8; cena, §5; nó `staff`, §5.1; glifos
reservados, §4); o host só faz a conta abaixo. Nada disso muda o desenho:
esconder e mostrar é trocar a cor ou não pintar, sem recompilar a página, e
vale igual nas páginas normais e nas alternativas (§2.5), porque só usa o que
está na própria página.

**Quais colunas somem e quando é decisão do host**, assim como a cor da
pausa, o piscar e a revelação ao errar; nada disso está no formato. O que
fica na tela é: pauta, clave, armadura, fórmula de compasso, barras de
compasso, pausas de verdade, a letra (`verse`), ligaduras de expressão e de
prolongamento, dedilhado e as notas que não foram escondidas.

**Entradas.** `C`: os ids **notados** (§2.8) das notas da coluna, todas na
mesma pauta de desenho `S` (o nó `staff` em `staff`, §5.1, ou o ancestral).
`H`: o conjunto de **todas** as notas escondidas no momento (as de `C` e as
de outras colunas já escondidas). Do `pitchpos.json`, cada nota de `C` traz
`loc`, `dur` e `dots`; de `S`, `n`, `topY`, `unit` (`lines`) e `gs`. Um id
expandido do timemap (`-rend<N>`) vira o id da cena por `sceneIdOf` (§2.4).

**1. Esconder a nota.** Para cada nota de `C` (e para a sua continuação
ligada, ver abaixo), o host troca a cor do nó `note` por transparente (§6,
cor herdada): cabeça, haste própria, colchete, acidente, articulação e
pontos de aumento são descendentes do nó e vão junto. Três casos:
  - **Continuação de nota ligada** é outra `note` na cena: o host a esconde
    pelo id (`midi.json`, `tied`, §2.7).
  - **Acorde.** A haste, o colchete, os pontos e as articulações de um acorde
    são filhos do nó `chord`, **não** de cada `note`. O host esconde o nó
    `chord` inteiro quando **toda** `note` descendente dele está em `H`. Com
    uma coluna (que cobre o acorde todo) isso é sempre o caso; só um acorde
    cross-staff dividido entre duas pautas pode ficar pela metade, e então a
    haste fica (limitação da v1).
  - **Exceções.** Nós que a coluna não leva consigo, como `verse` (filho da
    nota), continuam visíveis: o host os pinta com a cor normal, não com a
    herdada (`kOverrideExemptClasses`, no `score_bridge`).

**2. Barra de ligação.** As formas **filhas diretas** de um nó `beam` (as
barras propriamente ditas) deixam de ser pintadas quando **toda** `note`
descendente desse `beam` está em `H`. Barras aninhadas: a regra vale para cada
`beam` com as suas próprias descendentes. O host **não** esconde o nó `beam`
(trocar a cor dele esconderia também as notas visíveis, descendentes dele);
só as formas filhas diretas. Medido em G08c (3 115 `beam` em 36 peças): todo
`beam` tem ao menos uma forma filha direta e uma `note` descendente; nenhuma
barra aninhada em outra; 2 entre pautas (cross-staff, na Clair de Lune: a regra
vale como está, só some quando as notas das duas pautas somem); 1 615 têm um
nó `chord` dentro (as notas dele contam como descendentes); nenhum `bTrem`/`fTrem`
na amostra. O nó `beamSpan` (barra de ligação que atravessa compassos ou
quebra de sistema: 47 casos, em 2 peças, nenhum nos hinos) **não é** um `beam`:
é um nó próprio, sem nota descendente, e a regra 2 não o alcança — a barra dele
continua desenhada (limitação da v1; ao esconder um compasso inteiro, a regra 8 a
resolve: o `beamSpan` some quando todos os compassos que ele toca estão escondidos).

**3. Linhas suplementares.** Os nós `ledgerLines` (classes `ledgerLines above`,
`ledgerLines below` e as variantes cue) são filhos de `staff`, sem `id`; cada
**traço** é uma forma `p` própria. Para um traço em `y_t` (a ordenada do
segmento, no referencial do §5.1) e de `x` em `[a, b]`:
  - **ordem `k`**: acima da pauta (`y_t < topY`), `k = (topY − y_t) / (2·unit)`;
    abaixo (`y_t > topY + 2·(n − 1)·unit`), `k = (y_t − (topY + 2·(n − 1)·unit))
    / (2·unit)`; arredonda-se `k` ao inteiro mais próximo (`k ≥ 1`);
  - **extensão da cabeça** de uma nota: `[xl, xr]` = o intervalo horizontal
    dos vértices (`v`) do contorno de cada glifo `u` do nó `notehead` da nota
    (§4, §5.3), com `x` e `sx` da instância — a mesma medida de largura da
    §10, passo 7;
  - o traço **pertence** a uma nota quando a nota está na **mesma pauta de
    desenho** (§5.1, `staff`), `[xl, xr] ⊆ [a − 1, b + 1]` (1 unidade de
    viewBox de folga) e o `loc` dela alcança a linha: acima, `loc ≥ 2·(n −
    1) + 2·k`; abaixo, `loc ≤ −2·k`;
  - o traço **pertence também a uma pausa** (nó `rest` ou `mRest` da mesma
    pauta de desenho) cujo glifo `u` ele cobre do mesmo jeito (`[xl, xr]` = o
    contorno do glifo × `sx`) e cujo `loc` = `2·(n − 1) − (y − topY)/unit`
    alcança a linha. O Verovio desenha traço para uma pausa deslocada (posição
    explícita, ou deslocada por camada), e o dele pode **fundir-se** com o de
    uma nota da outra camada. O host nunca esconde uma pausa de verdade, então
    **um traço que tem uma pausa entre as donas fica**;
  - o traço **deixa de ser pintado** quando toda dona dele é uma nota e toda
    nota a que pertence está em `H`. Um traço sem nenhuma dona (não deve
    existir) continua visível. Os traços de uma coluna visível não são
    afetados.

*Medido em G08c (D-SUM-NATIVO: não é preciso dado novo na cena).* Em 7 381
traços de 36 peças (corpus + hinos; páginas normais e alternativas), com as
donas acima: **nenhum traço sem dona e nenhum traço com donas de colunas
diferentes**. As donas de um traço são sempre da mesma coluna (mesma pauta de
desenho e mesmo instante, com uma ressalva: as notas de um acorde arpejado
têm instantes ligeiramente diferentes no timemap — o `arpeg` espalha os
`on` de 0,02 a 0,04 de semínima — mas são um acorde só na cena, e o traço de um
arpejo some quando a **última** nota dele some). 108 traços têm uma pausa
entre as donas (4 só dela, 104 fundidos com o de uma nota, em 4 peças): sem a
pausa como dona, a regra apagaria um traço de que a pausa visível precisa.

**4. Figura.** `dur` e `dots` da nota **mais curta** da coluna: o maior `dur`
entre as notas de `C` (figura mais curta) e, no empate, o **menor** `dots`
(a sem ponto é mais curta que a pontuada de mesmo `dur`). É a figura **escrita**
(§2.8): quiáltera, ligadura e fermata não a mudam. Se alguma nota de `C` não
tem `dur`, ou o `dur` fica fora do que a regra 5 cobre, a coluna é escondida
**sem pausa substituta**.

**5. Glifo da pausa.** Chave do dicionário `"<fonte>:<codepoint>"` (a fonte
é a dos glifos reservados, §4):

| `dur` | 1 | 2 | 4 | 8 | 16 | 32 | 64 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| codepoint | `E4E3` | `E4E4` | `E4E5` | `E4E6` | `E4E7` | `E4E8` | `E4E9` |

(semibreve, mínima, semínima, colcheia, semicolcheia, fusa, semifusa). Fora
dessa faixa (`dur` ≥ 128) não há pausa substituta. Um `.vsb` anterior a G08b,
sem esses glifos no dicionário, esconde a coluna do mesmo jeito, sem pausa.

**6. Posição.** Em unidades de viewBox, no referencial de conteúdo (§5.1):

```text
x    = menor x de cabeça (u dentro de notehead) entre as notas de C
loc  = n − 1                                  // linha do meio da pauta
se dur ≤ 2 (mínima ou semibreve) e loc ímpar:  loc −= 1
se dur == 1 e n > 1:                           loc += 2
y    = topY + (2·(n − 1) − loc)·unit
sx = gs[0], sy = gs[1]
```

(`dur ≤ 2` é "mais longa que a semínima"; com `n = 5` o `loc` do meio, 4, é par e
a condição nunca dispara.) **Pauta que não tem 5 linhas** (`n ≠ 5`) fica sem
pausa substituta (limitações, abaixo).

São as mesmas condições de `calcalignmentpitchposfunctor.cpp` para a posição
automática de uma pausa (a linha do meio; a de duração maior que a semínima
cai numa linha; a semibreve pendura-se uma linha acima), **sem** o ajuste por
camada (`GetOptimalLayerLocation`): a pausa substituta é uma só por pauta. A
pausa é um `u` com o glifo da regra 5, `{g, x, y, sx, sy}`, pintado na cor do
host. O `x` é o da cabeça da coluna **por definição**: não há oráculo para ele
(trocar nota por pausa muda o espaçamento que o Verovio calcula). A pausa é de
largura parecida com a da cabeça (226 unidades com `gs` 0,72): semínima 219,
colcheia 198, semicolcheia 233, semibreve e mínima 216; só as de fusa (286) e
semifusa (344) ultrapassam a cabeça, para a direita.

*Posição, glifo e pontos são os do Verovio* (G08c, oráculo): em 855 pausas de
verdade (pauta de uma camada, fora de barra, sem posição explícita) e em 840
colunas trocadas por uma pausa dentro do próprio Verovio, **0 divergências** de
glifo, `y`, escala e pontos, com tolerância de 0,5 unidade de viewBox
(`compare/scripts/hide_oracle.py`). Ficam fora do oráculo, por serem posição que
o Verovio muda por outro motivo: pausa com `@loc`/`@ploc` explícito, pauta de
mais de uma camada (`GetOptimalLayerLocation`), pausa dentro de barra (altura
pela vizinhança) e pauta que recebe nota cross-staff no mesmo compasso (a pausa
desvia dela); nesses casos a pausa substituta fica na posição padrão da pauta,
que pode encostar numa nota visível (limitação da v1).

*Pontos de aumento* (`dots > 0`), na regra de `View::DrawDots` e
`CalcDotsFunctor::VisitRest`: o Verovio desenha cada ponto como um círculo (não
como glifo; `View::DrawDot`), de raio `r = max(2·unit / 5, 2)`. Para a pausa
substituta, com `ux = unit` e `loc` o da pausa acima:

```text
locDot = loc;  se locDot é par: locDot += 1
se dur == 32 ou 64: locDot += 2             // a pausa de fusa/semifusa é mais alta
xRel   = (dur > 2) ? ⌊largura do glifo da pausa⌋ : ⌊2,5·unit⌋
         // largura = bbox[2] / 10 × sx (§4), truncada: o Verovio calcula em inteiros
x0     = x + xRel + unit
yDot   = topY + (2·(n − 1) − locDot)·unit
ponto j (j = 0 … dots − 1): elipse { cx = x0 + j·1,5·unit, cy = yDot, rx = ry = r }
```

Cada ponto é um círculo `fill` na cor da pausa, sem contorno. A conta foi
conferida contra o Verovio (oráculo, G08c) com pausas de todas as figuras de
semibreve a semifusa, com 0, 1 e 2 pontos (`corpus/sumico/s01-pausas-pontuadas.mei`);
o único acerto em relação ao texto de G08a foi o truncamento da largura.

**7. Uma pausa por (pauta de desenho, instante).** Se o host esconde colunas
de duas pautas no mesmo instante, desenha duas pausas, uma em cada pauta de
desenho (cross-staff: `staff`, §5.1). Mais de uma coluna na **mesma** pauta e
no mesmo instante não existe por definição (a coluna é o conjunto do
instante).

**O que o host não deve fazer.**
  - Deduzir a figura do timemap: erra em quiáltera, em nota ligada e em
    fermata (use `dur`/`dots`, §2.8).
  - Esconder `verse`: a letra fica.
  - Apagar o nó `beam` inteiro: levaria as notas visíveis dele junto (regra 2:
    só as formas filhas diretas).
  - Deduzir a pauta de desenho pela posição vertical: ela está em `staff`
    (§5.1).
  - Interpretar CSS ou nomes de classe além dos já citados (§1: o estilo está
    resolvido no arquivo).

**Limitações da v1.** A pausa substituta pode ficar apertada contra uma nota
visível vizinha (o espaçamento foi calculado para a nota); ligadura de
prolongamento ou de expressão que começa ou termina numa nota escondida
continua desenhada; dedilhado (`fing`) continua desenhado; apojaturas e
ornamentos não somem; `beamSpan` não some (regra 2); o traço fundido com o de uma
pausa deslocada fica inteiro, mais largo do que a pausa precisa; pauta que não
tem 5 linhas, tablatura, percussão e notação mensural ficam sem pausa
substituta.

### 11.1 Exemplos trabalhados

Os dois vêm do hino 010, *O Senhor está aqui* (`corpus/sumico/h010.musicxml`;
página 0; `docs/formato/sumico/h010.vsb`): uma pauta de duas vozes em camadas
separadas, com letra, de `topY` 1106, `unit` 90, `n` 5 e `gs` 0,72 — o caso dos
hinos do `zywny`, que o Satie (§10.1) não cobre. Os números saem de
`compare/scripts/hide_ref.py` e estão em `docs/formato/sumico/vetores.json`
(`c01-duas-vozes`, `c06-pontuada`, mais nove casos), com um PNG de evidência por
caso em `compare/out/g08c/` (git-ignorado; `g08c-make-vectors.py` o refaz). O
oráculo do Verovio (`hide_oracle.py`) concorda com os dois em glifo, `y`,
escala e pontos.

**Ex. 1 — duas vozes, figuras diferentes, linha suplementar.** O instante 2 da
pauta `c1k2xsnz`: soprano `r10709ff` (semínima, `loc` 3) e, em acorde `yy2zfkq`,
alto `z1oagi0k` (mínima, `loc` 0) e tenor `x1848jna` (mínima, `loc` −2); todas
com cabeça em `x` 3446. `C = H =` as três notas.

  - regra 1: as três notas e o acorde `yy2zfkq` (as duas notas dele estão em
    `H`) somem, com haste, colchete e pontos; a letra fica;
  - regra 2: nenhuma barra (`r10709ff` é uma nota solta): `beams` vazio;
  - regra 3: o tenor, em `loc` −2, pede 1 linha abaixo; o traço
    `["c1k2xsnz", "below", 1, 3398, 3720]` (cabeça 3446-3672 ± 48 de extensão)
    só tem essa coluna como dona e some; o traço do instante 0 (x 1678-2000),
    vizinho, fica;
  - regra 4: as figuras são (4, 0), (2, 0) e (2, 0): a mais curta é a semínima;
  - regra 5: `dur` 4 -> `Leipzig:E4E5`;
  - regra 6: `loc` = 5 − 1 = 4 (par; `dur` 4 não pede ajuste); `y` = 1106 +
    (8 − 4)·90 = **1466**; `x` = **3446**; `sx` = `sy` = 0,72.

**Ex. 2 — figura pontuada.** O instante 12 da pauta `wuhbofp` (topo 3519): `g1qqc06o`
(mínima, `loc` 0) e `y4ih5in` (semínima pontuada, `loc` 4), `x` 12798.

  - regra 4: a mais curta é a semínima pontuada, (4, 1);
  - regra 5: `Leipzig:E4E5`; regra 6: `loc` 4, `y` = 3519 + 4·90 = **3879**;
  - pontos: `loc` 4 é par -> `locDot` 5; `dur` 4 não sobe; `xRel` = ⌊219,6⌋ =
    219 (largura de `E4E5` × 0,72); `x0` = 12798 + 219 + 90 = **13107**; `yDot` =
    3519 + (8 − 5)·90 = **3789**; raio 2·90/5 = 36: um círculo `{cx: 13107,
    cy: 3789, rx: 36, ry: 36}`.

Os outros nove casos de `vetores.json` cobrem barra com 1 de 2 e 2 de 2 notas
escondidas, semibreve (`loc` 6), empate de figura (a sem ponto vence), tercina,
nota ligada (cabeça + continuação escondida pelo id), coluna cross-staff (pausa
na pauta de desenho) e página alternativa.

### 11.2 Esconder um compasso inteiro: a pausa de compasso substituta (regra 8)

O decorar esconde uma **coluna** (regras 1 a 7). O aprendizado esconde um
**compasso inteiro, nas duas pautas** e quer ver no lugar **uma única pausa de
compasso por pauta**, a semibreve centrada que o Verovio desenha para `<mRest/>`,
não uma fileira de pausas pequenas que entregaria o ritmo. Compassos escondidos
vizinhos têm cada um a sua. As regras 1 a 3 valem como estão; o que muda é o
conjunto `H` (todas as notas do compasso) e o que mais some com ele.

**Entradas.** `M`: o conjunto de ids de nó `measure` escondidos por inteiro (os
`measureOn` do timemap, §2.4, são os mesmos ids; `sceneIdOf` para `-rend<N>`).
Tudo o mais vem da cena: as **notas do compasso** são os nós `note`
descendentes do nó `measure` (não é preciso o `pitchpos.json`); a **pauta de
desenho** de uma nota é a da regra 1 (`staff` do nó, §5.1, ou o ancestral).

**8.1 O que some.** Para cada pauta de desenho `S` do compasso:
  - `S` **tem alguma nota**: todas as notas dela entram em `H` (regras 1 a 3 as
    levam com acorde, barra e linhas suplementares) e **as pausas de verdade**
    (nós `rest`, não `mRest`) **também somem**, inclusive os pontos delas e o
    traço de linha suplementar de uma pausa deslocada (a regra 3 passa a contar
    as pausas escondidas como donas escondidas). Entra a pausa de compasso (8.3).
  - `S` **não tem nenhuma nota** (só `rest` ou só `mRest`): o host **não faz
    nada** nessa pauta; a pausa que existe já é o que o aluno veria.
  - **Tercina** (nó `tuplet`): some o nó inteiro quando toda `note` e toda
    `rest` descendente dele está escondida (leva o colchete e o número, nós
    `tupletBracket`/`tupletNum`). O host o trata como a nota: cor transparente,
    com a mesma exceção da regra 1 (`verse` fica).
  - **Controles ancorados** (nós `tie`, `slur`, `phrase`, `arpeg` e `beamSpan`,
    filhos do `measure` ou, quando cruzam a quebra de sistema, do `system`, sem
    `id`): o **dono** é o conjunto de compassos que o controle toca. Para um
    controle de caixa `[x0, _, x1, _]`, tocar um compasso `m` do mesmo sistema é
    `min(x1, m.fim) − max(x0, m.início) > 1` (1 unidade de folga), onde
    `[m.início, m.fim]` é o primeiro traço de linha de pauta do compasso (§5.1,
    `p` filho do `staff`). O controle **some** quando todos os compassos que toca
    estão em `M`; **fica** se toca algum compasso visível (a ligadura de
    prolongamento que sai do compasso escondido para o seguinte). Sem `id`, ele é
    identificado por `classe@x0,y0,x1,y1` (caixa, 1 casa).

| O que mora no compasso | Nós no corpus¹ | O que acontece |
| --- | --- | --- |
| cabeça, haste, colchete, acidente, ponto, articulação | 21 738 notas | **somem** (regra 1) |
| barra de ligação (`beam`) | 3 400 | **some** (regra 2) |
| linha suplementar (`ledgerLines`) | 2 286 | **some** (regra 3; o traço de uma pausa que some conta) |
| pausa de verdade (`rest`) em pauta que tem nota | 732 pautas de compasso | **some**, entra a pausa de compasso |
| pausa de verdade em pauta sem nota | 35 pautas de compasso | **fica** |
| tercina (`tuplet`, `tupletNum`, `tupletBracket`) | 90, 64, 4 | **some** quando todo o conteúdo some |
| ligadura de prolongamento (`tie`) | 1 282 | **some** se toca só compassos escondidos (874); **fica** se cruza para um visível (408) |
| ligadura de expressão (`slur`) e frase (`phrase`) | 555 e 12 | idem (496 e 3 somem; 59 e 9 cruzam e ficam) |
| arpejo (`arpeg`), barra entre compassos (`beamSpan`) | 8, 47 | **somem** (o `beamSpan` deixa de ser limitação da regra 2) |
| dinâmica, andamento, cifra, texto de direção, pedal, ottava, trinado, fermata, dedilhado, número do compasso | 184, 156, 168, 83, 656, 10, 16, 16, 8, 276 | **ficam** (não revelam altura nem ritmo; o aluno vê o contexto) |
| letra (`verse`/`syl`), clave, armadura, fórmula, barra de compasso, `space`/`mSpace` | — | **ficam** |

¹ 70 partituras (34 do G08c, 35 do aprendizado e `g11-compassos-especiais.mei`), páginas normais e alternativas
(`compare/scripts/g11-sweep.py`). Escondendo **todos** os compassos de cada
página, sobram desenhados só os nós da coluna "fica": **0 vazamentos** de nota,
haste, barra, tercina ou ligadura (124 páginas, 1 517 compassos).

**8.2 Pausa de compasso substituta.** Por pauta de desenho `S` que tem nota no
compasso `m`, **uma** pausa, um `u` `{g, x, y, sx, sy}` pintado na cor do host:

```text
g    = "<fonte>:E4E3"                        // a semibreve, qualquer fórmula de compasso
cx   = m.inner[0] + ⌊(m.inner[1] − m.inner[0]) / 2⌋     // divisão inteira
x    = cx − ⌊largura de E4E3 × sx⌋ / 2                   // largura = bbox[2] / 10 × sx (§4), truncada; / 2 inteiro
loc  = n − 1;  se loc ímpar: loc −= 1;  se n > 1: loc += 2   // a mesma conta da semibreve (regra 6, dur = 1)
y    = topY + (2·(n − 1) − loc)·unit
sx, sy = gs                                 // do nó staff (§5.1)
```

(`topY`, `unit`, `n` do `lines` e `gs` do nó `staff`.) Com `n = 5`, `loc` = 6 e
`y = topY + 2·unit`. A pausa de compasso **não leva pontos** e não depende do
`dur` de nenhuma nota. As contas são as do Verovio (`View::DrawMRest`,
`Measure::GetInnerCenterX`, `CalcAlignmentPitchPosFunctor`). **Sem pausa de
compasso substituta** (as notas somem do mesmo jeito): `.vsb` sem `inner` (anterior
a G11); compasso de **2 semibreves ou mais** (o Verovio desenha a pausa de breve,
`E4E2`, que não é glifo reservado; o compasso dura `qlen ≥ 8` semínimas, de
`measureOn` consecutivos no timemap, §2.4; o último compasso até o fim do
timemap); pauta com `n ≠ 5`; glifo `E4E3` ausente (`.vsb` anterior a G08b).
**Anacruse e compasso incompleto:** o Verovio desenha a mesma semibreve
centrada, e a regra vale igual (medido: 1 semínima, mesma pausa); decidir se se
esconde uma anacruse é do host.

**8.3 Compassos vizinhos, página e cross-staff.** Dois compassos escondidos
lado a lado dão uma pausa de compasso **cada um**, sem pausa dupla (cada uma
centrada no `inner` do seu compasso). Vale nas páginas normais e nas
alternativas (§2.5). Cross-staff: a pausa vai para a pauta de **desenho** que
tem notas; a pauta de origem, se ficou só com pausas, fica como está.

**8.4 Provado contra o Verovio** (`compare/scripts/hide_oracle.py --measures`, G11):
  - *sem rodar o Verovio de novo*: toda `mRest` de verdade do corpus (pauta de
    uma camada): 11 conferidas, 0 divergências de glifo, `x`, `y` e escala;
  - *rodando o Verovio*: numa cópia MEI de cada peça, **todo o conteúdo de todos
    os compassos** (e de um em cada 3) é trocado por `<mRest/>`; 5 170 pausas
    desenhadas pelo Verovio contra a regra: **0 divergências** (`x`, `y`, glifo,
    escala; |dx| máximo 0,00) em todas as categorias: 612 primeiro do sistema,
    3 699 comum, 742 último, 42 primeiro com barra de repetição à esquerda, 54
    barra de repetição à esquerda, 21 cabeçalho no meio (armadura, fórmula ou
    clave trocada); mais os 2 compassos de 2 semibreves, onde o Verovio desenha
    `E4E2` e a regra, coerente, não dá pausa. Sem o campo `inner` isso não se
    atingia: a margem de 87 a 90 unidades depois do cabeçalho não sai da cena
    (um compasso com cabeçalho errava o centro em até 1,4 unidade, e em até 18 se a
    borda usada era a de cada pauta em vez da mais larga das duas).

**O que o host não deve fazer** (acréscimo): deduzir o centro do compasso pelo
`bbox` do `measure` (inclui o número do compasso e as sobras) ou pela borda do
cabeçalho; desenhar a pausa de compasso com `dur` de nota ou pontos; esconder
`mRest` ou pausa de pauta sem nota.

**Limitações da regra 8.** Pausa de compasso de várias vozes em camadas
(`GetOptimalLayerLocation`: a posição vertical muda): fica na posição padrão da
pauta; pausa multi-compasso (`multiRest`) fora; ligadura que cruza para um compasso
visível fica (dá a entender que o som continua); dedilhado, ottava, trinado e
fermata ficam; nota ligada a um compasso visível continua visível lá.

## Histórico de revisões

| Data | Mudança |
| --- | --- |
| 2026-09-17 | S01: formato nomeado Verovio Score Bridge (`.vsb`), flags `-t vsb`/`-t vsb-json`, timemap embutido quando disponível, exemplo mínimo, schema v1 e correspondência completa da IR. |
| 2026-09-17 | Correção pós-S04: `pages[].elements` (§5.5) definido para o índice plano de elementos endereçáveis que `BridgeDeviceContext` já constrói (`BridgePage::index`) mas que nunca tinha ganhado forma na especificação/schema; tabela de §8 atualizada de `Lottie*` para os nomes atuais `Bridge*` (renomeados em S02) e completada com as linhas de `BridgeGlyphUse`/`BridgeChild.glyphUse` (S03) e `BridgeNode.bbox`/`BridgeIndexEntry` (S04), que tinham ficado como placeholders de uma linha só. |
| 2026-09-17 | Correção durante S05: a tabela de §8 previa `t.family` vindo de "`FontInfo` ativo (fora de `BridgeTextRun`)", mas nenhuma estrutura da IR carregava essa informação até a árvore ser serializada, e o `BridgeWriter` não tem acesso ao `FontInfo` do `DeviceContext` (que só existe durante o `DrawText`). Adicionado `BridgeTextRun::family` (`bridgegeometry.h`), populado em `BridgeDeviceContext::DrawText` a partir de `FontInfo::GetFaceName()` (com o mesmo fallback que a raiz do SVG usa quando vazia); tabela corrigida para refletir a IR real. |
| 2026-09-18 | Correção do S08: especificado que `glyphs[].bbox` é `[x, y, width, height]` na escala interna do Verovio (10× os contornos) e com Y para cima, incluindo a conversão normativa para o sistema dos contornos; tabela de §8 e parser Dart atualizados para o tipo explícito `GlyphBBox`. |
| 2026-09-19 | Correção pós-S04: §5.1 explicita que `bbox` é no referencial de conteúdo (antes do `translate(origin)`; comparar contra o `viewBox` somando `origin`, §3) — era o que sustentava a ressalva da bbox da raiz, agora encerrada; §5.5 corrige "nenhum caso observado" para os 5 653 casos reais de `[0, 0, 0, 0]` (tabela por classe nas notas de S04). |
| 2026-09-19 | Correção R06b: §5.2 ganha a exceção de pena 0 — formas desenhadas com `SetPen(0)` (só preenchimento por intenção: feixes, colchetes de pedal, pontos) saem com `"stroke": "none"` em vez do hairline de 1 unidade herdado da regra CSS global, que o Impeller alargava em um pixel inteiro nas formas finas. Medido no corpus: 24,2% das formas passam a `stroke: none` (todos os `r`/`e`, mais os `p` de feixe/polígono cheio); média de divergência 0,4122% → 0,3959% (−3,9% dos pixels divergentes). |
| 2026-09-20 | `pages[].elements` removido do formato: o índice plano de §5.5 era redundância deliberada com a árvore e custava 20,5% do `scene.json` / 29,3% do `.vsb`. §5.5 passa a especificar a **regra de derivação** que o leitor aplica no percurso que já faz; `BridgeIndexEntry`/`BridgePage::index` saíram do exportador e o `score_bridge` constrói `ScenePage.elements` no parse. Um leitor que encontre `elements` num arquivo antigo pode ignorá-lo. |
| 2026-09-20 | `meta.json` (§2.3): título e autores da peça, uma vez por documento e à parte do `scene.json`, lidos do `<meiHead>` do Verovio (MEI e MusicXML). Opcional, com a mesma regra de omissão do timemap (`manifest.files.meta`; propriedade `meta` no JSON único). Mudança aditiva: `version` continua `1` e leitores antigos, que ignoram o arquivo extra, seguem funcionando. Schema, fixture e `score_bridge` (`VsbDocument.meta`) atualizados. |
| 2026-09-20 | `meta.title` passa a ser derivado do cabeçalho **renderizado** (`Page::GetHeader()` da página 1), seguindo `--header`: ausente com `none`, primeira linha do bloco de título com `auto`, título do cabeçalho codificado com `encoded`. Antes vinha do `<meiHead>`, o que dava título mesmo com o cabeçalho desligado e nenhum título nas peças MusicXML que só têm `<credit-words>` (4 das 5 do corpus, agora todas com título). `creators` continua vindo do `<meiHead>`. Sem mudança de forma: schema, fixture e leitor Dart inalterados. |
| 2026-09-21 | E01b: §2.4 (nova) documenta o timemap embutido — sempre pedido com `includeMeasures: true` (preenche `measureOn`) e a regra de sufixo `-rend<N>` que resolve um id expandido do timemap ao nó da cena (D-EXPMAP, decisão do usuário: regra documentada, sem `expansion.json` à parte). Mudança aditiva: `version` continua `1`, o formato do pacote não muda, só o conteúdo de `timemap.json` ganha mais um campo por instante. |
| 2026-09-22 | P01a (D-META-TITULO, opção (a)): `meta.title` deixa de depender de `--header`. Passa a ser o título que o cabeçalho mostraria com `--header auto` — do `<pgHead func="first">`/`<credit>` codificado se a peça já traz um, senão de um `PgHead` descartável gerado do mesmo jeito que `Doc::GenerateHeader()` faria — calculado mesmo com `--header none`. Motivo: P01b torna `--header none` o padrão do `.vsb` (D-VSB-PADRAO), e o host precisa do título mesmo sem cabeçalho desenhado. Medido nas 10 peças do corpus: `title` passa a ser igual com `none`, `auto` e `encoded` (30/30; antes, `encoded` saía sem título nas 5 peças MEI, que não têm `<pgHead>` codificado). `creators` não muda (já independia de `--header`). `scene.json`, `glyphs.json` e `-t svg` byte-idênticos nos 3 valores de `--header` (o desenho não muda). |
| 2026-09-22 | P02a (D-ALT/D-ALT-EXTENSAO): `alternates.json` (§2.5, novo) — páginas alternativas do player para saltos de repetição que mudam de página, cada sequência do compasso de chegada até o fim da peça, mesma forma de `scene.pages[i]` e mesmo `glyphs.json`. `files.alternates`/propriedade `alternates` opcionais (§2.1/§2.2), mesma regra de omissão do timemap/`meta`. §5.5 explicita que o índice de elementos é por sequência (não existe índice único do documento, já que ids se repetem entre sequências e páginas normais por construção). §9: aditivo, leitor antigo ignora. Mudança só de documentação e schema (`$defs/alternateSequence`, `$defs/alternatesDocument`, reuso de `$defs/page`) — nenhum código ainda; `docs/formato/exemplo-alternates.json` (novo) é o primeiro documento a validar contra o schema novo. |
| 2026-09-24 | Modo debug (§2.6, novo): `--vsb-debug` embute `debug-options.json` (`Toolkit::GetOptions()`) e `debug-source.txt` (o documento como `Toolkit::LoadData` o recebeu) no `.vsb`, e a propriedade `debug` no JSON único, para reproduzir um render só a partir do pacote (uso: `compare/scripts/compare-page.sh` com um `.vsb` em vez da partitura + flags originais). Nova flag `--options-file` no `verovio` (`tools/main.cpp`) aplica esse JSON via `Toolkit::SetOptions`. Aditivo: `version` continua `1`, mesma regra de omissão do timemap/`meta`/`alternates`; leitor antigo ignora. `manifest.files.debugOptions`/`.debugSource`, `$defs/debug` no schema. |
| 2026-09-25 | G01: `midi.json` (§2.7, novo) — o fluxo de eventos (`notes[]`/`pedal[]`) que o exportador MIDI do Verovio emitiria, com o `xml:id` de origem e o tempo já em ms, ligaduras unidas e ornamentos expandidos como no `.mid`. Gravado por um "gravador" opcional em `GenerateMIDIFunctor` (`SetEventLog`, `nullptr` por padrão — zero mudança no `.mid`/`.vsb` existentes), repassado por `Doc::ExportMIDI(midiFile, eventLog = nullptr)`, serializado por `BridgeWriter::WriteMidi` (conversão semínima→ms pelos pontos de andamento em `MIDIEventLog::tempos`) e integrado nos dois caminhos de exportação do bridge (`Toolkit::RenderMidiEventLog`, chamado por `RenderToBridgeJson`/`RenderToBridgeFile`). Aditivo: `version` continua `1`, mesma regra de omissão do timemap/`meta`/`alternates`; leitor antigo ignora. `manifest.files.midi`, propriedade `midi` no JSON único, `$defs/midiDocument` no schema. |
| 2026-09-29 | G04a-G04d (nota fantasma, D-FANT-*): **`pitchpos.json`** (§2.8, novo) — contexto de notação por nota e pausa (`co`, `sh`, `key`, `acc`, `pn`/`o`/`alt`/`loc`), indexado pelo id **notado**; **nó `staff`** (§5.1) ganha `lines`/`ledger`/`ledgerCue`/`gs`, e nós de nota/acorde/pausa cross-staff ganham `staff`; **glifos reservados** (§4) sempre no dicionário (E0A4, E260-E262, E511/E512/E515/E516); **timemap** (§2.4) passa a ser pedido com `includeRests` (`restsOn`/`restsOff`, só essas chaves são novas); **§10 Nota fantasma** (normativo, com 3 exemplos do Satie), validada por oráculo Verovio (2 400 alvos, 100%) e vetores `docs/formato/fantasma/vetores.json`. Aditivo: `version` continua `1`, leitor antigo ignora tudo; `manifest.files.pitchpos`, propriedade `pitchpos` no JSON único, `$defs/pitchposDocument`/`pitchposEvent` no schema, `exemplo-pitchpos.json`. Flag `--no-vsb-pitchpos` desliga o arquivo. |
| 2026-09-30 | G06 (fantasma cross-staff): **§10 passos 1 e 5** — a fantasma vai para a pauta onde a altura cabe (menos linhas suplementares brutas; desempates: menor `\|k − ref\|`, depois maior `ref`); coluna (x) do candidato mais próximo dentro da pauta escolhida; grafia e acidente usam o contexto da pauta (`co`/`sh`/`key`/`acc` do evento dela mais próximo de `k`); `8va`/`8vb`/`15ma`/`15mb` só no extremo do sistema ou com pauta única. Sem campo novo no `.vsb` (`version` continua `1`): o host alimenta `E` com as notas do passo + as pausas (`restsOn`) e as notas seguradas do instante — varredura do corpus (7 113 instantes): 183 sem cobertura (2,6%, quase todos de mão única soando sozinha), nunca as duas pautas sem evento. Referência (`ghost_ref.py`) + 6 vetores novos (32 casos, `resumo` à mão) + Ex. 4 no §10.1. Porta Dart no `zywny`. |
| 2026-11-04 | G08a (nota escondida, D-SUM-FIGURA = (a), decisão do usuário): **`pitchpos.json`** (§2.8) ganha `dur` e `dots` por nota e pausa — a figura escrita, não deduzida do timemap; **glifos reservados** (§4) passam a 16, com as pausas `E4E3`-`E4E9` e o ponto `E1E7`; **§11 Nota escondida e pausa substituta** (normativo; regras 1-7, "o que o host não deve fazer" e esqueleto de §11.1). A regra 1 trata o **acorde** (haste, colchete e pontos são filhos do nó `chord`, não da nota) e a regra 6 corrige a posição vertical da pausa de mínima e semibreve para a do Verovio; os pontos são um círculo (`View::DrawDot`), não o glifo `E1E7`. Regras 3 e dos pontos sujeitas a conferência em G08c. Aditivo: `version` continua `1`, leitor antigo ignora tudo. Schema e `exemplo-pitchpos.json` atualizados. |
| 2026-11-04 | G08c (nota escondida, referência e prova): **§11** corrigida onde a medição contradisse o texto de G08a — regra 3 passa a contar a **pausa deslocada** entre as donas do traço (o traço fundido com o dela fica); regra 6 troca `dur ≥ 2` por `dur ≤ 2` (era numericamente trocado), declara `n ≠ 5` sem pausa, a largura do glifo no cálculo do ponto é **truncada** (o Verovio usa `int`) e o `x` da pausa é o da cabeça por definição; regra 2 registra o `beamSpan` como limitação; §11.1 preenchida com os dois exemplos do hino 010. Medido: 7 381 traços, 0 sem dona, 0 com donas de colunas diferentes (D-SUM-NATIVO: sem dado novo na cena); 855 pausas de verdade e 840 colunas trocadas por pausa dentro do Verovio, 0 divergências de glifo/`y`/escala/pontos. Referência `hide_ref.py`, varredura `g08c-sweep.py`, oráculo `hide_oracle.py`, 11 vetores em `docs/formato/sumico/vetores.json`. Sem mudança no formato (`version` continua `1`). |
| 2026-11-04 | G11 (esconder um compasso inteiro, D-SUM-COMPASSO = campo no formato, decisão do usuário): **`measure.inner`** (§5.1) — `[x0, x1]`, a faixa em que o Verovio centra a pausa de compasso (`GetDrawingX() + GetLeftBarLineRight()` e `+ GetRightBarLineLeft()`), gravado em todo nó `measure` (aditivo, `version` continua `1`; leitor antigo ignora); **§11.2, regra 8** (normativa): pausa de compasso substituta (glifo `E4E3`, `x` do centro de `inner`, `y` da regra da semibreve, sem pontos), o que some com o compasso (notas, pausas de verdade em pauta que tem nota, tercina, ligaduras de prolongamento/expressão, arpejo e `beamSpan` pelo dono = compassos que tocam), o que fica, e a classificação por ocorrências em 70 partituras. Provado: 5 170 pausas desenhadas pelo Verovio com 0 divergências de `x`, `y`, glifo e escala; 124 páginas, 1 517 compassos escondidos, 0 vazamentos. Sem o campo, o `x` de um compasso com cabeçalho errava até 1,4 unidade (até 18 por pauta). Exige refazer a `libverovio` (Linux, Android, Web). Schema (`measure.inner`) e 15 casos novos em `vetores.json` (`casosCompasso`). |
| 2026-11-08 | M02 (`music.json`, §2.9, novo; ver M00): arquivo opcional com a estrutura da partitura notada, sem geometria — partes, compassos (`n`, casas, barras, fórmula, armadura e modo), pautas, camadas e eventos (nota, pausa, `mr`, acorde, apojatura, quiáltera), ornamentos, cifras (`harmonies`), direções (`directions`) e andamentos (`tempi`). `manifest.files.music`, propriedade `music` no JSON único, `$defs/musicDocument` (e auxiliares) no schema. Aditivo: `version` continua `1`; leitor antigo ignora. §2.9 traz as ressalvas R1-R5; a R1 (a inversão de `grace` pelo importador do MusicXML) fica pendente de decisão do usuário. Fixture: `docs/formato/musica/` (`m02-entrada.musicxml` sintético + `m02-esperado.json`), conferida contra o MusicXML e o MEI com `-x 42`. |
| 2026-11-08 | M04 (`music.json`, §2.9, regras 7 e 8; ver M00): `harmonies` e `directions` passam a sair preenchidos. A estrutura da `<harmony>` (raiz, alteração, `kind`, `kind@text`, baixo, graus, numeral) é guardada pelo importador MusicXML num `HarmData` ligado ao `harm` e lida por `ReadBridgeMusic`; o MEI não muda. `text` sai do `Doc`, então `<words>` com formatação chega inteiro. Figured bass (`fb`) fica fora de `harmonies`. Aditivo: `version` continua `1`; o schema não muda (já previa os campos). |
| 2026-11-08 | M07 (oráculo do `music.json`, `compare/scripts/music_oracle.py`): R1 corrigida (refutada: o importador grava o valor do MEI, sem inversão); R3 atualizada com a medição; R6 (espaços de preenchimento `s`, gerados pelo importador) acrescentada. Vetores em `docs/formato/musica/vetores/` (oito `music.json` conferidos contra a fonte). Sem mudança de forma: `version` continua `1`. |
| 2026-11-08 | M05 (API; §2.8 e §2.10, novo): `renderToMusicJson` (C e Dart) devolve `timemap`, `midi`, `pitchpos` e `music` sem desenho e sem layout, nos ids da carga. Em `pitchpos`, `loc` e `acc` passam a poder sair `null` nessa chamada quando o documento não foi cortado no carregamento (`--breaks none` ou MEI com `<pages>`); o `.vsb` e o JSON único não mudam. Esquema: `musicJsonDocument`; `loc` e `acc` aceitam `null`. |
| 2026-11-08 | M05-P (correção do M05; §2.8 e §2.10): `renderToMusicJson` monta o layout das páginas, sem desenhar, quando o carregamento não cortou (`--breaks none`, MEI com `<pages>`), para `loc` e `acc` do `pitchpos` saírem preenchidos e iguais aos de `renderToBridgeJson` da mesma carga. Deixa de haver `null` em `loc` e `acc` nas saídas do formato (decisão do usuário, 2026-11-08). Aditivo: `version` continua `1`; o `.vsb`, o JSON único e as demais chaves de `renderToMusicJson` não mudam. O schema ainda aceita `null` nesses dois campos (não foi alterado). |
| 2026-11-08 | R2 (regras 5 e 6 da §2.9; decisões do usuário de 2026-11-08): **`parts`** passa a depender do formato da fonte (MusicXML: uma entrada por `<part>`; MEI: uma por `staffGrp`, e um `staffGrp` sem `staffGrp` filho é uma parte só, com todas as pautas). **`ornaments`** ganha `measure` e `tstamp`, e `startid` passa a poder ser `null`; cada item tem `startid` ou `tstamp` não nulo (os 12 trinados do Scarlatti, só com `@tstamp`, entram). **`pitchpos`** (esquema): `loc` e `acc` sem `null`, como já dizia §2.8 (M05-P). Mudança não aditiva para quem lê `ornaments`: `measure` e `tstamp` são campos novos e `startid` pode vir `null`; `version` continua `1`. O `.vsb`/JSON único não mudam fora de `music.json`. |
