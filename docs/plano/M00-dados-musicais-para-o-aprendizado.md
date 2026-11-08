# M00 — Os dados musicais que o `zywny-aprendizado` pede ao Verovio (`music.json`)

**Depende de:** G01 e G04c (o `midi.json` e o `pitchpos.json` já existem) ·
**Decisões:** **D-MUSICA-FORMA**, **D-MUSICA-CIFRA** e **D-MUSICA-Q** resolvidas pelo usuário em 2026-11-07 (abaixo); o `getElementAttr` do M05 também (ver "Notas de execução")

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
| M02 | Especificação: §2.9 `music.json`, o schema JSON, uma fixture, histórico de revisões | M01 | concluído com ressalva: R1 (inversão de `grace` pelo importador, decisão do usuário pendente), ver "Notas de execução" |
| M03 | C++: `ReadBridgeMusic` (partes, compassos, fórmula, armadura e modo, notas/pausas, ornamentos, andamentos) e `music.json` no `.vsb` e no JSON único | M02 | pendente |
| M04 | C++: cifras e direções (a estrutura da `<harmony>` guardada no importador; texto de `<words>`) | M03 | pendente |
| M05 | API: `RenderToMusicJson`, `c_wrapper`, binding Dart (e a correção do `getElementAttr`), `exports.txt` | M03, M04 | pendente |
| M06 | Dart (`score_bridge`): modelo `VsbMusic` e parser de `music.json` | M02, M05 | pendente |
| M07 | Oráculo, varredura e vetores: `music.json` contra o MusicXML (lido por script), corpus, fixtures do aprendizado e os 600 hinos | M04, M05 | pendente |
| M08 | Nota para o `zywny-aprendizado` (a execução Dart de lá fica lá) | M06, M07 | pendente |

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

- `grace` está **invertido** no importador do MusicXML: `slash="yes"` (acciaccatura)
  vira `unacc`, e a ausência de barra vira `acc` (`iomusxml.cpp` L3310-3345). O
  desenho continua certo porque a barra vem em `stem.mod="1slash"`. A spec segue o
  valor do MEI, como o M00 pede (`@grace`). **Pendente de decisão do usuário (R1):**
  (a) manter o valor do MEI e traduzir no leitor; ou (b) corrigir o importador. A
  (b) muda o MEI e o `getMEI` do corpus, o que fere o critério 3 do "Critérios de
  aceite do conjunto". Nenhuma das duas foi decidida aqui.
- `ending.n` com espaço (`"2, 3"`) passa do `@number` sem normalização.
- Os ids da fixture vêm de `verovio -x 42` (binário do fork, `6.3.0-8aabb53-dirty`).
  O M03 precisa reproduzi-los para o teste do `ReadBridgeMusic`.

**Ressalvas para o M03 e o M07 (não bloqueiam o M02)**

- R2: pauta da cifra em parte de duas pautas, só no caso sintético.
- R3: notas invisíveis (`print-object="no"`), ainda fora do timemap e de `music.json`.
- R4: `numeral` sem caso real; fixture não cobre (M07).

Os desvios e os números do M07 entram aqui quando o passo rodar.
