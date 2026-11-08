# M00 — Os dados musicais que o `zywny-aprendizado` pede ao Verovio (`music.json`)

**Status: concluído com ressalvas (2026-11-08, M08).** O M06 (`score_bridge` em Dart) **não foi executado neste repositório**: fica para o `zywny` (decisão do usuário, 2026-11-08; o pacote não está aqui). O `wasm` do `renderToMusicJson` não foi compilado aqui, e `just medidor` do aprendizado não rodou (depende da troca do `getElementAttr` no app). Detalhes em "Notas de execução" (M08) e na nota para o host, [`docs/nota-para-zywny-musica.md`](../nota-para-zywny-musica.md).

**Depende de:** G01 e G04c (o `midi.json` e o `pitchpos.json` já existem) ·
**Decisões:** **D-MUSICA-FORMA**, **D-MUSICA-CIFRA** e **D-MUSICA-Q** resolvidas pelo usuário em 2026-11-07 (abaixo); o `getElementAttr` do M05 também (ver "Notas de execução"). **Correção (M05-P, 2026-11-08):** `renderToMusicJson` monta o layout quando o carregamento não cortou, e `loc`/`acc` do `pitchpos` saem completos também sem corte (decisão do usuário; ver o fim de "Notas de execução")

> Pedido do `zywny-aprendizado` (regra de projeto no `CLAUDE.md` de lá:
> *"toda informação musical que vem de um MusicXML ou de um MEI é extraída pelo
> Verovio, nunca pela leitura direta do XML"*; passos LM15 e seguintes). Este
> documento diz **o que o Verovio deste repositório precisa passar a exportar**
> para o app deixar de ler o texto do MusicXML, e como fazer. O código do app
> (Dart, `zywny-aprendizado` e `zywny-comum`) **não** se faz aqui: ver o M08.

Este arquivo é um plano de vários passos (M01 a M08, tabela no fim), no molde do
G07/G11: a visão geral, os fatos medidos, a proposta, as decisões e os critérios
de aceite de cada passo. Quem executar um passo lê este arquivo inteiro e o
`CLAUDE.md` da raiz; o que o passo descobrir volta para cá, em "Notas de
execução".

## Por que

O app (`zywny-aprendizado`) mede músicas, monta exercícios e avalia o teclado
sobre o que o Verovio entende da partitura. Um leitor de texto próprio sempre
acaba divergindo dele (o primeiro leitor do medidor contava o tempo diferente do
timemap em 125 de 600 hinos: repetições e casas). Por isso o app passou a pedir
**tudo** ao Verovio, e achou o que o `.vsb` ainda não entrega. Hoje ele consegue:

- notas, pausas, tempo, repetições expandidas, ligaduras e a altura escrita, do
  `timemap`, do `midi.json` e do `pitchpos.json`;
- a estrutura (compasso → pauta → voz → nota), pela **cena** (`scene.json`), com
  o `id` e a `class` de cada nó;
- os atributos de um elemento (`n` do compasso, da pauta e da voz, `left`/`right`
  do compasso, `grace` da nota), pelo `getElementAttr`, **um pedido por
  elemento**.

E tropeça em quatro coisas, todas medidas (ver "Fatos medidos"):

1. **A fórmula de compasso e a armadura não saem.** O nó `meterSig` da cena tem
   um id de uma cópia de desenho: o `getElementAttr` não o acha (`Element 'x' not
   found`). O app hoje reconhece a fórmula pelos **glifos de algarismo** do nó
   (SMuFL `E080`–`E089`) e a armadura pelo `pitchpos`. É um remendo: não dá o
   `sym` (C, C cortado) fiel, nem o **modo** (`<mode>`), nem armadura não
   padrão.
2. **O modo (maior/menor) do `<key>` não sai** em lugar nenhum, embora o
   importador MusicXML o leia (`iomusxml.cpp`, `keySig->SetMode(...)`).
3. **As cifras (`<harmony>`) saem só como o texto desenhado** (`C`, `Cmaj7`...).
   O importador monta o texto e **joga fora** a estrutura: raiz, alteração da
   raiz, `kind` (`major-seventh`), `text` do `kind`, baixo, graus. O app precisa
   da estrutura para converter em sua grafia (`C7M`) e para dar erro certo
   quando o tipo não tem nome.
4. **O texto das direções (`<words>`) não sai por elemento**: o app usa a marca
   `chg` (troca de acorde) e hoje só a acharia desenhada na cena, no meio de um
   `SceneText`.

Além disso há custo e ergonomia:

- O app (nativo: isolate; Web: worker) não pode fazer um `getElementAttr` por
  elemento sem uma viagem de ida e volta cada; hoje o isolate pré-busca os
  atributos de **todo** `measure`, `staff`, `layer` e `note` da cena (milhares de
  chamadas por hino).
- Para ler a música, o app renderiza **todas as páginas** (`renderToBridgeJson`)
  só para obter a cena e as outras três tabelas. A cena precisa de layout; as
  outras três (timemap, midi, pitchpos) precisam do layout só no caso do pitchpos
  (ver acima), não do desenho. Medido no M01 (in-process, mediana de 5 cargas):
  ~16 ms numa peça de 8 compassos (twinkle) e ~181 ms por hino na mediana de 20
  hinos com `renderToBridgeJson` (números dos 600 hinos em "Notas de execução").
- O binding Dart do `getElementAttr` tem **um argumento a mais** que a função C
  (`getElementAttr(String element, String attribute)` contra
  `vrvToolkit_getElementAttr(tk, xmlId)`): funciona por acaso na convenção de
  chamada x86-64/arm64; será corrigido no M05 removendo o segundo argumento (decisão de 2026-11-07; quebra quem chama com dois).

## Ler antes (só isto)

- `docs/formato/especificacao-v1.md`: §2 (empacotamento), §2.4 (timemap e ids
  `-rend<N>`), §2.7 (`midi.json`), §2.8 (`pitchpos.json`), "Histórico de
  revisões".
- [`G01`](G01-gravador-de-notas-midi.md) e [`G04c`](G04c-contexto-por-evento.md)
  (como o `midi.json` e o `pitchpos.json` são montados: `RenderMidiEventLog`,
  `RenderPitchPos`, `bridgepitchpos.cpp`).
- `verovio/src/toolkit.cpp`: `RenderToBridgeJson` (~L2094), `ReadBridgeMeta`
  (~L2334), `RenderToBridgeFile` (~L2440): onde as tabelas são juntadas.
- `verovio/src/iomusxml.cpp`: `ReadMusicXmlHarmony` (L2858: onde a cifra vira
  texto e a estrutura se perde), a leitura de `<key>` com `<mode>` (~L4470), e a
  de `<words>`/`<direction>` (procure `ReadMusicXmlDirection`).
- `verovio/tools/c_wrapper.{h,cpp}`, `verovio/bindings/dart/lib/src/`
  (`verovio_bindings.dart`, `verovio_toolkit.dart`) e
  `verovio/emscripten/exports.txt`: as três superfícies de API.
- No `zywny-aprendizado` (para saber o que o consumidor faz com cada dado):
  `lib/music_reading/music_verovio.dart` (o leitor, `readMusic`),
  `docs/plano/LM15-verovio-como-fonte.md` e o `CLAUDE.md` (seções "Regra de
  projeto: a informação musical vem do Verovio" e "Leitura pela música: o
  medidor"). Para a melodia e as cifras: `zywny-comum/packages/zywny_music/lib/
  melody_xml.dart` (**o leitor que este plano manda aposentar**).

## O que o app faz com cada dado

Cada linha é uma necessidade do consumidor; a coluna "Hoje" é o que o Verovio
entrega agora; "Falta" é o que este plano acrescenta.

| Dado | Quem usa | Hoje | Falta |
| --- | --- | --- | --- |
| Compassos na ordem da partitura, com o rótulo `n` (`"1"`, `"1i"` da introdução, `"0"` da anacruse) | medidor, melodia | cena (`measure` + `getElementAttr`) | `n` no próprio dado |
| Barra de repetição `left`/`right`, casa (`<ending>`) | medidor (seções), melodia | `left`/`right` por `getElementAttr`; **casa não** | `left`, `right`, `ending` |
| Fórmula de compasso vigente (`count`, `unit`, `sym`) | medidor, melodia, `play-lead-sheet` | **glifos desenhados** (remendo) | `meter` por compasso |
| Armadura vigente (`sig`, quintas) e **modo** | medidor, `harmonize`, `keys:` | quintas pelo `pitchpos.key`; **modo não** | `key` por compasso, com `mode` |
| Pautas e vozes (`n` da pauta e da camada) por nota e pausa | medidor, melodia (voz 1) | cena + `getElementAttr` | `staff`, `layer` na nota |
| Parte (`<part id>`) a que cada pauta pertence | melodia ("a primeira parte") | **não** | `parts[]` |
| Nota de apojatura (`grace`) | medidor, melodia | `getElementAttr` por nota | `grace` na nota |
| Quiáltera (razão `num:numbase`) | medidor | ancestral `tuplet` da cena | `tuplet` na nota |
| Notas do mesmo acorde (`<chord>`) | melodia ("a mais aguda") | ancestral `chord` da cena | `chord` (id) na nota |
| Trinado, mordente, grupeto | medidor | nós `trill`/`mordent`/`turn` da cena | lista `ornaments` |
| Tempo de partitura da nota **sem desdobrar repetições** (`q`, `ql`, em semínimas) | medidor, melodia | recomposto pelo app a partir do timemap | — (fica fora, D-MUSICA-Q) |
| Andamento (`midi.bpm`) | medidor | `timemap.tempo` | — |
| **Cifras** (`<harmony>`): hora, raiz, alteração, `kind`, `text`, baixo, graus | `harmonize`, `play-lead-sheet` | só o texto desenhado | `harmonies[]` estruturado |
| **Direções** (`<words>`): hora e texto (`chg`) | `harmonize` | só o texto desenhado | `directions[]` |

Nada disto precisa de layout: é a estrutura da **partitura notada**, a mesma
que a cena desenha, tirada do `Doc` (não do desenho).

## Fatos medidos (não os assuma de novo; confira ao medir)

- A cena (`scene.pages[].root`) tem nós `class: measure | staff | layer | note |
  rest | mRest | chord | tuplet | graceGrp | trill | mordent | turn | meterSig |
  keySig | harm | dir ...` com `id`. `getElementAttr` acha `measure` (`{"n",
  "left", "right", "metcon"}`), `staff` (`{"n"}`) e `layer` (`{"n"}`), **não** o
  `meterSig`/`keySig` desenhados.
- Um MEI exportado de MusicXML tem o `<meterSig xml:id="…" count="4" unit="4"/>`
  dentro do `<staffDef>`, mas o `xml:id` **não é o do nó da cena** (cópia de
  desenho).
- `layer n` = o número da `<voice>` do MusicXML (a voz 5 do baixo sai como
  `layer n="5"`); `staff n` = o da pauta.
- O compasso de introdução do Hymn_Grabber sai com `n="1i"`, `"2i"`... (rótulo
  texto, não número) e o da anacruse com `n="0"` e `metcon="false"`.
- `Harm` guarda o `Text` já montado e `@type` (o do `<harmony type>`) e
  `@tstamp`; a raiz, a alteração, o `kind`, o `text` do `kind`, o baixo e os
  graus **não são guardados**. (Confirmado no M01, `ReadMusicXmlHarmony`, L2858.
  Quando existe, o `kind@text` é que vira o texto do `Harm`: em 14 852 de 30 553
  cifras dos 610 arquivos medidos.)
- O timemap desdobra repetições e casas (ids `-rend<N>`); a primeira passada tem
  o id notado. Os compassos depois de uma barra final (`right="end"`) **não**
  entram no timemap (o hino 458 tem 9 deles).
- `Toolkit::RenderToBridgeJson` monta, nesta ordem: `scene` (`RenderPagesToBridge`,
  precisa de layout), `timemap` (`RenderToTimemap`), `meta`, `midi`
  (`RenderMidiEventLog`) e `pitchpos` (`RenderPitchPos`, `toolkit.cpp` L2108-L2121).
  O `pitchpos` lê o layout que a `scene` também usa, e por isso vem antes das
  alternativas (que fazem `Select`/`RedoLayout`). O primeiro `RenderToTimemap` ou
  `RenderMidiEventLog` de uma carga chama `SetMidiDoc()`, que reexporta o MEI e o
  reimporta num `Doc` expandido (`toolkit.cpp` L288-L310): ~37 ms na 1ª chamada,
  depois cacheado (ver M01).
- O `midi.json` já dá, por nota, `s` (pauta), `l` (camada), `tied` (a cadeia da
  ligadura) e `orn`; o `pitchpos.json`, `pn`/`o`/`alt`/`dur`/`dots` e a
  armadura vigente (`key`). **Não** repita isso em `music.json`.

## Proposta

### 1. Um arquivo novo: `music.json` (§2.9 da spec)

A **estrutura musical da partitura notada**, sem geometria. Opcional como os
outros (mesma regra de omissão: `manifest.files.music`; propriedade `music` no
JSON único). Mudança **aditiva**: `version` continua `1`; leitor antigo ignora o
arquivo extra.

```json
{
  "version": 1,
  "parts": [
    { "id": "P1", "name": "Piano", "staves": [1, 2] }
  ],
  "measures": [
    {
      "id": "m1x…", "index": 0, "n": "1",
      "left": "rptstart", "right": null,
      "ending": null,
      "meter": { "count": 4, "unit": 4, "sym": null },
      "key":   { "sig": "2s", "fifths": 2, "mode": "major" },
      "staves": [
        { "n": 1, "layers": [
          { "n": 1, "events": [
            { "id": "n1a2b", "t": "n",
              "chord": null, "grace": false, "tuplet": null },
            { "id": "r9z",   "t": "r" }
          ] }
        ] }
      ]
    }
  ],
  "ornaments":  [ { "id": "t1", "kind": "trill", "startid": "n1a2b" } ],
  "harmonies":  [ { "id": "h1", "measure": 0, "staff": 1, "tstamp": 1,
                    "root": "C", "rootAlter": 0,
                    "kind": "major-seventh", "kindText": null,
                    "bass": "G", "bassAlter": 0,
                    "degrees": [ { "value": 9, "alter": 0, "type": "add" } ],
                    "text": "Cmaj7/G" } ],
  "directions": [ { "id": "d1", "measure": 0, "staff": 1, "tstamp": 1,
                    "place": "above", "text": "chg" } ],
  "tempi":      [ { "id": "tp1", "measure": 0, "bpm": 100, "text": null } ]
}
```

Regras normativas (a spec ganha uma §2.9 com isto; o M02 as escreve):

1. **Ordem e ids.** `measures` na ordem do documento **notado** (sem desdobrar
   repetições; as casas uma depois da outra, como estão escritas), incluindo os
   compassos de introdução e os que o timemap não toca. Os ids são os **notados**
   (os mesmos da cena, do `pitchpos.json` e, na primeira execução, do timemap);
   a regra do sufixo `-rend<N>` da §2.4 vale.
2. **`n`** é o texto do `@n` do compasso, sem interpretação. **`left`/`right`**:
   `rptstart`, `rptend`, `rptboth`, `end`, `dbl`... (o valor do MEI), `null` se
   não há. **`ending`**: `{"n": "1"}` se o compasso está dentro de uma
   `<ending>`, senão `null`. **Corrigido no M01:** o valor é o `@number` da casa,
   que pode ser uma lista (`"2,3,4"`), e **não** o texto impresso (`"2. 3. e 4."`):
   o importador perde o texto no `<ending type="stop">` (`iomusxml.cpp` L428). A
   spec diz isso (lista separada por vírgula).
3. **`meter`** e **`key`** são os **vigentes no começo do compasso** (herdados do
   `scoreDef`/`staffDef` anterior), da primeira pauta; um compasso novo só repete
   o que mudou se o leitor comparar com o anterior. `sym`: `"common"` ou `"cut"`
   quando o MusicXML pede `symbol="common|cut"`, senão `null`; `count`/`unit`
   sempre presentes (C = 4/4, C cortado = 2/2). `key.sig` é o `@sig` do MEI
   (`"0"`, `"2s"`, `"3f"`; `null` se não padrão) e `fifths` a soma das
   alterações (a armadura fora do padrão também sai assim); **`mode`** é o do
   `<mode>` (`"major"`, `"minor"`, `"dorian"`…) ou `null` quando o arquivo não o
   diz.
4. **`events`**: toda nota (`"n"`), pausa (`"r"`), pausa de compasso (`"mr"`) e
   `space` (`"s"`) da camada, **na ordem do documento**. Sem `q`/`ql` (D-MUSICA-Q): o tempo da
   nota sai do timemap, pelo mesmo id. `chord`: o id do `<chord>` a que a nota pertence
   (`null` fora de acorde). `grace`: `false`, `"acc"` ou `"unacc"` (`@grace` da
   nota ou `<graceGrp>` pai). **Pauta de cada evento (corrigido no M01):** uma nota cruzada (o `<staff>`
   do MusicXML é diferente da pauta onde o Verovio a guarda) fica numa camada da
   pauta de origem, mas o MEI traz o `@staff` do próprio nó (`note` ou `chord`).
   Medido: 123 notas em `Clair_de_Lune` e 2 em `Nocturne`. A pauta do evento é o
   `@staff` do nó quando existe, senão a da pauta que o contém (regra para a §2.9,
   no M02). `tuplet`: `{"num": 3, "numbase": 2}` da quiáltera
   mais interna (a razão composta só se o MEI a tem; ver "Fica fora"), senão
   `null`. **Altura, figura e ligadura não se repetem aqui**: estão no
   `pitchpos.json` e no `midi.json`, pelo mesmo id.
5. **`parts`**: uma entrada por `<part>` do MusicXML (ou `staffGrp` do MEI), com
   o `id` do arquivo (`P1`), o nome e as pautas (`@n`) que ele tem. Serve a "a
   primeira parte" da melodia. Num MEI sem partes, uma só com todas as pautas.
6. **`ornaments`**: os elementos de controle `trill`, `mordent` e `turn`, com
   `startid` (fermata e os outros ficam fora). Substitui contar nós da cena.
7. **`harmonies`** (D-MUSICA-CIFRA): uma por `<harmony>`, na ordem do
   documento. `tstamp` é o do MEI (batida a partir de 1, na unidade do compasso);
   A estrutura vem do **MusicXML**: `root` (`root-step`),
   `rootAlter` (`root-alter`, semitons inteiros), `kind` (o conteúdo de
   `<kind>`, ex. `major-seventh`, sem tradução), `kindText` (o atributo `text`
   do `<kind>`, ou `null`), `bass`/`bassAlter`, `degrees`
   (`degree-value`/`-alter`/`-type`) e, para numeral romano, `numeral`
   (`{"root": "V", "alter": 0}`, no lugar de `root`). `text` é o texto que o
   Verovio desenha (o `Harm` já tem). **De um MEI**, onde só há o texto, os
   campos estruturados saem `null` e `text` vale.
8. **`directions`**: uma por `<direction>` com `<words>` (e `<rehearsal>`),
   com o texto (`<words>` concatenados) em `text`, `place` (`above`/`below` ou
   `null`) e a hora. Só texto; dinâmica, pedal e cunha ficam no `midi.json` e na
   cena (G10).
9. **`tempi`**: os andamentos (`midi.bpm` ou `<sound tempo>`/`<metronome>`),
   com `bpm` e o texto desenhado (ou `null`).

### 2. Uma chamada que não desenha: `RenderToMusicJson`

`Toolkit::RenderToMusicJson()`: devolve **um JSON só** com `music` (a §2.9),
`timemap` (§2.4, com `includeMeasures` e `includeRests`, como no `.vsb`), `midi`
(§2.7) e `pitchpos` (§2.8), **sem** `scene`, sem `glyphs` e **sem layout**.

- O `pitchpos` hoje lê o layout (`loc`, `GetDrawingLoc`, `GetDrawingAccid`,
  ponteiros cross-staff) de **todas** as páginas do intervalo pedido
  (`BridgePitchPosBuilder::Build` percorre `firstPage..lastPage`), não só da
  página 1. O layout é calculado em `Page::LayOut` (`CalcAlignmentPitchPosFunctor`,
  `page.cpp`), sem passar pelo `DeviceContext`: dá para produzi-lo sem desenhar.
  Medido no M01 (ver "Notas de execução"): o layout custa ~22 ms por hino; o
  `loc` não precisa sair `null`. O app não usa o `loc`.
- Os ids são os mesmos de um `RenderToBridgeJson` **da mesma carga**.
- Não mexe em estado (nada de `Select`, `RedoLayout` permanente).
- Alvo (a medir no M01 e confirmar no M07): ≤ 50 ms por hino, contra ~0,5 s hoje.
- Superfícies: `vrvToolkit_renderToMusicJson` (C), `renderToMusicJson()` (Dart),
  `_vrvToolkit_renderToMusicJson` (wasm, `exports.txt`) e, no `zywny-aprendizado`,
  o `web/verovio_worker.js` (M08).

O `.vsb` (`-t vsb`) e o JSON único (`-t vsb-json`) **também** passam a levar
`music.json`/`music`, pelo mesmo código (`RenderToBridgeFile`/`RenderToBridgeJson`
chamam o mesmo `ReadBridgeMusic`). O tamanho é pequeno (sem geometria): medir
no corpus.

### 3. O que muda no importador MusicXML

O `music.json` sai do `Doc` **depois** do `LoadData`, então o que o importador
descarta não está lá. Três pontos (o M04 os faz):

- **Cifras:** ao montar o `Harm` em `ReadMusicXmlHarmony`, guardar a estrutura
  (raiz, alteração, `kind`, `kind@text`, baixo, graus, numeral) num objeto
  anexo ao `Harm` (**D-MUSICA-CIFRA**: ver abaixo). Não vai para o MEI (o
  `getMEI` não muda; nenhum teste de MEI pode mudar).
- **Direções:** garantir que o texto de `<words>` de uma `<direction>` chegue ao
  `Dir` por inteiro (hoje vira `<rend>`/`<lb>` conforme a formatação; o
  `music.json` junta o texto cru).
- **Modo:** o `KeySig` já guarda o `mode`; só falta exportar. Conferir o caso de
  `<key>` mudando no meio da peça (`<attributes>` em outro compasso) e o de uma
  armadura sem `<mode>` (`null`).

## Decisões necessárias

Resolvidas pelo usuário em 2026-11-07 (não dependiam de medição; o M01 só confirma os fatos). Cada uma abaixo traz o registro, e o conjunto está em "Notas de execução".

- **D-MUSICA-FORMA — um arquivo novo ou campos na cena?** **Resolvida (2026-11-07): arquivo novo, `music.json`.** *Proposta original (adotada
  enquanto o usuário não disser outra coisa):* arquivo novo (`music.json`), porque
  a estrutura não depende de layout (serve à chamada sem desenho), não infla a
  cena, e o leitor não precisa percorrer árvore de glifos. Alternativa: acrescentar
  `n`, `left`, `right`, `grace`, `meter`, `key` etc. como campos dos nós da
  cena; não resolve cifras/direções (que não são nós de página) nem o custo de
  desenhar.
- **D-MUSICA-CIFRA — onde guardar a estrutura da cifra?** **Resolvida (2026-11-07): campos próprios num `HarmData` ligado ao `Harm`, sem atributo MEI; se o `Harm` não aceitar campo sem mexer no `libmei`, tabela lateral no `Doc` (o M01 confirma o fallback).** *Proposta original:* campos
  próprios num objeto `HarmData` ligado ao `Harm` (ponteiro no `Harm`, preenchido
  só pelo importador MusicXML), **sem** atributo MEI. Alternativas: (a) `@type`
  com JSON (poluiria o MEI e o `type` já é do autor); (b) uma tabela lateral
  `id → HarmData` no `MusicXmlInput` (some depois do `LoadData`, não serve ao
  `Toolkit` sem guardá-la no `Doc`). Se o `Harm` não puder ter campo novo sem
  mexer no schema MEI gerado (`libmei`), usar (b) guardada num mapa do `Doc`.
- **D-MUSICA-Q — o tempo da partitura notada (`q`, `ql`).** **Resolvida (2026-11-07): sem `q`/`ql` no `music.json`; o app segue recompondo pelo timemap.** Pergunta original: o app hoje o recompõe
  do timemap (o compasso mede o que o timemap diz até o seguinte; a primeira
  passada de cada compasso dá o tempo das notas). Se o `Doc` notado já tem
  `scoreTime` por elemento (a camada do `GenerateMIDIFunctor` roda no documento
  expandido, mas `Doc::CalcScoreTime` ou o `Measure::m_scoreTimeOffset` pode
  existir no notado), exportar. *Medir:* se não existe sem expandir, o M03
  calcula a soma de durações por camada (ritmo, quiálteras, ponto), que **já é a
  conta do Verovio** no `DurationInterface`; se nem isso for confiável, **tirar
  `q`/`ql` do `music.json`** e o app segue recompondo pelo timemap (é a solução
  atual, correta, com o custo de código no app).

## Passos

| Passo | O quê | Depende de | Estado |
| --- | --- | --- | --- |
| M01 | **Medir** os fatos (decisões já tomadas, ver "Decisões necessárias"): o que o `Doc` notado tem (`Harm`, `Dir`, `KeySig::mode`, `layer n` = voz, id da parte), custo de `RenderToMusicJson` sem layout | — | concluído com ressalva: células de Chopin e Debussy só parcialmente explicadas (notas invisíveis), ver "Notas de execução" |
| M02 | Especificação: §2.9 `music.json`, o schema JSON, uma fixture, histórico de revisões | M01 | concluído com ressalva: R1 (premissa de que o importador troca os valores de `grace`; **refutada no M07**), ver "Notas de execução" |
| M03 | C++: `ReadBridgeMusic` (partes, compassos, fórmula, armadura e modo, notas/pausas, ornamentos, andamentos) e `music.json` no `.vsb` e no JSON único | M02 | concluído com ressalva: R-PARTES e R-TRINADO resolvidas em R2 (2026-11-08), `score_bridge` sem teste (fonte fora do repositório), ver "Notas de execução" |
| M04 | C++: cifras e direções (a estrutura da `<harmony>` guardada no importador; texto de `<words>`) | M03 | concluído com ressalva: R2 (pauta de cifra em parte de duas pautas) sem caso no corpus; `numeral` só no caso sintético; alteração fracionária truncada (nenhuma no corpus); ver "Notas de execução" |
| M05 | API: `RenderToMusicJson`, `c_wrapper`, binding Dart (e a correção do `getElementAttr`), `exports.txt` | M03, M04 | concluído; **corrigido em M05-P** (2026-11-08): `loc` e `acc` saem completos também sem corte (o layout é montado sem desenhar). Custo mediano de 43 ms com corte, alvo de 50 ms não atingido em 5 de 20 hinos (`SetMidiDoc`); sem corte, ~70 ms de mediana em 10 hinos (ver "Notas de execução") |
| M06 | Dart (`score_bridge`): modelo `VsbMusic` e parser de `music.json` | M02, M05 | **não executado aqui (fica no zywny)**: o pacote `score_bridge` foi para o `zywny-comum` (git subtree) e não está neste repositório; ver M08 |
| M07 | Oráculo, varredura e vetores: `music.json` contra o MusicXML (lido por script), corpus, fixtures do aprendizado e os 600 hinos | M04, M05 | concluído com ressalva: `just medidor` não executado (o aprendizado chama `getElementAttr` com dois argumentos, quebra do M05; ver "Notas de execução", M07); causas R3 (notas invisíveis); R-TRINADO resolvida em R2 |
| M08 | Nota para o `zywny-aprendizado` (a execução Dart de lá fica lá) | M06, M07 | concluído com ressalvas: wasm não compilado aqui, `score_bridge` (M06) não verificado aqui, `just medidor` não rodado, e os ids da Clair de Lune em sequência no mesmo processo (ver "Notas de execução", M08) |

### M01 — Medir e decidir

Sem código de produção (scripts em `compare/scripts/`, saída em `compare/out/`).

1. Para o corpus (`corpus/musicxml/*.mxl`), as quatro partituras de teste do
   aprendizado (`ode`, `intro`, `menor`, `recusa`, em
   `zywny-aprendizado/test/music_reading/fixtures/src/`), as de curso com cifra
   (`test/fixtures/cursos/lead-sheet/media/twinkle.musicxml`, `contrafato-1`,
   `harmonia/media/folclore-1`) e uns 20 hinos do `Hymn_Grabber` (**corrigido no M01:** `folclore-1` não tem `<harmony>` (0), e `folclore-2` tem só `chg`; as cifras de curso são `twinkle` (2 cópias) e `contrafato-1`. O caminho do `Hymn_Grabber` é `/home/mauricio/IdeaProjects/Hymn_Grabber/musicxml_simplificado` e não `../Hymn_Grabber`, que a partir da raiz deste repositório não existe)
   (`musicxml_simplificado/`: 001, 213, 248, 458, e os com repetição e casas):
   confirmar cada linha de "Fatos medidos" e registrar o que mudou.
2. **Doc notado** (`scoreTime` saiu da lista pela D-MUSICA-Q): `layer n` é a voz do MusicXML em todos os casos? Onde o `Doc` guarda
   o `id` da `<part>` (`staffGrp`/`staffDef@n` + `label`/`midi.instr`)? O
   `KeySig::GetMode()` vem preenchido do `<mode>`, e vazio quando não há? Como a
   `<ending>` aparece (`Ending` pai do `Measure`)?
3. **Cifras e direções:** para cada `<harmony>` do corpus, conferir que o
   importador chega a `ReadMusicXmlHarmony` com `kind`, `degree`, `bass` e
   `numeral` e liste os `kind` que `ConvertKindToText` não conhece (viram texto
   vazio?). Mesmo para `<direction><words>`: quantos têm formatação (`<rend>`)
   e como o texto se junta.
4. **Custo:** medir `RenderToBridgeJson` contra uma `RenderToMusicJson`
   provisória (só timemap + midi + pitchpos), por hino. Dizer se o `pitchpos` sem
   desenho é possível.
5. Escrever as **respostas** às três decisões em "Notas de execução" e, se mudar
   a proposta, **corrigir este arquivo**. Se a medição mostrar algo que o
   usuário precise decidir (as decisões de 2026-11-07 já estão tomadas: pare e pergunte só se surgir decisão nova).

**Aceite:** uma tabela "fato → confirmado/corrigido" com os números; as três
decisões resolvidas; este documento coerente com elas.

### M02 — Especificação

Escrever a §2.9 na `especificacao-v1.md` (as regras 1 a 9 acima, já corrigidas
pelo M01), acrescentar `music.json` ao quadro de §2 (e o `music` no JSON único e
no `manifest.files`), o schema (`docs/formato/schema/`, no molde dos outros),
uma fixture mínima e a linha no "Histórico de revisões" (mudança aditiva,
`version` continua `1`). **Aceite:** o schema valida a fixture; a fixture cobre
repetição com casas, anacruse, mudança de armadura e de fórmula, apojatura,
quiáltera, acorde, duas camadas numa pauta, uma cifra com `kind`, `degree` e
baixo, e uma direção `chg`.

### M03 — `ReadBridgeMusic`

Um arquivo novo no estilo de `bridgepitchpos.cpp` (`bridgemusic.cpp/.h`: `struct
BridgeMusic`, `ReadBridgeMusic(Doc&)`), chamado por `RenderToBridgeJson`,
`RenderToBridgeFile` e (M05) `RenderToMusicJson`; `BridgeWriter` serializa. Não
inclui cifras nem direções (M04). **Aceite:** o `music.json` das fixtures bate
com o que o M07 espera; `just`/`cmake` do Verovio compila sem aviso novo; **o
`getMEI` e o SVG de todo o corpus continuam idênticos** (a prova de que o
importador não mudou); `score_bridge` ainda lê o `.vsb` (campo extra ignorado).

### M04 — Cifras e direções

O que o importador guarda (D-MUSICA-CIFRA), a exportação de `harmonies` e
`directions`, e o texto de `<words>`. **Aceite:** para todo `<harmony>` das
fixtures, `root`/`rootAlter`/`kind`/`kindText`/`bass`/`bassAlter`/`degrees` batem
com o que o MusicXML diz (o oráculo do M07 é quem confere); `text` é o mesmo
que o SVG desenha; o `getMEI` não muda.

### M05 — API

- `Toolkit::RenderToMusicJson()` (e a variante `...File`, como as irmãs).
- `vrvToolkit_renderToMusicJson` em `tools/c_wrapper.{h,cpp}`.
- Dart: `renderToMusicJson()` em `verovio_toolkit.dart` e a ligação em
  `verovio_bindings.dart`; **remover o segundo argumento** de `getElementAttr` (fica um, o `xmlId`;
  ver "Por que") quebrando quem chama com dois (decisão de 2026-11-07, sem `@Deprecated`;
  o `zywny` atualiza junto) e registrar a quebra na nota do M08.
- `emscripten/exports.txt`: `_vrvToolkit_renderToMusicJson`.
- `docs`: o `CLAUDE.md` e o `README` do plano (Mapa do código).

**Aceite:** uma chamada de `renderToMusicJson` não altera `getMEI`,
`renderToTimemap` nem `renderToSVG` feitos depois; ids iguais aos de
`renderToBridgeJson` da mesma carga (teste); o tempo medido por hino, no número
do M01.

### M06 — Dart: `score_bridge`

`VsbMusic` (e as classes `MusicMeasure`, `MusicEvent`, `MusicHarmony`,
`MusicDirection`...) e o parser em `VsbDocument.music`, no molde do G02 (`midi`,
`pitchPos`): opcional (`null` sem o arquivo), tolerante a campo desconhecido.
**Aceite:** `flutter test` no `score_bridge` com a fixture do M02 e dois `.vsb`
reais; `flutter analyze` limpo.

### M07 — Oráculo, varredura e vetores

Um script em `compare/scripts/` (Python, no molde de `hide_oracle.py`) que lê o
**MusicXML** diretamente (o oráculo: é o Verovio que está sendo verificado, a
regra "só pelo Verovio" é do app, não deste teste) e confere o `music.json`:
contagem de compassos e notas por compasso, rótulos `n`, `left`/`right`,
fórmula e armadura (com modo) por compasso, `layer n` = `<voice>`, cada cifra
(todos os campos), cada `chg`. Rodar:

- no corpus e nas fixtures do aprendizado;
- nos **600 hinos** (`/home/mauricio/IdeaProjects/Hymn_Grabber/musicxml_simplificado`; corrigido no M01), com `just
  medidor` do aprendizado depois, como prova de ponta a ponta (os números da
  passada do LM14/LM15 não podem mudar: 149 passam o filtro 1, M2 25, M3 6, M4 7,
  M5 56, nenhum 506);
- gerar os **vetores** (fixture → `music.json` esperado) para o `score_bridge` e
  para o aprendizado.

**Aceite:** zero divergência nas fixtures; nos 600 hinos, toda divergência
**listada e explicada** (o oráculo é texto cru; o hino 458 e os compassos depois
da barra final entram como "não tocados", não como erro); tabela com os números
no fim deste arquivo.

### M08 — Nota para o `zywny-aprendizado`

Um arquivo `docs/nota-para-zywny-musica.md` (no molde de
`nota-para-zywny-fantasma.md`) que diz ao host o que mudou e **o que ele pode
apagar**. O que o app faz com isto (a execução é de lá, passos a criar no
`docs/plano` dele):

| No app hoje | Passa a ser |
| --- | --- |
| `MusicVerovio.bridge()` + `attributes(id)` (pré-busca de atributos de `measure`, `staff`, `layer`, `note`) | `MusicVerovio.music()` (o `music.json` + as tabelas); some a pré-busca (`kMusicAttributeClasses`, `musicSnapshotOf`) e o `getElementAttr` |
| Fórmula de compasso pelos glifos da `meterSig` da cena | `measures[].meter` |
| `readMusic` lê a cena e recompõe o tempo pelo timemap | lê `music`; o tempo continua vindo do timemap (D-MUSICA-Q) |
| `readWrittenKey` (ABC) e o leitor de armadura pelo `pitchpos` | `measures[0].key` (com `mode`) |
| `readMelodyXml` (`zywny_music`, lê o XML) | aposentado: notas e compassos de `music` + `midi` + `pitchpos`; `chg` de `directions`; cifras de `harmonies` |
| Cifra por texto desenhado | `harmonies[].root/kind/…` convertidos na grafia da EX01 pelo app |
| Isolate e worker devolvem `{bridge, attributes}` | devolvem o texto de `renderToMusicJson()` (uma chamada, sem layout) |

**Aceite:** o arquivo existe, cita os campos pela spec, registra a quebra do `getElementAttr` (dois argumentos → um), e o `CLAUDE.md` do
aprendizado (seção da regra) pode trocar a pendência do `readMelodyXml` por
"troca em andamento" com o link para este plano.

## Critérios de aceite do conjunto (portão)

1. `music.json` no `.vsb` e no JSON único, validado pelo schema, com a spec §2.9
   escrita e o histórico atualizado.
2. `renderToMusicJson` disponível em C, Dart e wasm, sem layout, nos ids da
   carga.
3. **Nenhuma** saída existente muda: `getMEI`, SVG, `timemap.json`, `midi.json`,
   `pitchpos.json` e `scene.json` de todo o corpus idênticos antes e depois
   (diff vazio); a paridade visual (`relatorio-paridade.md`) não muda.
4. O oráculo do M07: zero divergência nas fixtures; os 600 hinos medidos e as
   exceções explicadas.
5. O `score_bridge` lê o `music.json` e continua lendo `.vsb` antigos.
6. A nota para o host (M08) escrita.

## Fica fora

- **Layout, geometria e glifos:** nada disto entra no `music.json`.
- **Tempo da partitura notada (`q`/`ql`):** fica fora (D-MUSICA-Q); o app recompõe o tempo pelo timemap.
- **Altura, figura e ligadura por nota:** já estão no `pitchpos.json` e no
  `midi.json`; não se duplicam.
- **Dinâmica, pedal, cunha, ligadura de expressão, articulação:** G10
  (marcas de expressão), à parte.
- **Quiáltera com razões compostas** (quiáltera dentro de quiáltera): `tuplet`
  leva só a mais interna; o produto das razões fica para quando um caso real
  pedir (o aprendizado a deduz do timemap).
- **Ler MusicXML/MEI no app:** este plano existe para que **não** seja preciso.
  O MusicXML só é lido pelo importador do Verovio e pelo script oráculo do M07.
- **Notação mensural, tablatura, partes múltiplas além de uma `<part>` por
  pauta:** `parts` sai, mas o app só usa a primeira.

## Notas de execução

**2026-11-07: decisões do usuário (sem medição; o M01 ainda não foi executado)**

- **D-MUSICA-FORMA:** arquivo novo `music.json`, como proposto.
- **D-MUSICA-CIFRA:** `HarmData` ligado ao `Harm`, sem atributo MEI. A tabela lateral no `Doc` é o fallback, a confirmar no M01.
- **D-MUSICA-Q:** sem `q`/`ql` no `music.json`. A decisão foi aplicada a **todos** os campos de tempo (compasso, evento, `harmonies`, `directions`, `tempi`), não só às notas. A posição dentro do compasso continua no `tstamp` das cifras e das direções. O M01 não mede `scoreTime`.
- **M05, `getElementAttr`:** remover o segundo argumento, sem `@Deprecated`. **Quebra** para o `zywny`, que hoje chama com dois argumentos; a quebra vai na nota do M08.

**2026-11-08: M01 executado (medição, sem código de produção)**

Ferramentas: `compare/scripts/m01-medicoes.py` (oráculo em cima do MusicXML, lido
direto; `-t mei` e `-t vsb-json` do próprio Verovio; modo `--levantamento` lê
os 600 hinos e o corpus sem o Verovio) e `compare/out/m01/bench.c` (ligado à
`libverovio.so` de `verovio/tools/build-library`, recompilada no início do passo).
Saídas em `compare/out/m01/` (git-ignorado): `resumo.json`, `levantamento.json`,
`bench-hinos.txt`, `bench-600.txt`. Os 38 arquivos medidos são: 4 de
`test/music_reading/fixtures/src`, 5 de cursos e assets, 5 de `corpus/musicxml`
(`.mxl`), 20 hinos (001, 213, 248, 458 e 16 com casa ou anacruse) e 2 sintéticos
(twinkle com `<mode>` e troca de armadura no compasso 5, e a mesma sem `<mode>`).

**Fato → confirmado ou corrigido**

| Fato (M00) | Medido | Veredito |
| --- | --- | --- |
| Cena tem nós `measure`, `staff`, `layer`, `note`, `rest`, `chord`, `meterSig`, `keySig`, `harm`, `dir`, `tempo` com `id` | Classes na 1ª página de cada uma das 38 cenas (`vsb-json`) | Confirmado. `mordent`/`turn` não apareceram nas 38 (só `trill`, 1 vez); `graceGrp` não foi conferido. |
| `getElementAttr` acha `measure` `{n,left,right,metcon}`, `staff` `{n}`, `layer` `{n}`, não o `meterSig` | `bench attr` em `intro.mei`: `measure` → `{"n":"1i"}`, `staff` → `{"n":"1"}`, `layer` → `{"n":"1"}`, `meterSig` da cena `b12odbi7` → `not found` | Confirmado |
| `meterSig` do MEI tem `xml:id` diferente do nó da cena (cópia) | MEI `v1ombt22`, cena `b12odbi7` | Confirmado |
| `layer n` = voz do MusicXML | 38 arquivos, 20 hinos: 0 células divergentes. Nas 38 há 65 células divergentes, todas de pauta ou nota invisível, não de voz (ver ressalvas) | Confirmado |
| `1i`, `2i`... é o rótulo `n` da introdução; anacruse sai com `n="0"` e `metcon="false"` | `hymn-003`: `n="0" metcon="false" left="rptstart"`; `hymn-001`: `n="1i"`, `2i`, `3i` com `metcon="false"` | Confirmado |
| `Harm` guarda só texto, `type` e `tstamp` | Código (`ReadMusicXmlHarmony`, L2858). Cifras no MEI: `harm` = `staff`, `tstamp`, texto | Confirmado |
| Cifra estruturada se perde no importador | 30 553 `<harmony>` em 610 arquivos; 1173 de 1173 chegam ao MEI nos 38 | Confirmado (`harm` = `<harmony>` em número) |
| Compassos após barra final (`right="end"`) fora do timemap; hino 458 tem 9 | 458: 9 compassos após `right="end"`, 9 fora do timemap; nenhum outro dos 38 | Confirmado |
| Ordem de `RenderToBridgeJson` | `toolkit.cpp` L2094-L2121: scene, timemap, meta, midi, pitchpos, alternativas | Confirmado, com correção: pitchpos lê o layout (ver abaixo) |
| `midi.json`: `s`, `l`, `tied`, `orn` | Notas: `id,on,off,p,s,l,v` (+`tied` em 846); `orn` (booleano, `bridgewriter.cpp` L845) não apareceu nos 38 | Confirmado; `orn` sem caso medido |
| `pitchpos.json`: `pn`, `o`, `alt`, `dur`, `dots`, `key` | Chaves `t`, `co`, `key`, `pn`, `o`, `alt`, `loc`, `dur`, `dots` | Confirmado (faltavam `t`, `co`, `loc`, que não mudam nada) |
| `pitchpos` depende do layout da página 1 | `BridgePitchPosBuilder::Build` percorre `firstPage..lastPage` e usa `GetDrawingLoc`, do layout (`page.cpp` L282/L370/L698), não do desenho | **Corrigido** |
| Medido: ~50 ms por peça de 8 compassos e ~0,5 s por hino (600) | Ver "Custo" abaixo: twinkle 16 ms; 600 hinos 157 ms (mediana, in-process) | **Corrigido** |
| Caminhos: `../Hymn_Grabber` | Não existe a partir da raiz; o certo é `/home/mauricio/IdeaProjects/Hymn_Grabber` | **Corrigido** (L327, L412) |
| `folclore-1` é cifra de curso | 0 `<harmony>`; `folclore-2` tem `chg` (plano); cifras: `twinkle` (2 cópias) e `contrafato-1` | **Corrigido** |
| `ending` (regra 2) é o texto da casa | `ending@n` no MEI é o `@number` da casa, lista como `"2,3,4"`, não `"2. 3. e 4."`: o texto se perde no `<ending type="stop">` (`iomusxml.cpp` L428). 30 casas no MEI = 30 em `part` 1 | **Corrigido** (regra 2) |
| Pauta da nota = pauta onde o Verovio a guarda | Notas cruzadas: `@staff` do nó difere da pauta que o contém em 123 notas (`Clair_de_Lune`) e 2 (`Nocturne`) | **Corrigido** (regra 4): pauta = `@staff` do nó, senão a da pauta que o contém |
| `ReadMusicXmlHarmony` ~L2860 | L2858 | Corrigido (linha) |

**Perguntas do M01**

1. Corpus e hinos: 38 arquivos medidos (ver acima); os 610 arquivos do levantamento
   (600 hinos, 5 do corpus, 5 de cursos) em `levantamento.json`.
2. **Doc notado.**
   - `layer n` é o `<voice>` (default 1): `SelectLayer`, `iomusxml.cpp`.
   - **Id da parte:** em parte de uma pauta, o `staffDef` leva `xml:id` = id da `<part>` (twinkle: `staffDef xml:id="P1"`, com `label` e `instrDef` filhos). Em parte de várias pautas, o `staffGrp` leva o id (`staffGrp xml:id="P1" bar.thru="true"`, intro). As partes de todos os 38 arquivos foram achadas.
   - `KeySig::GetMode()` é `MODE_NONE` sem `<mode>` (`libmei/dist/atts_analytical.cpp` L197); o importador só lê `<mode>` no ramo `<fifths>` (`iomusxml.cpp` L4470). Nos 1302 `<key>` dos hinos não há `<mode>`; em `Clair_de_Lune`, 3 `<key>` sem `<mode>` → 0 `mode` no MEI; no sintético, `minor` na 1ª armadura e `major` no compasso 5 (`keySig mode`), e nenhum `mode` na versão sem `<mode>`.
   - `<ending>`: o `Ending` é pai do `Measure` (MEI `<ending n=...>` envolve os compassos), 30 de 30 nos 38 arquivos.
3. **Cifras e direções:**
   - Chegada: 1173 de 1173 `<harmony>` nos 38 arquivos viram `harm`; nos 610 arquivos, `root` em 30 553, `bass` em 7 070, `degree` em 2 420, `numeral` em 0 (sem caso real).
   - Tipos: 13 `kind` distintos no corpus e nos hinos, todos no `ConvertKindToText`; 0 perdidos. Fora do mapa, pelo código (comentários de `ConvertKindToText`): `none`, `other`, `neapolitan`, `italian`, `french`, `german`, `pedal`, `tristan`. Sem `kind@text` viram texto vazio; não aparecem no corpus medido.
   - `kind@text` é usado em 14 852 de 30 553 cifras (49%), e é ele que vira o texto do `Harm`.
   - Direções: 137 `<words>` não vazios nos 38 arquivos, **todos** aparecem em algum lugar do MEI (0 perdidos). Mas só 39 viram `dir`: os de direção com `<sound tempo>`/`<metronome>` vão para `tempo` e os com dinâmica para `dynam`. Formatação (`rend`): 65 direções (`Clair_de_Lune` 63, `Maple_Leaf` 2). Nos 600 hinos há 21 direções com `<words>`, nenhuma com várias `<words>`, nenhuma com formatação, nenhuma com tempo ou dinâmica. `chg` (folclore-2) sai como `dir`. Várias `<words>` numa direção, quando houver, viram `Text` seguidos, sem separador (`TextRendition`, L705).
4. **Custo** (`bench`, cada operação numa carga nova; mediana):

   | Operação | 20 hinos (N=3) | 600 hinos (N=1) | Twinkle 8 compassos (N=5) |
   | --- | --- | --- | --- |
   | `loadData` | 37,9 ms | 38,3 ms | 9,0 ms |
   | `renderToTimemap` (1ª / 2ª chamada) | 39,6 / 2,6 ms | 44,3 / 2,8 ms | 5,8 ms |
   | `renderToMIDI` (1ª / 2ª chamada) | 36,0 / 1,0 ms | 39,1 / 1,1 ms | 5,7 ms |
   | `redoLayout` (só layout) | 22,0 ms | 19,4 ms | 4,0 ms |
   | `renderToSVG` de todas as páginas | 30,5 ms | 27,8 ms | 3,3 ms |
   | `renderToBridgeJson` (caminho atual) | 181,0 ms | 156,6 ms (média 174,7; p90 266,8; máx 687,8) | 16,3 ms |
   | provisório `RenderToMusicJson` (timemap + midi + layout, uma carga) | 60,0 ms | 62,6 ms (média 65,5; p90 93,7) | 10,0 ms |

   Na CLI (processo inteiro, mínimo de 3), o `--no-vsb-alternates` mostra quanto as alternativas pesam: 001 149 → 95 ms; 213 246 → 125 ms; 031 338 → 158 ms; 248 213 → 207 ms (sem casas; quase nenhuma diferença).

   - **Alvo ≤ 50 ms não atingido: 63 ms de mediana.** Quase tudo é a primeira chamada de timemap ou MIDI na carga: `SetMidiDoc()` reexporta o MEI e o reimporta num `Doc` expandido (`toolkit.cpp` L288-L310), ~37 ms, cacheado depois (2ª chamada ~3 ms). O layout (~20 ms) é o que o `pitchpos` precisa. Para o M05/M07 vale a comparação 63 ms × 157 ms; se o alvo de 50 ms continua valendo, é a rever no M07 (o custo de `SetMidiDoc` é a alavanca).
   - **Pitchpos sem desenho:** é possível pela leitura de código (o layout que o `loc` usa é `Page::LayOut`, sem `DeviceContext`). Não dá para provar empiricamente agora: não há entrada pública que faça layout e devolva o `pitchpos` sem desenhar. O M05 tem de provar que o `pitchpos` da rota sem desenho é igual ao da rota com desenho. O `loc` **não** sai `null`.
   - **Corrigido:** "~0,5 s por hino" era o caminho do app; in-process na C API a mediana é 157 ms. O app (isolate, worker, JSON) acrescenta o que este número não mede.

5. **Fallback do D-MUSICA-CIFRA:** `Harm` é classe escrita à mão (`include/vrv/harm.h`); o libmei só gera as classes de atributo (`AttLang`, `AttNNumberLike`). Um campo novo (ponteiro para `HarmData`) **não** mexe no libmei. Cuidado: `Harm::Clone()` é `new Harm(*this)` (cópia rasa), então o ponteiro deve ser `std::shared_ptr<const HarmData>` ou a tabela lateral deve existir. Se o M03/M04 preferir a tabela lateral: `include/vrv/doc.h`, junto de `pugi::xml_document m_header` (L601); limpa em `Doc::Reset()` (`src/doc.cpp` L110); preenchida em `MusicXmlInput::ReadMusicXmlHarmony` (`src/iomusxml.cpp` L2858), pelo `m_doc`; lida pelo `ReadBridgeMusic`, pelo id notado.

**Decisões do usuário, registradas**

- **D-MUSICA-FORMA:** mantida, arquivo novo `music.json`.
- **D-MUSICA-CIFRA:** mantida. O caminho principal (`HarmData` por ponteiro no `Harm`) é viável sem libmei; a tabela lateral não é necessária. Ressalva: o ponteiro é `shared_ptr` por causa de `Clone()`.
- **D-MUSICA-Q:** mantida. Nada medido sobre `scoreTime` (o próprio D-MUSICA-Q diz que o M01 não mede).

**Ressalvas para o M02/M03/M07 (não bloqueiam; não são decisão de usuário)**

- **Notas invisíveis** (`print-object="no"`) não entram no `Doc`, portanto não no timemap nem no `music.json`: Satie 10 pausas invisíveis = 10 células divergentes (explicado 100%); Chopin 14 e Debussy 113 notas invisíveis, só em parte explicado. O M07 decide como o oráculo trata isso.
- **Notas cruzadas:** a pauta de um evento vem do `@staff` do nó (regra 4 corrigida).
- **`time symbol`** (`common`, `cut`): nenhum no corpus medido. O campo `sym` não tem caso real; o M02 cria um vetor sintético.
- **`numeral`**: 0 em 610 arquivos; o caminho existe (`ReadMusicXmlHarmony`) mas sem amostra. O M07 precisa de uma fixture.
- **`harm@staff`** varia (`1` em 1018 cifras, `2` em 86 nos 20 hinos). Não usar o `staff` do `harm` como pauta do acorde sem checar.
- **`orn`** nunca apareceu nos 38 arquivos.

**Passo M01:** concluído com ressalva (ver acima: as células divergentes de Chopin e Debussy só estão parcialmente explicadas; o M07 é o lugar de fechar).

**2026-11-08: M02 executado (especificação, schema e fixture; sem código de produção)**

Entregas: §2.9 em `docs/formato/especificacao-v1.md` (com a regra 1 a 9 deste
arquivo corrigidas, §2.1, §2.2, §9 e histórico); `$defs/musicDocument` e
auxiliares em `docs/formato/schema-v1.json`; fixture em `docs/formato/musica/`
(`m02-entrada.musicxml`, sintético, duas partes, seis compassos, e
`m02-esperado.json`). Conferência: `compare/out/m02/check_m02.py` (fora do
repositório, em `compare/out/`), com `verovio -x 42 -t mei` para os ids.

**Aceite**

| Critério | Resultado |
| --- | --- |
| Schema valida a fixture | `jsonschema` 4.10.3, Draft 2020-12: `musicDocument` aceita `m02-esperado.json`; a raiz (`oneOf`) tem 0 erros; os três exemplos existentes (`exemplo-minimo`, `exemplo-pitchpos`, `exemplo-alternates`) continuam válidos. Sete casos negativos são rejeitados (pausa com `chord`, `grace` inválido, `version` 2, `sym` inválido, `tuplet` sem `numbase`, harmonia sem `text`, casa com campo extra). |
| Cobertura da fixture | tabela em §2.9 ("Cobertura"), item a item: casas (compassos 1 a 3), anacruse (0), armadura (3), fórmula (4 e 5), apojatura (1), acciaccatura (2), quiáltera (1), acorde (1), duas camadas (1), cifra com `kind`, `degree` e baixo (3), `chg` (4). |
| Confronto com o MusicXML | `check_m02.py`: eventos por (compasso, pauta, camada) com `t`, `chord`, `grace`, `tuplet`: 42 eventos, 0 divergências; fórmula e armadura vigentes em cada compasso: 0 divergências; 42 eventos na pauta e na camada que o MEI declara. |
| Confronto com o MEI | ids dos compassos e eventos, casas, barras (`left`/`right`), harmonias (texto, pauta, `tstamp`), ornamento (`startid`), direção e andamento: 0 divergências. |
| JSON | `json.loads` em `m02-esperado.json` e `schema-v1.json`: ok. |

**Desvios e correções em relação ao M00**

- **Caminho do schema.** O M00 pede `docs/formato/schema/` (`music.schema.json`),
  mas o schema do formato é um único arquivo, `docs/formato/schema-v1.json`, com um
  `$defs` por documento (`midiDocument`, `pitchposDocument`, `alternatesDocument`).
  Acrescentado lá, no mesmo molde; não se criou pasta nova.
- **`version`.** O `music.json` leva `"version": 1`, como no exemplo do M00. É o
  único documento do pacote que repete o campo (`midi` e `pitchpos` não o têm).
  Mantido, sem efeito sobre o leitor.
- **Regra 3 (fórmula e armadura).** A frase "um compasso novo só repete o que mudou
  se o leitor comparar com o anterior" era ambígua. A spec fixa: todo compasso traz
  `meter` e `key` com os valores vigentes no começo dele.
- **Regra 4 (eventos).** O exemplo do M00 omitia `chord`, `grace` e `tuplet` na pausa.
  A spec fixa os cinco campos em todo evento (em pausa, `chord` `null`, `grace` `false`).
- **Regra 4 (pauta de nota cruzada).** Fixado: a camada é a de origem (`layer n`); a
  pauta do evento é o `@staff` do nó (ou a que o contém). O evento aparece na pauta
  do nó, com a camada de origem.
- **Regra 2 (`ending.n`).** O valor é o `@number` como o MEI o grava, com os espaços
  da fonte: a fixture produz `"2, 3"`; o M01 viu `"2,3,4"` nas peças reais. A spec
  manda o leitor separar por vírgula e tirar os espaços (R5).
- **Pauta da cifra (não registrada no M01).** O M01 dizia só "não usar o `staff` do
  `harm` sem checar". Medido agora: nenhum `<harmony>` do corpus traz `<staff>`, e
  em todos os arquivos com cifra do M01 o `harm@staff` é a pauta única da parte onde
  está o `<harmony>`. A spec adota essa regra (§2.9, regra 7); a parte de duas pautas
  fica como ressalva R2 (só no caso sintético).
- **Pauta da direção.** A spec segue o importador (`ReadMusicXmlDirection`): o
  `<staff>` da `<direction>`, senão a primeira pauta da parte. Conferido em contagem
  nos 20 hinos com `<words>` (contagem total por arquivo, 0 divergências); o M07
  confere pauta por pauta.
- **Trinado em acorde.** Novo fato: o `startid` do trinado de uma nota de acorde
  aponta para o `chord`, não para a nota (medido na fixture). Está na regra 6.
- **Numeração de `index`.** `index` é 0-based (como no exemplo do M00); a
  "ocorrência" do M00 é `index + 1`. Escrito na regra 1.

**Fatos novos medidos (M02)**

- **R1 (premissa refutada no M07):** à primeira leitura, parecia que o `grace` saía
  trocado no importador do MusicXML: `slash="yes"` (acciaccatura) virando `unacc`, e a
  ausência de barra virando `acc` (`iomusxml.cpp` L3310-3345). O M07 mostrou que o
  importador grava exatamente o valor do MEI, e o desenho sempre esteve certo (a barra
  vem em `stem.mod="1slash"`). A spec segue o valor do MEI, como o M00 pede (`@grace`),
  e a alternativa de corrigir o importador (que mudaria o `getMEI` do corpus) não se
  colocou.
- `ending.n` com espaço (`"2, 3"`) passa do `@number` sem normalização.
- Os ids da fixture vêm de `verovio -x 42` (binário do fork, `6.3.0-8aabb53-dirty`).
  O M03 precisa reproduzi-los para o teste do `ReadBridgeMusic`.

**Ressalvas para o M03 e o M07 (não bloqueiam o M02)**

- R2: pauta da cifra em parte de duas pautas, só no caso sintético.
- R3: notas invisíveis (`print-object="no"`), ainda fora do timemap e de `music.json`.
- R4: `numeral` sem caso real; fixture não cobre (M07).

Os desvios e os números do M07 entram aqui quando o passo rodar.

**2026-11-08: M03 executado (C++: `ReadBridgeMusic`, `music.json` no `.vsb` e no JSON único)**

Entregas: `verovio/include/vrv/bridgemusic.h` e `verovio/src/bridgemusic.cpp`
(`struct BridgeMusic`; `ReadBridgeMusic(Doc&)`, que só lê o `Doc`);
`BridgeWriter::WriteMusic` (`bridgewriter.h/.cpp`), com `harmonies` e `directions`
vazias até o M04 (o schema exige as chaves); `WriteManifest` ganhou `hasMusic` e
`WriteSingleJson` ganhou `music` (depois de `pitchpos`); `Toolkit::RenderToBridgeJson`
e `RenderToBridgeFile` (`toolkit.cpp`) leem o `music` logo depois do `pitchpos` e
antes dos alternativos (que mudam o `Doc`). O `.vsb` ganha `music.json` e
`manifest.files.music`.

Linha de base e aceite (saídas git-ignoradas em `compare/out/m03-base/` e
`compare/out/m03-after/`):

- **Base** antes de editar C++: 72 arquivos, `corpus/mei` e `corpus/musicxml`, mais
  `corpus/fantasma`, `ligaduras`, `repeticoes`, `sumico` e o fixture do M02 (cobertura
  extra). Para cada um: getMEI, SVG de todas as páginas e os JSON do pacote. Duas
  rodadas do binário anterior dão o mesmo resultado depois de normalizar `isodate`
  do MEI e a string de versão (`6.3.0-<hash>[-dirty]`, que muda com o working tree).
- **Depois**: 578 arquivos comparados (getMEI, SVG, `timemap`, `midi`, `pitchpos`,
  `scene`, `glyphs`, `alternates`, `meta`): **0 diferenças**. O `manifest.json`
  muda em 72 de 72 pacotes, e a única diferença é a entrada `music`.
- **Build**: `cmake ../cmake && make -j4` sem aviso novo (os 6 avisos de
  `stl_algobase.h` já existiam na base).
- **Fixture** (`m02-entrada.musicxml`, `verovio -x 42`): `music.json` igual por valor a
  `m02-esperado.json` em tudo, **exceto `harmonies` e `directions`**, que saem vazias
  (são o M04). O aceite do M03 fala em "igual"; isso não se alcança sem o M04.
- **Corpus** (72 `music.json`), conferido por scripts independentes:
  - schema `$defs/musicDocument`: 72 de 72 válidos;
  - compassos, notas, pausas, pausas de compasso e espaços contra o MEI notado (sem o
    `<incip>` do cabeçalho, que é descrição da obra, não partitura): 0 divergências;
  - partes contra `<score-part>` dos 6 MusicXML: 0 divergências (ids e nomes);
  - compasso, armadura e modo contra o `<time>`, `<key>` e `<mode>` do MusicXML: 0
    divergências em 330 compassos;
  - casas contra o `<ending>` do MEI: 1037 compassos, 36 dentro de casa, 0 divergências;
  - 14 733 eventos (acorde, apojatura, quiáltera, pauta e camada) contra o MEI: 0
    divergências;
  - 140 andamentos e os 5 ornamentos com `@startid` contra o MEI: 0 divergências.
    Uma comparação mostrou um espaço inicial no texto de andamento do Clair de Lune
    (`" morendo jusqu'à la fin"`); o texto é o `<rend>` do MEI, e o oráculo é que o
    aparava. `music.json` guarda o texto como vem.

Pontos técnicos para o M04:

- Depois do layout, o `Doc` está em *cast-off*: os compassos saem do `Score` e vão
  para `Page`/`System`, e o `scoreDef` inicial fica no `Score`, que a varredura a
  partir do `Doc` não alcança. Por isso `ReadBridgeMusic` lê o `scoreDef` inicial por
  `Doc::GetFirstScoreDef()` e varre o resto a partir do `Doc` (os compassos estão nas
  páginas, e os `scoreDef` de seção também).
- Depois do cast-off, a casa não é ancestral do compasso: o `ending` sai de
  `Measure::GetDrawingEnding()`, que `PrepareMilestonesFunctor` preenche no
  carregamento (antes do cast-off).
- Armadura e fórmula em cada compasso: a regra 3 pede os valores do começo do
  compasso. Mudanças no começo (camada antes de qualquer evento) valem para o
  compasso; as do meio valem a partir do evento. O M04 deve ler `<harmony>` e
  `<direction>` no mesmo percurso (são filhos do compasso, nas páginas).
- `multiRest` não aparece no corpus e não gera evento.

Desvios e ressalvas:

- **Spec (§2.9)**: acrescentadas notas de implementação às regras 4, 5 e 6 (camada sem
  nota; partes; trinado só com `@tstamp`). Nenhuma regra normativa mudou.
- **R-PARTES (decisão do usuário; resolvida em R2, ver o fim deste arquivo)**: o MusicXML sai certo, com uma entrada por
  `<part>`. Os 5 MEI de `corpus/mei/` têm pauta dupla num `staffGrp` sem grupo de
  parte, e saem com 2 partes cada. A regra 5 manda uma entrada só nesse caso, mas a
  estrutura não distingue esse MEI de duas partes de uma pauta cada num MusicXML (que
  o fixture do M02 precisa). Mantive uma entrada por filho do `staffGrp` externo.
- **R-TRINADO (decisão do usuário; resolvida em R2)**: 12 trinados do Scarlatti têm só `@tstamp`, sem
  `@startid`. O schema exige `startid`, então ficam fora de `ornaments` (aviso no log:
  `music: trill ... has no @startid`).
- **R1 (refutada no M07)**: a premissa de que o `grace` sai trocado não se confirmou.
  O `music.json` segue o MEI (confirmado nos 14 733 eventos). O importador não foi tocado.
- **R-SCORE_BRIDGE**: o `score_bridge` não está neste repositório. O `compare/pubspec.yaml`
  aponta para `/home/mauricio/IdeaProjects/zywny/score_bridge`, que não existe (há só
  `build/unit_test_assets/packages/score_bridge/fonts`). Não rodei `flutter test` e não
  li o parser Dart: o campo extra `music` no pacote não foi verificado do lado do leitor.
  Fechar quando o pacote estiver disponível.
- **Camadas vazias**: 12 (2 no Clair de Lune, 10 na Gymnopédie), saem com `"events": []`.

**2026-11-08: M04 executado (C++: cifras e direções no `music.json`)**

Entregas:

- `verovio/include/vrv/harm.h`: `HarmDegree` e `HarmData` (a estrutura da `<harmony>`) e `Harm::SetHarmData`/`GetHarmData`, com `std::shared_ptr<const HarmData>` (sobrevive a `Harm::Clone()`, que é cópia rasa). Sem atributo MEI. A tabela lateral do `Doc` não foi preciso (D-MUSICA-CIFRA).
- `MusicXmlInput::ReadMusicXmlHarmony` (`iomusxml.cpp`) preenche o `HarmData` ao lado do texto, que não mudou. Só o importador MusicXML preenche: o `harm` de MEI fica sem.
- `verovio/include/vrv/bridgemusic.h` e `src/bridgemusic.cpp`: `BridgeMusicHarmony`, `BridgeMusicDirection`; `ReadBridgeMusic` acrescenta `HARM` e `DIR` ao percurso que já fazia (ordem do documento, depois do compasso). `bridgewriter.cpp`: `AppendHarmony`/`AppendDirection` em `WriteMusic`.
- Onde o percurso acha as cifras e as direções: `HARM` e `DIR` são filhos do `Measure` também depois do cast-off (como `TEMPO`), então o percurso sobre o `Doc` alcança as páginas. Nada de `View`, `getMEI` nem SVG mudou.

Desvios em relação ao M00:

- `staff` de um `harm` sem `@staff` (MEI que não o traz): a primeira pauta do compasso, porque o schema exige inteiro. Não estava no M00; a spec (§2.9, regra 7) registra.
- O `<figured-bass>` do MusicXML também vira `Harm` no importador (com `Fb`, sem texto de cifra). Não é `<harmony>`: fica fora de `harmonies`. Medido no caso sintético: o MEI tem o `harm` com `fb`, e `harmonies` tem só as cifras.
- Cifra sem `@tstamp`, sem texto ou fora de compasso, e direção fora de compasso: saem com aviso, como o trinado sem `@startid` (R-TRINADO). Nenhum caso no corpus.
- Direção sem texto (coda, segno) não entra em `directions`.
- A reavaliação de R1 ("premissa refutada") foi feita no M07, ver "Notas de execução", M07. Este passo não tocou `grace`.

Linha de base e aceite (saídas em `compare/out/m04-base/` e `compare/out/m04-new/`, git-ignoradas):

- Linha de base com o binário do HEAD `680cb1d`, antes de editar: 72 pacotes (lista do M03), 0 falhas. Depois: 72 pacotes, 0 falhas.
- Comparação arquivo a arquivo (650 arquivos: `getmei`, páginas SVG e os JSON do pacote): **só `vsb/music.json` difere, em 10 pacotes**. `manifest.json` igual em 72 de 72. Dentro de `music.json`, só `harmonies` e `directions` mudam: os demais campos são iguais em 72 de 72.
  - `harmonies`: `h010` 0 → 52, `h056` 0 → 45, fixture 0 → 2.
  - `directions`: Chopin Étude 0 → 29, Mazurka 0 → 10, Nocturne 0 → 21, Clair de Lune 0 → 5, Gymnopédie 0 → 1, r08 0 → 2, r09 0 → 4, fixture 0 → 1.
  - `getmei`, SVG, `timemap`, `midi`, `pitchpos`, `scene`, `glyphs`, `alternates` e `meta`: nenhuma diferença.
- Fixture: o bloco `music` inteiro é igual por valor a `m02-esperado.json` (os 7 campos). O esperado não precisou de correção.
- Conferência independente (script de fora do repositório): os 99 `<harmony>` dos MusicXML do corpus viram 99 `harmonies`; a estrutura (raiz, alteração, `kind`, `kind@text`, baixo, graus) confere como multiconjunto; ids, texto, pauta, `tstamp` e compasso batem com o `getmei.mei` do mesmo binário (72 pacotes, 0 divergências); os textos de `<words>` dos MusicXML batem com `directions` pela regra do importador (multiconjunto, 34 textos); os `music.json` de origem MEI não têm campo estruturado.
- Schema: 72 de 72 `music.json` válidos em `$defs/musicDocument`.
- Texto desenhado: a fixture desenha `CMaj7`, `chg` e `G7(` + U+EA64 (glifo de bemol da fonte Leipzig) + `9)/B`; `harmonies` traz `G7(♭9)/B` com U+266D, o mesmo bemol.
- Caso sintético fora do corpus (numeral com alteração, `<figured-bass>`, `<words>` extra): numeral `{"root": "V", "alter": -1}`, `root` e `rootAlter` `null`, `text` `V♭7`; o figured bass fica fora.
- Build: sem aviso novo (os 6 avisos de `stl_algobase.h` já existiam).

Ressalvas abertas:

- **R2** (pauta de cifra em parte de duas pautas): sem caso no corpus.
- **R4** (`numeral`): só o caso sintético acima; o M07 traz fixture real.
- `root-alter`, `bass-alter` e `degree-alter` são lidos com `as_int`: uma alteração fracionária (quarto de tom) sai truncada. Nenhuma no corpus (medido: todos inteiros).
- `degree-type` sai como vem (o MusicXML exige o elemento).
- `<words>` com quebra de linha perde a quebra em `text` (a §2.9 manda concatenar sem separador, como `TextRendition` desenha).

Passo M04: concluído com ressalva (R2, R4 e a alteração fracionária, acima).

**2026-11-08: M05 executado (API: `renderToMusicJson`, C, Dart e `getElementAttr`)**

Entregas:

- `Toolkit::RenderToMusicJson()` e `RenderToMusicJsonFile()` (`toolkit.h/.cpp`): `timemap`
  (mesmas opções de `RenderToBridgeJson`), `RenderMidiEventLog`, `RenderPitchPos(..., withLayout)`
  e `ReadBridgeMusic`. Sem `RenderPagesToBridge` e sem `Select`. `BridgeWriter::WriteMusicJson`
  monta `{timemap, midi, pitchpos, music}`, com as mesmas regras de omissão do JSON único.
- `BridgePitchPosBuilder::Build(..., withLayout)` e `BridgePitchPos::layout`
  (`bridgepitchpos.h/.cpp`). Com `layout` falso, `loc` e `acc` saem `null` (`WritePitchPos`).
  O `.vsb` e o JSON único seguem com `layout` verdadeiro: a saída deles não muda.
- `Toolkit::m_layoutAtLoad`, ligado no `LoadData` no ramo do corte (`--breaks` diferente de
  `none`). O MEI com `<pages>` cai em `none` (`LAYOUT_DONE`), então também fica sem.
- C: `vrvToolkit_renderToMusicJson(tk)` (`tools/c_wrapper.h/.cpp`); `emscripten/exports.txt`:
  `_vrvToolkit_renderToMusicJson`.
- Dart: `VerovioToolkit.renderToMusicJson()` (`verovio_toolkit.dart`, `verovio_bindings.dart`).
  `dart analyze lib test example`: sem problemas; `dart format`: limpo.
- Spec: §2.8 (regra "Sem layout"), §2.10 (novo: `renderToMusicJson`), `schema-v1.json`
  (`loc` e `acc` aceitam `null`; `$defs/musicJsonDocument`) e a linha de histórico.

**`pitchpos` sem layout: a prova (experimento temporário, removido antes do commit)**

O M01 supunha que `loc` precisava do layout de página. A medição corrige isso: o
carregamento já faz o trabalho, para todo documento que é cortado nele.

- Com corte no carregamento, **nenhuma** chamada de layout é necessária. Montado logo após o
  `LoadData`, sem `Page::LayOut`, o `pitchpos` (`co`, `key`, `acc`, `alt`, `pn`, `o`, `loc`,
  `dur`, `dots`) bate com a linha de base com layout em `--breaks` auto nos 72 arquivos do
  corpus, e em line, smart e encoded em 5 arquivos (matriz: Mazurka, f04, f02, Clair de
  Lune e r06; em `line` a Mazurka não tem comparação, o HEAD cai nela). O `sh` é o único campo que depende do MIDI, e o experimento não o montava.
  Os 72 arquivos com auto foram confirmados de novo pelo harness (`ids`), na chamada final.
- Sem corte (`--breaks none`): o `loc` calculado sem layout estaria errado em 859 de 896
  notas da Mazurka e 1647 de 1720 do Clair de Lune; o `acc` em 120 e 213 eventos. Por isso
  saem `null`. Nos mesmos casos, os demais campos (`t`, `co`, `key`, `alt`, `pn`, `o`, `dur`,
  `dots`) continuam iguais: 72 de 72 arquivos, sem nenhuma diferença fora de `loc` e `acc`.
- MEI page-based (`-t mei-pb`, `<pages>`, `LAYOUT_DONE`), caso de `f04-cross-staff`: `loc`
  diferente em 5 de 6 notas. Com o layout completo (controle), bate. Um passe só de
  `pitchpos` (`LayOutPitchPos`, sem o alinhamento horizontal) derrubou o processo (SIGSEGV),
  por isso não foi adotado.
- **Decisão de implementação (resolvida pelo usuário em 2026-11-08: montar o layout, ver M05-P no fim):** quando o corte não aconteceu no
  carregamento, `loc` e `acc` saem `null`. A regra do plano cobria só `loc`; estendi a `acc`,
  porque um `acc` ausente sairia como "nenhum acidental em vigor", que é dado errado sem aviso.
  A alternativa é montar o layout nesses casos. Isso mudaria o "sem layout" da chamada e
  precisa de decisão à parte.

**Ids e estado (harness C contra `libverovio.so` recompilada; `compare/out/m05-base` e scripts fora do repositório)**

- Ordem nos dois sentidos, na mesma carga (semente 42): `timemap`, `midi`, `pitchpos` e
  `music` de `renderToMusicJson` são iguais aos de `renderToBridgeJson` em 72 de 72 arquivos
  (JSON parseado).
- Chamada nova contra os `vsb/*.json` da linha de base (CLI, `-x 42`): 72 de 72.
- Estado: `getMEI` e `renderToTimemap` iguais antes e depois de `renderToMusicJson` em 72 de 72.
  O SVG "depois" é igual ao SVG de um controle sem a chamada nova em 72 de 72. Entre um SVG e
  o seguinte já difere em 9 arquivos, porque cada render gera `id` de `tspan` novos (acontece
  sem a chamada nova também; é anterior ao M05).

**Aceite de não mudança (ordem 4 do M05)**

- Linha de base com o binário de HEAD `386ee76`, **com `-x 42`**. Sem semente, cada processo sorteia
  os `xml:id` gerados (o `scene.json` e o SVG mudam de uma rodada para outra; a mesma causa
  está no `Object::SeedID`). O M02 a M04 já usavam `-x 42`; o M07 deve usar o mesmo.
- Depois: 72 pacotes, 0 falhas. Comparação de 722 arquivos (getMEI, SVG de cada página e os JSON do
  pacote, com o `.vsb` descompactado, já que o zip tem data): **0 diferenças**.
- Build: `tools` sem aviso novo (os 6 de `stl_algobase.h` continuam os mesmos). A `build-library`
  foi reconfigurada (`cmake -S ../cmake`), porque o `libverovio.so` anterior não tinha o
  `bridgemusic.cpp` (o glob é avaliado na configuração).

**Custo: `renderToBridgeJson` contra `renderToMusicJson` (20 hinos da lista do M01, 7 cargas novas por hino e operação)**

| Hino | `renderToBridgeJson` (ms, mediana) | `renderToMusicJson` (ms, mediana) |
| --- | --- | --- |
| 001 | 115,5 | 36,5 |
| 213 | 206,4 | 37,8 |
| 248 | 171,9 | 59,7 |
| 458 | 142,5 | 25,3 |

Os 20 hinos (mediana das medianas; média das médias): `renderToBridgeJson` **175,3** ms (177,2;
faixa 102 a 303); `renderToMusicJson` **43,2** ms (44,1; faixa 25 a 60). Razão de ~4x.

- Alvo ≤ 50 ms: **atingido na mediana** (43 ms), **não em todos os hinos**: 15 de 20 ficam ≤ 50 ms;
  passam 248 (60), 036 (57), 011 (57), 033 (55) e 031 (51).
- Motivo medido: a primeira chamada de `renderToTimemap` na carga (que dispara `SetMidiDoc`, o
  reexport e a reimportação do MEI expandido) é 37,7 ms de mediana; o resto da chamada
  (MIDI, `pitchpos`, `music`) leva ~4,5 ms. Não foi otimizado (fora do passo). A alavanca é o
  `SetMidiDoc`; rever no M07.
- Medição feita com o `libverovio.so` deste passo, no mesmo ambiente das duas chamadas. O número
  do M01 (157 ms de `renderToBridgeJson`) foi tirado em outra sessão; não é comparável diretamente.

**Quebras e ressalvas**

- **`getElementAttr`**: a função Dart passa a ter um argumento (`getElementAttr(String xmlId)`,
  batendo com `vrvToolkit_getElementAttr(tk, xmlId)`). **Quebra** para quem chama com dois
  (o `zywny`, que o M08 registra). Chamadores neste repositório: nenhum (`grep -rn getElementAttr
  verovio/bindings compare`; `score_bridge` não está aqui, ver R-SCORE_BRIDGE).
- **Defeito pré-existente (fora do escopo, não tocado)**: o HEAD (`386ee76`) derruba com SIGSEGV o
  `-t vsb` de `Chopin_Mazurka_Op6_No1.mei` com `--breaks line`, e de seu MEI page-based
  (`-t mei-pb`). A chamada nova não passa por esse caminho de layout no MEI page-based (sem corte,
  `loc` sai `null`), e não foi testada com `--breaks line` na Mazurka.
- **R-PARTES, R-TRINADO e R1 (`grace`)**: nada mudou neste passo.
- **Ressalva do M06**: `score_bridge` não está neste repositório; o parser de `renderToMusicJson` (raiz
  com `timemap`/`midi`/`pitchpos`/`music` opcionais, `loc` e `acc` `null` sem corte) não foi
  testado aqui.

**Passo M05:** concluído com ressalva (ver acima: alvo de 50 ms atingido na mediana e não em 5 de 20 hinos).
**Corrigido em M05-P** (2026-11-08, ver o fim deste arquivo): `loc` e `acc` deixam de sair `null` sem corte.

**2026-11-08: M07 executado (oráculo, varredura e vetores)**

Entregas:

- `compare/scripts/music_oracle.py`, com três subcomandos: `verificar FONTE MUSIC.json`
  (relatório em JSON), `varredura --out compare/out/m07 --jobs 4` e
  `vetores --out-dir docs/formato/musica/vetores`.
- `docs/formato/musica/vetores/`: oito `music.json` (`m02`, `ode`, `intro`, `menor`,
  `recusa`, `twinkle`, `contrafato-1`, `folclore-2`) e `vetores.json` (índice, com o
  `fonte_sha256` de cada fonte). Gerados por `-x 42 -t vsb-json` e gravados só com zero
  divergência. `m02.music.json` é igual por valor a `m02-esperado.json`. As fontes do
  aprendizado ficam lá (só leitura); o índice guarda o caminho relativo a
  `zywny-aprendizado` e o hash.
- Sem mudança no exportador, no `grace` nem no Dart. O binário `verovio/tools/verovio`
  estava em `386ee76-dirty` (de antes do M05); foi recompilado (`cmake ../cmake && make
  -j4`), e a varredura usou `ec8a8a2`.

Como o oráculo lê a fonte:

- **MusicXML**: lido direto (ElementTree), sem o Verovio. As regras de tradução seguem o
  importador (`iomusxml.cpp`); as tabelas de texto (sufixo de `kind`, símbolos de
  alteração, graus que recebem `add`, figuras do andamento) são **extraídas do fonte do
  importador**, não digitadas. Isso mede a exportação, não um dicionário próprio de cifras.
- **Comportamentos do importador que o oráculo precisa modelar** (sem eles haveria
  divergências que não são da partitura): espaços `s` de preenchimento (`FillSpace`,
  L559, também em `<forward>`); a camada de cada nota é a de `SelectLayer` (L470: a 1ª
  nota desde o começo do compasso ou o último `<backup>`; a pauta do evento continua a
  do nó); o colchete de quiáltera (`ReadMusicXmlTupletStart`, L4325), com a nota de acorde
  herdando a quiáltera do início do acorde; o texto de andamento com metrônomo
  (`PrintMetronome`, L784); `<words>` que começa por cresc/dim/decresc vira dinâmica, e
  `<words>` vazio não vira `dir`. O `tuplet` de um `s` de preenchimento não é conferido
  (vem do contêiner aberto no importador).
- **MEI** (corpus nativo, sem MusicXML de origem): conferência parcial, sobre o MEI
  exportado pelo Verovio (`<body>`; o `<incip>` do cabeçalho fica fora). Confere-se
  compasso (`n`, barras, casa), eventos (tipo, acorde, apojatura, quiáltera, incluindo
  `tupletSpan`), cifras (texto), direções (texto), andamentos e ornamentos. **Não**
  conferidos: partes (R-PARTES), fórmula, armadura e a estrutura da cifra (só se confirma
  que vem `null`).
- **Não tocados**: o timemap define. Um compasso não tocado é o que o id notado não tem
  no timemap; os que não vêm depois de uma barra final são divergência.

Resultados (`varredura`, 617 fontes, 0 erros do Verovio; saída em `compare/out/m07/`,
git-ignorada, com `resumo.json`, `relatorios/` e `music/`):

| Grupo | Arquivos | Compassos | Eventos | Camadas | Cifras | Direções | Andamentos | Ornamentos | Divergências | Causa |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Fixture do repositório (`m02`) | 1 | 6 | 42 | 19 | 2 | 1 | 1 | 1 | 0 | — |
| Fixtures do aprendizado (`ode`, `intro`, `menor`, `recusa`) | 4 | 25 | 117 | 52 | 0 | 0 | 4 | 1 | 0 | — |
| Cursos com cifra (`twinkle`, `contrafato-1`, `folclore-2`) | 3 | 24 | 86 | 24 | 27 | 4 | 0 | 0 | 0 | — |
| Corpus MusicXML (`.mxl`) | 5 | 324 | 6 364 | 873 | 0 | 27 | 101 | 2 | 16 | R3 (16) |
| Corpus MEI (`.mei`, conferência parcial) | 5 | 291 | 4 704 | 668 | — | 39 | 1 | 2 | 0 | R-TRINADO (12, fora de `ornaments`, contados à parte) |
| Hinos (`musicxml_simplificado`, 600 arquivos) | 600 | 19 730 | 141 214 | 39 522 | 30 512 | 21 | 599 | 0 | **0** | 2 arredondamentos de 6 algarismos (não contam) |

Os 601 itens da pasta dos hinos são 600 `.musicxml` e `_avisos.log` (aviso de
simplificação, um registro: `220: 8 sílabas na pauta de fá ficaram de fora`). O
`_avisos.log` não é hino e não entra na conta.

Não tocados nos hinos: 34 compassos depois da primeira barra final (`right="end"`). Desses,
**9 não tocados** (hino 458, todos depois da barra final, fora do timemap) e 25 que o
timemap **toca** (hinos 360, com 16, e 453, com 9): nesses dois, o `right="end"` é dupla
barra no meio da peça, seguida de casa 2 e repetição; o timemap segue por ali (a regra
"depois de barra final, não tocado" não vale em geral; ver "Desvios").

Divergências explicadas (todas com causa; nenhuma nova):

- **R3 (nota invisível, `print-object="no"`), 16 no corpus MusicXML.** Gymnopédie n.º 1:
  10 compassos (21 a 30) em que uma pausa invisível não sai no `music.json`; removendo as
  invisíveis do esperado, a divergência some (medido). Clair de Lune: 2 camadas (compassos
  65 e 67, pauta 1, camada 1) em que a nota invisível não sai, e 4 quiálteras no compasso 22
  (pautas 1 e 2, camadas 2 e 7) em que notas invisíveis abrem ou fecham o colchete. As outras
  42 camadas com invisíveis saem com elas (o Verovio as mantém, com a invisibilidade perdida).
- **R-TRINADO, 12 no corpus MEI** (trinados do Scarlatti só com `@tstamp`; resolvida em R2, entram em `ornaments`): antes, fora de
  `ornaments`, como mapeado no M03.
- **Arredondamento de 6 algarismos**: `tstamp` e `bpm` saem com 6 algarismos
  significativos (hinos 215 e 239: `1.16667` por `1.1666667`). Tolerância relativa de 5e-6;
  contado em `arredondados_6_algarismos` (2 nos hinos). Não é erro, é a forma do JSON.

Checagens do próprio oráculo (feitas para não confiar num zero à toa):

- Mutação no `music.json` da fixture (apojatura, fórmula, `kindText`, texto de `chg`,
  evento apagado, armadura, `right`): todas acusadas.
- Mutação num hino (`001`: evento, barra, texto de cifra): acusada.
- Fixture `m02`: 42 eventos, 6 compassos, 2 partes, 2 cifras e 1 trinado conferidos.

`just medidor`: **não executado.** Motivos:

1. O `medir` exige a pasta ou o arquivo (`Falta a pasta ou o arquivo .musicxml`); sem
   argumento o `just medidor` falha.
2. O aprendizado resolve `verovio_flutter_bridge` por `path` e o caminho é um link para este
   repositório, com o binding Dart do M05: `getElementAttr(String xmlId)`. O
   `music_toolkit.dart` (L22) chama `getElementAttr(id, '')` com dois argumentos, então o
   medidor não compila até a troca do M08 (que está fora deste passo).
3. Rodar exigiria escrever em `zywny-aprendizado` (`.dart_tool/` e, sem `--out`, `build/medidor`),
   o que o escopo proíbe.

Os números 149 / 25 / 6 / 7 / 56 / nenhum 506 não foram reproduzidos neste passo.

Desvios e correções no M00:

1. **R1 (premissa refutada).** O importador grava o valor do MEI: sem barra →
   `acc` (apojatura, acentuada), com barra (`slash="yes"`) → `unacc` (acciaccatura). O oráculo
   confere os 6 364 eventos do corpus MusicXML e os 141 214 dos hinos com essa regra. Spec
   §2.9 corrigida (R1); importador não tocado.
2. **"Compassos depois de barra final não entram no timemap"** vale para o hino 458 (9
   compassos) e não é regra geral: 25 compassos depois de `right="end"` estão no timemap (360
   e 453). O "não tocado" passa a ser definido pelo timemap.
3. **"Notas invisíveis não entram no `Doc`" (M01)** vale só em parte: a maioria entra (42
   camadas do Clair de Lune, com a invisibilidade perdida); saem 10 pausas invisíveis da
   Gymnopédie e 2 camadas do Clair de Lune. O `music.json` não traz a visibilidade. Spec R3
   atualizada.
4. **`layer n` = `<voice>`** confirmado em todas as 147 515 notas medidas (corpus e hinos).
   A pauta do evento é o `@staff` do nó, e 131 notas são cruzadas (confirmado).
5. **Espaços `s` de preenchimento** (não estavam no M00): o `music.json` traz `s` que não são
   pausas escritas (lacunas da camada). Spec §2.9, R6.
6. **Arredondamento de 6 algarismos** em `tstamp` e `bpm` (não estava no M00): registrado acima.

O que o M08 precisa saber:

- Os oito vetores estão em `docs/formato/musica/vetores/` (`vetores.json` é o índice).
- Eventos `s` aparecem em qualquer posição da camada, inclusive antes de uma nota, por
  lacuna (`<forward>` ou voz que ainda não chegou). O app os trata como espaço, não como pausa.
- Notas invisíveis podem sair como `n` em `music` (sem marca de visibilidade): o app não deve
  supor que todo `n` é som escrito visível.
- `tstamp` e `bpm` vêm com 6 algarismos significativos.
- O `renderToMusicJson`/`getElementAttr` de 1 argumento (M05) quebra o medidor até o M08.
- Trinados só com `@tstamp` (R-TRINADO) não aparecem em `ornaments`.

**2026-11-08: M05-P (correção do M05: `pitchpos` completo também sem corte)**

Decisão do usuário (2026-11-08): `renderToMusicJson` monta o layout quando o carregamento não cortou, em vez de deixar `loc` e `acc` `null` (a alternativa que o M05 registrou). Entregas:

- `Toolkit::LayOutPagesWithoutDrawing()` (`toolkit.h`/`toolkit.cpp`, privado): para cada página, `m_doc.SetDrawingPage(p, true)` e `m_view.SetPage(page, true)`, o trecho de layout de `RenderToDeviceContext`, sem `DrawCurrentPage`. `RenderToMusicJson` chama essa função só quando `!m_layoutAtLoad`, e então `RenderPitchPos(1, -1, midiLog)` com `withLayout` padrão (`true`).
- Nada mais muda no código: `music`, `timemap`, `midi`, `scene`, `glyphs`, `alternates`, manifest e os caminhos cortados (`-t vsb`, `-t vsb-json`, `renderToBridgeJson`) seguem os mesmos.
- `withLayout = false` (e o ramo `layout = false` de `WritePitchPos`, que grava `null`) ficou **sem chamador**. Mantido de propósito, porque remover não fazia parte da correção; limpar é decisão à parte.
- Documentação atualizada: §2.8 (o parágrafo "Sem layout" virou "Layout", sem o `null`), §2.10 (`null` retirado e função nova citada), histórico de revisões (linha M05-P; `version` continua `1`), comentários de `toolkit.h`, `bridgepitchpos.h`, `bridgewriter.cpp`, `c_wrapper.cpp` e o doc de `renderToMusicJson` no binding Dart.
- Nota: §2.9 não citava `loc`/`acc` nulos; a frase estava em §2.8 e §2.10, e as duas foram corrigidas.

Medição (linha de base no HEAD `cc16ed1`, `-x 42`, os 72 arquivos do corpus; saídas em `compare/out/m05p-base` e `compare/out/m05p-final`, scripts fora do repositório):

- **`loc`/`acc` `null`:** sem corte, a base tinha 14 555 eventos de `pitchpos` com `acc` `null` e 13 624 com `loc` `null`. Agora são **0** em `renderToMusicJson`, nos dois modos (58 220 eventos somados).
- **`pitchpos` de `renderToMusicJson` igual ao de `renderToBridgeJson` na mesma carga:** **288 de 288** pacotes (72 arquivos × automático e `--breaks none` × 2 ordens de chamada).
- **Com corte (automático):** `pitchpos` de `renderToMusicJson` igual à base em 72 de 72.
- **`timemap`, `midi` e `music`** de `renderToMusicJson` iguais à base em 144 de 144 (72 × 2 modos); `renderToBridgeJson` igual à base em 144 de 144.
- **Estado:** `getMEI`, `renderToTimemap` e os SVGs de todas as páginas, antes e depois da chamada, iguais à base: 144 de 144 linhas de estado e 288 de 288 SVGs. Em 9 dos 72 arquivos, o SVG já difere entre "antes" e "depois" dentro da mesma carga, **também na base**, pelos `id` de `tspan` gerados a cada render (mesma ressalva do M05, anterior à chamada).
- **Saídas da CLI** (`-t mei`, `-t svg -a`, `-t vsb-json`, `-t vsb` e os dois com `--breaks none`): **1 562** arquivos comparados com a base, **0** diferenças. Normalizados apenas `isodate` do MEI e a string de versão (`6.3.0-<hash>`).
- **Fixture `m02`** (`docs/formato/musica/m02-entrada.musicxml`): está entre os 72 arquivos da varredura.
- **Caso `mei-pb`** (`f04-cross-staff` gerado com `-t mei-pb`, `<pages>`, `LAYOUT_DONE`): a base tinha 6 de 6 eventos com `loc` e `acc` `null`; agora são 6 de 6 iguais ao `renderToBridgeJson`, nas duas ordens, sem `null`. **O SIGSEGV que o M05 relatou não reproduz com o layout completo.** Ele veio de um experimento que chamava só `LayOutPitchPos`, sem o `Page::LayOut` que `View::SetPage` faz; o caminho entregue não chama `LayOutPitchPos` sozinho.
- **Custo de `renderToMusicJson` sem corte** (10 primeiros hinos da lista do M01, `n = 7`, mediana): mediana das medianas **47,5 ms → 69,9 ms** (+22,4 ms, que é o layout). Hino 248: 65 → 130 ms (remedido com `n = 15`: 66 → 128 e 133). `renderToBridgeJson` no mesmo tempo não muda, dentro do ruído. Não é alvo; só registro. O caminho com corte não muda (43 ms de mediana, como no M05).
- **Build:** sem `warning:` nas compilações refeitas (CLI e `build-library`, `Release`).

Pendências (não decididas aqui):

- `docs/formato/schema-v1.json` ainda aceita `null` em `loc` e `acc` (acrescentado no M05). Não foi alterado: o pedido listava só a spec, e a spec agora diz que esses campos nunca são `null`. Decidir se o schema também tira o `null`.
- A versão embutida na biblioteca vem do `git describe` congelado na configuração do CMake: a `build-library` mostrava `6.3.0-ec8a8a2` depois do commit `cc16ed1`. É cosmético, mas torna a comparação de saídas ruidosa; por isso a checagem normaliza a versão.

Passo M05-P: **concluído** (correção do M05). O `music.json` não muda (é o que o M06 lê); só o `pitchpos` de `renderToMusicJson` sem corte passa a sair completo.

**2026-11-08: R2 (R-PARTES, R-TRINADO e schema do `pitchpos`; decisões do usuário de 2026-11-08)**

Decisões: **R-PARTES** pela opção (b), gravar o formato de origem no `Doc`; **R-TRINADO** pela
relaxação do esquema; **`pitchpos`** sem `null` em `loc` e `acc` no esquema, como já dizia a spec.

Entregas:

- `Doc::GetSourceFormat()`/`SetSourceFormat()` (`doc.h`, `doc.cpp`): campo interno, gravado pelo
  importador MusicXML (`MusicXmlInput::Import`, `MUSICXML`) e pelo MEI (`MEIInput::Import`, `MEI`), limpo
  em `Doc::Reset()`. Não entra no MEI, no SVG nem no JSON: `getMEI` e SVG seguem idênticos à base.
- `ReadBridgeMusic` (`bridgemusic.cpp`): `parts` por origem. MusicXML: como antes (uma entrada por
  `<part>`). MEI: uma entrada por `staffGrp` do `scoreDef`; um `staffGrp` sem `staffGrp` filho é uma
  parte só, com todas as pautas. Um `staffDef` solto num grupo que tem `staffGrp` filho continua sendo uma
  entrada própria (caso que o corpus não tem).
- `ornaments` (`bridgemusic.h`, `bridgewriter.cpp`): cada item ganha `measure` (índice do compasso) e
  `tstamp` (número ou `null`); `startid` pode ser `null`. Um controle sem `@startid` nem `@tstamp`, ou
  fora de compasso, sai com aviso.
- Esquema (`schema-v1.json`): `musicOrnament` com `measure`, `tstamp` e `startid` ou `tstamp` não nulo
  (`anyOf`); `pitchposEvent` com `loc` inteiro e `acc` sem `null`.
- Spec (§2.9 regras 5 e 6; exemplo de `ornaments`; linha do trinado no M02; histórico, linha R2).
- Oráculo (`compare/scripts/music_oracle.py`): o MEI passa a conferir `ornaments` com `measure` e
  `tstamp` (e `startid` ou `null`); o caso R-TRINADO sai. Partes do MEI continuam sem conferência
  (o oráculo só lê o MEI exportado).
- Fixture `m02-esperado.json` e vetores `m02.music.json` e `recusa.music.json` (os dois trinados ganham
  `measure` e `tstamp`); `vetores.json` não muda (o índice guarda só o `fonte_sha256`).

Medição (linha de base `compare/out/r2-base` no HEAD `d693c07`; resultado em `compare/out/r2-new`;
72 fontes, `-x 42`, com `--breaks` automático e `none`, 144 pacotes; fora do git):

- **Só `music.json` mudou**: em `parts`, 20 arquivos MEI (40 pacotes); em `ornaments`, 3 arquivos
  (6 pacotes). Nenhum MusicXML mudou em `parts`. Todo o resto é igual à base (`getMEI`, SVG de todas
  as páginas, `pitchpos`, `scene`, `glyphs`, `timemap`, `midi`, `alternates`, `meta`, manifest e o JSON
  único `-t vsb-json` sem o bloco `music`), depois de normalizar a versão (`-dirty`) e a data do `getMEI`.
  A chamada `renderToMusicJson` da biblioteca não foi comparada diretamente (usa o mesmo `ReadBridgeMusic`).
- **Partes, os 5 de `corpus/mei/`**: de 2 para 1 entrada, com as duas pautas (`staves` [1, 2]). Id:
  o `xml:id` do `staffGrp`, ou o que o Verovio gera quando a fonte não traz (`buv5k6i` nos 8 arquivos
  que trocaram de 2 para 1 entrada e em 7 dos 12 de 1 entrada; `a1sgk5cn` em `f05` e `s01`). Chopin Mazurka: o `staffGrp` tem `<label>1</label>`, então o nome
  sai `"1"` (antes saía `"piano"`, de cada `staffDef`). Ver "Pendências".
- **Partes, os outros 15 MEI** (mesma forma, mesma regra): fantasma `f04` e `f08` e sumico `g11` (de 2
  para 1 entrada, com `staves` [1, 2]); e 12 arquivos que já tinham 1 entrada (fantasma `f01`, `f02`,
  `f03`, `f05`, `f06`, `f07`; repetições `r02`, `r04`, `r07`, `r11`, `r12`; sumico `s01`), em que só o
  `id` muda, para o do `staffGrp`.
- **Ornamentos**: Scarlatti de 2 para 14 (os 12 com `@tstamp` só entram, `startid` `null`, `tstamp` 3;
  os 2 com `@startid` ganham `measure` 3 e 5 e `tstamp` 3). Chopin Nocturne (2 trinados) e a fixture
  `m02` (1) ganham `measure` e `tstamp: null`.
- **Esquema**: 144 `music.json` gerados, 144 `pitchpos`, a fixture, os 8 vetores e os 3 exemplos validam
  (Draft 2020-12). Negativos: os 7 do M02 continuam rejeitados; o novo (trinado sem `startid` e sem
  `tstamp`) é rejeitado; `loc` e `acc` com `null` no `pitchpos` são rejeitados. Positivos: trinado só
  com `tstamp` e trinado só com `startid` são aceitos. (Os negativos do M02 não estavam salvos no
  repositório; foram refeitos num script fora dele.)
- **Oráculo**: `verificar` da fixture `m02` com zero divergência (2 partes, 6 compassos, 42 eventos,
  1 trinado). Nas fontes MusicXML, zero divergência em todas, exceto Clair de Lune (6) e Gymnopédie (10),
  que são as 16 da R3 do M07 (notas invisíveis). **Varredura** (`compare/out/r2-varredura`, 617 fontes,
  0 erros do Verovio): corpus MusicXML 16 divergências, todas R3 (como no M07); corpus MEI 0 (ornamentos
  14, eram 2 no M07); hinos 0 (599 com 2 entradas em `parts`, 1 com 3, como antes); os demais grupos 0.
- **Vetores**: regenerados com `music_oracle.py vetores` (zero divergência nos 8).

Pendências (não decididas aqui):

- **Nome da parte no Chopin Mazurka** (`"1"`): é o `<label>` do `staffGrp` externo, lido como está. Se o
  app precisa do nome das pautas (`"piano"`), é uma decisão à parte (ler o `label` do `staffDef`, ou o do
  grupo só quando houver).
- **Partes do MEI sem conferência**: o oráculo não confere `parts` do MEI (só o MusicXML). A regra fica
  só na implementação e na §2.9.
- **MusicXML convertido por Humdrum** (`MUSICXML_DEFAULT_HUMDRUM`, fora do build padrão): chega como MEI e
  segue a regra do MEI. Não medido.

O que o M08 precisa saber:

- `parts` de um MEI sem partes tem uma entrada com as duas pautas; o `staves` da entrada é a lista certa
  para o app (não contar `parts`).
- `ornaments[].startid` pode ser `null`, e `tstamp` pode ser `null`; cada item tem pelo menos um dos dois.
  Um trinado do Scarlatti só com `tstamp` entra com `measure` e `tstamp`, e o app o localiza por compasso
  e batida (não pelo id notado).
- O `id` de uma parte de MEI sem `xml:id` no grupo é gerado pelo Verovio (estável para a mesma carga, não
  para outro arquivo).

**2026-11-08: M08 executado (nota para o `zywny-aprendizado`, limpeza de texto, portão e status)**

Entregas:

- `docs/nota-para-zywny-musica.md` (novo, 228 linhas; no molde da fantasma e da sumico): o que mudou,
  como chamar, a quebra do `getElementAttr`, os campos pela §2.9, a tabela "No app hoje" → "Passa a
  ser", o que pode apagar, as ressalvas para o host (Chopin, `s`, notas invisíveis, grace, trinado,
  barra final), o M06 no `zywny`, a verificação e as pendências.
- Limpeza de texto (R1, premissa refutada): **7 ocorrências** de "inversão"/"invertido" corrigidas
  (4 neste arquivo: linha do M02 na tabela de passos, o bullet do M02 e o bullet do M03 que o
  tratavam como pendente, e a linha do M07; 3 na spec: §2.9 R1, e as linhas do histórico de M02 e de M07).
  Nenhuma ocorrência fica nos textos do repositório, exceto a docstring de `compare/scripts/music_oracle.py`
  (L214, "A R1 do M02 (inversão) não se confirmou"), que é código e não foi alterada. Texto novo: "premissa
  refutada (R1)": o importador grava o valor do MEI (`acc` sem barra, `unacc` com barra), e o desenho
  sempre esteve certo. O M04 e o M03 também usavam "pendente" para a R1: já estavam superados pelo M07.
- Spec: §2.9 (R1 e a fixture) e histórico (linhas de M02, M07 e M08). Nenhuma mudança de forma (`version` `1`).
- M06 marcado como "não executado aqui (fica no zywny)" na tabela de passos (ver a seção 7 da nota).
- O `libverovio.so` de `verovio/bindings/dart/` (git-ignorado) estava de 2026-11-05, sem `renderToMusicJson`:
  foi recompilado com `verovio/bindings/dart/build_linux_so.sh` (o mesmo script do Linux). Nada versionado mudou.

Portão (critérios do conjunto, medidos em 2026-11-08 no HEAD `2090558` e no binário pré-M00 `d30bfef`):

| # | Critério | Resultado |
| --- | --- | --- |
| 1 | `music.json` no `.vsb` e no JSON único, validado pelo schema; §2.9 e histórico | **Atendido.** 144 `music.json` extraídos de `.vsb` gerados nesta conferência (72 fontes × `auto`/`none`) validam em `$defs/musicDocument`; o manifesto traz `music` em 144 de 144. Os 144 `music` do JSON único (`compare/out/r2-new`, do mesmo código) validam. §2.9 (regras 1-9, R1-R6, fixture) e o histórico (M02 a M08) estão atualizados. Schema: `docs/formato/schema-v1.json`. |
| 2 | `renderToMusicJson` em C, Dart e wasm, sem layout de desenho, nos ids da carga | **Atendido em C e Dart; wasm não compilado aqui.** C: `vrvToolkit_renderToMusicJson` exportado no `libverovio.so` recompilado; em processo novo por carga, 144 de 144 cargas dão só `timemap`, `midi` (quando há nota), `pitchpos` e `music`, iguais aos de `renderToBridgeJson` na mesma carga, sem `loc`/`acc` `null` e válidas em `$defs/musicJsonDocument`. Dart: `renderToMusicJson()` e `getElementAttr(String xmlId)`; `dart analyze lib test example` sem avisos. Wasm: `_vrvToolkit_renderToMusicJson` está em `exports.txt`, mas **não compilado aqui**: o `verovio/emscripten/build/verovio.js` é de 2026-11-05 e não tem a função (não tentei o emsdk, como pedido). **Ressalva** (ver abaixo): no mesmo processo, carregando as 144 cargas em sequência, a Clair de Lune difere em `timemap`/`midi` em 1 de 3 execuções. |
| 3 | Nenhuma saída existente muda | **Atendido.** 72 fontes × `auto`/`none` = 144 pacotes, gerados pelo binário pré-M00 (`d30bfef`, com `git archive`) e pelo atual, com `-x 42`: `getMEI`, SVG de todas as páginas, e no `.vsb` (zip) e no JSON único `timemap`, `midi`, `pitchpos`, `scene`, `glyphs`, `alternates`, `meta` e o manifesto são idênticos (normalizada a versão `6.3.0-<hash>` e o `isodate` do MEI). Diferem só `music.json` e a entrada `music` do manifesto. **Exceções registradas**, todas dentro do que é novo: o `music.json` mudou depois do M03 em duas frentes do R2 (`parts` de 20 arquivos MEI, de 2 para 1 entrada onde o `staffGrp` tem as duas pautas; `ornaments` de 3 arquivos: Scarlatti 2 → 14, Nocturne e `m02` ganham `measure` e `tstamp`) e o `pitchpos` de `renderToMusicJson` sem corte ganhou `loc`/`acc` no M05-P. Nada disso aparece nas saídas de CLI, que continuam como antes. |
| 4 | Oráculo: zero divergência nas fixtures; hinos medidos e exceções explicadas | **Atendido.** `music_oracle.py verificar` nos 8 vetores e na fixture `m02`: zero divergência, e os `fonte_sha256` das fontes do aprendizado batem com `vetores.json`. Varredura do R2 (`compare/out/r2-varredura`, 617 fontes, 0 erros do Verovio; a tabela do M07 soma 618 porque conta a `m02`, que é conferida à parte): **600 de 600 hinos sem divergência**; corpus MusicXML: 16, todas R3 (notas invisíveis); corpus MEI e aprendizado: 0. **Não feito:** `just medidor` (ver abaixo). |
| 5 | `score_bridge` lê o `music.json` e continua lendo `.vsb` antigos | **Não verificado aqui.** O pacote está em `zywny-comum/score_bridge`, que hoje não tem `VsbMusic` nem leitura de `music.json` (busca sem resultado). Não rodei `flutter test` lá (não se escreve no `zywny`). |
| 6 | Nota para o host escrita | **Atendido.** `docs/nota-para-zywny-musica.md`. |

Ressalvas e pendências (abertas para o usuário ou para o `zywny`):

- **Ids da Clair de Lune em sequência (novo, não resolvido).** No mesmo processo, depois de carregar
  muitas partituras, `renderToMusicJson` e `renderToBridgeJson` da mesma carga deram `timemap` e `midi`
  com ids de nota diferentes (ids gerados, sem `xml:id` na fonte: `mx1rdxl` contra `o1r4wlty`, no
  `--breaks none` e no automático, em 1 de 3 execuções). Em processo novo, por carga, dá igual (144 de
  144, e 10 execuções seguidas da Clair de Lune dão o mesmo hash). `renderToBridgeJson` sozinho em sequência
  não reproduz (0 em 3 execuções). Causa não investigada; a regra "ids iguais" vale hoje por processo. Para
  o host: não misture os dois caminhos no mesmo isolate sem conferir, e prefira `renderToMusicJson` sozinho.
  Reproduzir: `compare/out/m08/capi_diag.py` (sequência no mesmo processo) e `capi_fresh.py` (processo novo por carga).
- **Nome da parte no Chopin Mazurka (MEI)** (decisão aberta): `parts[].name` sai `"1"`. Ver a nota, seção 6.
- **Wasm**: `tool/build_verovio_web.sh` do `zywny-comum` precisa rodar de novo, e o `verovio_worker.js` ganhar a chamada.
- **`just medidor`**: não rodado (depende da troca do `getElementAttr` no `zywny-aprendizado`, que está fora
  deste repositório). Os números 149, 25, 6, 7, 56 e nenhum 506 (LM14/LM15) não foram reproduzidos.
- **M06**: fica para o `zywny` (seção 7 da nota). `compare/pubspec.yaml` ainda aponta para
  `/home/mauricio/IdeaProjects/zywny/score_bridge`, que não existe; o pacote está em `zywny-comum/score_bridge`.
  Não alterado aqui (fora do escopo).
- **Docstring de `music_oracle.py` (L214)** ainda diz "A R1 do M02 (inversão)". Código, não alterado; a correção
  de texto fica para um passo de código.

Scripts do portão: `compare/out/m08/` (git-ignorado; `compare.py` compara o binário pré-M00 por `PRE_BIN`, `capi_fresh.py` e `capi_diag.py` testam a API C, `vetores.py` e `validate_music.py` o oráculo e o schema).

Passo M08: **concluído com ressalvas** (wasm não compilado aqui; `score_bridge` não verificado aqui; `just medidor`
não rodado; ids da Clair de Lune em sequência no mesmo processo). M00: **concluído com ressalvas** (M06 no zywny).
