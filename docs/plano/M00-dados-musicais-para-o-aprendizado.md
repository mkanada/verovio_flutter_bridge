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
  só para obter a cena e as outras três tabelas, que **não dependem de layout**.
  Medido: ~50 ms numa peça de 8 compassos e ~0,5 s por hino na passada nos 600
  hinos (a maior parte, o desenho).
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
- `verovio/src/iomusxml.cpp`: `ReadMusicXmlHarmony` (~L2860: onde a cifra vira
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
  graus **não são guardados**.
- O timemap desdobra repetições e casas (ids `-rend<N>`); a primeira passada tem
  o id notado. Os compassos depois de uma barra final (`right="end"`) **não**
  entram no timemap (o hino 458 tem 9 deles).
- `Toolkit::RenderToBridgeJson` já monta, nesta ordem e **sem** depender uns dos
  outros: `scene` (precisa de layout), `timemap`, `meta`, `midi` e `pitchpos`.
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
   `<ending>`, senão `null`.
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
   nota ou `<graceGrp>` pai). `tuplet`: `{"num": 3, "numbase": 2}` da quiáltera
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

- O `pitchpos` hoje lê o desenho (`loc`, ponteiros cross-staff) e por isso
  depende do layout da página 1; **medir** (M01) se dá para produzi-lo sem
  desenhar (RedoLayout sem render, ou um layout reduzido), e se não, o campo
  `loc` sai `null` nessa chamada e a spec diz isso. O app não usa o `loc`.
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
| M01 | **Medir** os fatos (decisões já tomadas, ver "Decisões necessárias"): o que o `Doc` notado tem (`Harm`, `Dir`, `KeySig::mode`, `layer n` = voz, id da parte), custo de `RenderToMusicJson` sem layout | — | pendente |
| M02 | Especificação: §2.9 `music.json`, o schema JSON, uma fixture, histórico de revisões | M01 | pendente |
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
   `harmonia/media/folclore-1`) e uns 20 hinos do `Hymn_Grabber`
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
- nos **600 hinos** (`../Hymn_Grabber/musicxml_simplificado`), com `just
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

Os desvios e os números do M07 entram aqui quando o passo rodar.
