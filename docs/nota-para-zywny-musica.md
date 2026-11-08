# Nota para o `zywny-aprendizado` — `music.json` e `renderToMusicJson` (M00, M01-M08)

Fechada em 2026-11-08 no lado deste repositório (formato, exportador, API, oráculo
e vetores). **Toda a execução Dart é do host**: o modelo e o parser (M06, que
ficou no `zywny`, ver a seção 7), o medidor e a troca do `getElementAttr` no
`zywny-aprendizado`. O contrato normativo é a **§2.9** (`music.json`) e a **§2.10**
(`renderToMusicJson`) de
[`docs/formato/especificacao-v1.md`](formato/especificacao-v1.md); o plano e as
decisões (D-MUSICA-FORMA, D-MUSICA-CIFRA, D-MUSICA-Q) estão em
[`docs/plano/M00-dados-musicais-para-o-aprendizado.md`](plano/M00-dados-musicais-para-o-aprendizado.md),
com o registro de cada passo em "Notas de execução".

O pedido do aprendizado é a regra de projeto do `CLAUDE.md` dele: a informação
musical vem do Verovio, nunca da leitura direta do MusicXML ou do MEI. Esta nota diz
o que o Verovio passou a entregar para isso e o que o app pode apagar.

## 1. O que mudou

Tudo aditivo (`version` continua `1`; um leitor antigo ignora), exceto a quebra da
seção 3:

| O quê | Onde | Para quê |
| --- | --- | --- |
| `music.json` (novo) | §2.9, `manifest.files.music`, propriedade `music` no JSON único | a estrutura da partitura **notada**, sem geometria: partes, compassos (`n`, casas, barras, fórmula, armadura e modo), pautas, camadas, eventos, ornamentos, cifras, direções e andamentos |
| `renderToMusicJson` (nova) | §2.10 | um JSON só, com `timemap`, `midi`, `pitchpos` e `music`, **sem desenho** e nos ids da carga. C: `vrvToolkit_renderToMusicJson(tk)`; Dart: `VerovioToolkit.renderToMusicJson()`; wasm: `_vrvToolkit_renderToMusicJson` em `emscripten/exports.txt` |
| `pitchpos.json`: `loc` e `acc` sempre preenchidos (§2.8) | `renderToMusicJson` sem corte (M05-P) | antes saíam `null` quando o documento não era cortado no carregamento; agora o layout é montado sem desenhar. O `.vsb` e o JSON único não mudam |
| `getElementAttr` com **um** argumento | Dart: `getElementAttr(String xmlId)` | **quebra**, ver a seção 3 |

Nada que já existia mudou: medido no fim do M08, os 72 arquivos do corpus e das
fixtures (`corpus/mei`, `corpus/musicxml`, `corpus/fantasma`, `corpus/ligaduras`,
`corpus/repeticoes`, `corpus/sumico` e a fixture do M02), com `--breaks auto` e
`none`, dão **144 pacotes idênticos** ao binário de antes do M00 (commit `d30bfef`):
`getMEI`, SVG de todas as páginas, e no `.vsb` e no JSON único `timemap`, `midi`,
`pitchpos`, `scene`, `glyphs`, `alternates`, `meta` e o manifesto. Só entrou o
`music.json` (e a entrada `music` no manifesto). Depois de normalizar a versão
(`6.3.0-<hash>`) e o `isodate` do MEI.

**Custo, medido** (20 hinos, mediana das medianas, M05): `renderToBridgeJson` 175 ms;
`renderToMusicJson` 43 ms com corte. Sem corte, o layout que o `pitchpos` precisa
custa ~22 ms a mais (70 ms de mediana, M05-P). Os números são do binário de
`libverovio` deste repositório, sem o custo do isolate, do JSON e do worker do app.

## 2. Como chamar

- Chame `setOutputTo('vsb-json')` **antes** de `loadFile`/`loadData`, como já se faz
  para `renderToBridgeJson`. Os padrões do bridge (sem cabeçalho, rodapé nem rótulo
  de instrumento) só valem nesse modo, e afetam a quebra de página do documento.
- Os ids são os da carga: na mesma carga, os corpos de `timemap`, `midi`, `pitchpos`
  e `music` são iguais aos de `renderToBridgeJson` (144 de 144 cargas, em processo
  novo; M05, M05-P e M08). **Ressalva:** num processo que carrega muitas partituras em
  sequência, a Clair de Lune (`--breaks` automático e `none`) deu ids de nota diferentes
  em 1 de 3 execuções. Até isso ser investigado, não misture os dois caminhos no mesmo
  isolate sem conferir (ver o M00, "Notas de execução", M08).
- A chamada não muda estado: `getMEI`, `renderToTimemap` e o SVG são os mesmos antes
  e depois dela.
- Para ler a música, use `renderToMusicJson()`, não `renderToBridgeJson()` (que
  renderiza todas as páginas só para obter a cena e as outras três tabelas).

## 3. Quebra: `getElementAttr` tem um argumento

- Antes: `getElementAttr(String element, String attribute)`, chamando
  `vrvToolkit_getElementAttr(tk, xmlId)` com um id só. Funcionava porque o segundo
  argumento era ignorado.
- Agora: `getElementAttr(String xmlId)`. O retorno não muda.
- **Quem quebra no aprendizado:** `lib/music_reading/music_toolkit.dart`, linha 22,
  `_toolkit.getElementAttr(id, '')`. A troca é `_toolkit.getElementAttr(id)`. Não há
  `@Deprecated`: a decisão de 2026-11-07 foi quebrar e o `zywny` atualiza junto.
- Neste repositório não há outro chamador (`grep -rn getElementAttr verovio/bindings
  compare`). O `score_bridge` não está aqui (seção 7).

## 4. Os campos, pela spec (§2.9)

- **`version`** é `1`. O leitor recusa valor maior (§9).
- **`parts`** (regra 5). MusicXML: uma entrada por `<part>`. MEI: uma entrada por
  `staffGrp` do primeiro `scoreDef`; um `staffGrp` sem `staffGrp` filho é **uma**
  entrada com todas as pautas dele. Use `staves`, não conte as entradas: num MEI sem
  partes há uma só. `id` é o `xml:id` do grupo (ou o gerado pelo Verovio quando a
  fonte não traz; é estável numa carga, não entre arquivos).
- **`measures`** (regras 1 a 4), na ordem do documento **notado**, sem desdobrar
  repetições. Entram a introdução (`n` `"1i"`), a anacruse (`n` `"0"`) e os compassos
  depois de uma barra final. `index` é 0-based. Os `id` são os notados (sem `-rend<N>`).
  - `left`/`right`: `rptstart`, `rptend`, `rptboth`, `end`, `dbl`... ou `null`.
  - `ending`: `null`, ou `{"n": "2, 3"}`. **Separe por vírgula e tire os espaços**
    (R5): o valor é o `@number` como o MEI o grava, não o texto impresso.
  - `meter` e `key` são os valores **vigentes no começo do compasso**, em todo
    compasso (a regra 3 não compara com o anterior). `meter.sym` é `"common"`,
    `"cut"` ou `null`. `key.fifths` é a soma das alterações, também fora do padrão.
    `key.mode` é `null` quando a fonte não traz `<mode>`: **não** deduza modo pela
    armadura.
  - `staves` → `layers` → `events`. Cada evento traz os cinco campos (`id`, `t`,
    `chord`, `grace`, `tuplet`). `t`: `n` nota, `r` pausa, `mr` pausa de compasso,
    `s` espaço (ver a seção 6). `chord` é o id do `<chord>` (todas as notas do acorde
    trazem o mesmo). `grace` é `false`, `"acc"` (apojatura) ou `"unacc"`
    (acciaccatura), como o MEI grava. `tuplet` é `{"num", "numbase"}` da quiáltera
    mais interna. A pauta do evento é o `@staff` do nó, e a camada é a `layer n`
    (o `<voice>`).
  - **Sem `q`/`ql`** (D-MUSICA-Q): a duração escrita não sai. O tempo de cada nota
    vem do timemap, pelo mesmo id, como hoje.
- **`ornaments`** (regra 6). `kind` (`trill`, `mordent`, `turn`), `measure` (índice do
  compasso), `startid` (o id da nota, ou o do `chord` quando a nota é de acorde) e
  `tstamp` (batida a partir de 1). Cada item tem `startid` ou `tstamp`, não nulo.
  Trinado só com `tstamp` (Scarlatti, R-TRINADO) entra com `startid` `null`.
- **`harmonies`** (regra 7). Uma por `<harmony>`, com `measure`, `staff` (a pauta da
  parte onde está a cifra), `tstamp`, `root`/`rootAlter`, `kind` (texto de `<kind>`,
  sem tradução), `kindText` (o `@text` do `kind`, quando existe; é ele que o desenho
  usa em 49% das cifras do corpus medido), `bass`/`bassAlter`, `degrees`
  (`value`/`alter`/`type`) e `numeral` (`{"root", "alter"}`, sem `root`). **`text`** é o
  que o Verovio desenha, e nunca vazio. Cifra de **MEI** traz só `text`: os campos
  estruturados saem `null` e `degrees` sai `[]`.
- **`directions`** (regra 8). Uma por `<direction>` com `<words>`: `text` é o texto
  cru, concatenado sem separador (como o desenho junta); `place` (`above`/`below`/`null`),
  `measure`, `staff` e `tstamp`. Andamento (`<sound tempo>`, `<metronome>`) vai a
  `tempi`, mesmo com `<words>`; dinâmica fica no `midi.json`.
- **`tempi`** (regra 9). `bpm` (número ou `null`) e `text` (o texto desenhado ou `null`).
- **Números** `tstamp` e `bpm` saem com 6 algarismos significativos
  (`1.16667`, não `1.1666667`). Compare com tolerância relativa, não por igualdade.

## 5. O que o app faz com cada dado, e o que pode apagar

A tabela é a do M00, com os nomes que o código tem hoje.

| No app hoje | Passa a ser |
| --- | --- |
| `MusicVerovio.bridge()` (`renderToBridgeJson`) + `attributes(id)` (pré-busca de `measure`, `staff`, `layer` e `note`), em `music_verovio.dart` e `music_toolkit.dart` | `renderToMusicJson()` (o texto que devolve é o `music` + as tabelas); some a pré-busca |
| Fórmula de compasso pelos glifos da `meterSig` da cena (remendo: `_glyphDigit0`, `_glyphCommon`, `_glyphCut`, função de `count/unit` em `music_verovio.dart`) | `measures[].meter` (`count`, `unit`, `sym`) |
| `readMusic` lê a cena e recompõe o tempo pelo timemap | lê `music`; o tempo continua vindo do timemap (D-MUSICA-Q) |
| Leitor da armadura pelo `pitchpos` (`writtenKeyOfDocument`, `score_measures.dart`) e o da ABC (`readAbcWrittenKey`, `score_key.dart`) | `measures[0].key` (com `mode`). A armadura de ABC continua sendo leitura de texto ABC: é outro formato, fora do Verovio |
| `readMelodyXml` (`zywny_music`, `packages/zywny_music/lib/melody_xml.dart`, do `zywny-comum`; lê o XML) | **aposentado**: notas e compassos de `music`, `midi` e `pitchpos`; `chg` de `directions`; cifras de `harmonies` |
| Cifra pelo texto desenhado | `harmonies[].root`/`kind`/`kindText`/`bass`/`degrees`, convertidos na grafia que o app usa (ex.: `C7M`) |
| Isolate (nativo) e worker (Web) devolvem `{bridge, attributes}` | devolvem o texto de `renderToMusicJson()`: uma chamada, sem layout de desenho. O `verovio_worker.js` hoje chama só `renderToBridgeJson` |

**Pode apagar** (lista do M00): `kMusicAttributeClasses`, `musicSnapshotOf`, a
pré-busca de atributos (`SnapshotMusicVerovio` com `attributes`), o `getElementAttr`
(com a troca da seção 3), o remendo dos glifos de `meterSig`, o leitor de cifra por
texto e `readMelodyXml`. A troca do `CLAUDE.md` do aprendizado, na regra "a
informação musical vem do Verovio", pode passar de "pendência" para "troca em
andamento", com o link para `docs/plano/M00-dados-musicais-para-o-aprendizado.md`
deste repositório. Esta nota **não** altera nada no aprendizado.

## 6. Ressalvas que o host precisa conhecer

- **Nome da parte no Chopin Mazurka (MEI).** O `staffGrp` externo tem
  `<label>1</label>`, então `parts[].name` sai `"1"` (antes o app via `"piano"`, do
  `staffDef` de cada pauta). **Para MEI, não confie em `name` sem conferir**: use
  `staves` e o `id`. Se o app precisar do nome das pautas, é decisão à parte (ler o
  `label` do `staffDef`, ou o do grupo só quando houver). Pendência aberta.
- **`s` é espaço, não pausa** (§2.9, R6). Pode aparecer em qualquer posição da camada,
  inclusive antes da primeira nota, por lacuna ou `<forward>`. Não conte como pausa e
  não o use para o tempo.
- **Notas invisíveis** (`print-object="no"`, R3) podem sair como `n` em `music`: não há
  flag de visibilidade. Se o app precisa dela, use o documento notado, ou não suponha
  que todo `n` é som escrito visível. No corpus, 16 divergências do oráculo são desse
  caso (Gymnopédie n.º 1 e Clair de Lune), todas explicadas.
- **Grace não se troca.** `grace` segue o valor do MEI: `"acc"` (apojatura, sem barra),
  `"unacc"` (acciaccatura, com barra). A hipótese de que o importador trocava esses
  valores (R1) foi **refutada** no M07: o oráculo confere os 6 364 eventos do corpus
  MusicXML e os 141 214 dos 600 hinos. Não troque os valores no leitor.
- **Trinado sem `startid`.** Localize pelo compasso (`measure`) e pela batida
  (`tstamp`). Um trinado de acorde aponta para o `chord`, não para a nota.
- **Pauta de cifra em parte de duas pautas** (R2): sem caso no corpus; a cifra sai na
  primeira pauta da parte. **`numeral`** (R4): só o caso sintético da fixture.
  **Alteração fracionária** (quarto de tom) sai truncada: nenhuma no corpus.
- **Compassos depois de barra final.** Entram em `measures`. Quem diz se um compasso
  é tocado é o timemap: no hino 458 os 9 compassos depois de `right="end"` ficam fora,
  mas nos hinos 360 e 453 há 25 que o timemap toca. Não use "depois de barra final" como regra.
- **Casa**: `ending.n` é uma lista separada por vírgula, com ou sem espaço (`"2, 3"`,
  `"2,3,4"`). Separe e tire os espaços (R5).
- **Direções**: só `<words>` que o importador grava como `dir`. Dinâmica e andamento
  estão em outros lugares (seção 4).

## 7. M06 não foi executado aqui (fica no `zywny`)

O M06 (`score_bridge` em Dart: modelo `VsbMusic`, classes de música e parser de
`music.json` em `VsbDocument.music`, opcional e tolerante a campo novo) **não foi
feito neste repositório**. O pacote `score_bridge` foi para o `zywny-comum` (git
subtree, em `zywny-comum/score_bridge`), e o `compare/pubspec.yaml` daqui ainda aponta
para `/home/mauricio/IdeaProjects/zywny/score_bridge`, que não existe. Decisão do
usuário, 2026-11-08: o M06 fica para o `zywny`. Em 2026-11-08, `zywny-comum/score_bridge`
ainda não tem `VsbMusic` nem leitura de `music.json` (busca sem resultado, sem
alteração). O que o `zywny` precisa fazer:

1. Criar o modelo `VsbMusic` e o parser, no molde do `midi` e do `pitchPos` (G02).
2. Testar o parser com `docs/formato/musica/m02-esperado.json` (a fixture) e com os
   vetores de `docs/formato/musica/vetores/` (oito `music.json`, um por fonte do
   aprendizado e de curso, mais o índice `vetores.json` com o `fonte_sha256` de cada
   fonte).
3. Testar `.vsb` antigo (sem `music.json`) e o JSON único sem `music`: `music` `null`.
4. Conferir `flutter analyze` e `flutter test` no pacote (não rodados aqui).

## 8. Verificação feita aqui

- Schema: os 144 `music.json` dos pacotes `.vsb` gerados agora, os 9 da fixture e dos
  vetores, e os 144 `music` do JSON único validam em `$defs/musicDocument`
  (`docs/formato/schema-v1.json`, Draft 2020-12). Os `loc` e `acc` do `pitchpos` não
  aceitam `null`.
- Oráculo: `compare/scripts/music_oracle.py verificar` nos oito vetores e na fixture
  do M02: zero divergência, e os hashes das fontes do aprendizado batem com
  `vetores.json`. Varredura do R2 (617 fontes, 0 erros do Verovio): hinos 600 de 600
  sem divergência; corpus MusicXML, só as 16 de R3; corpus MEI sem divergência (as
  partes do MEI não são conferidas pelo oráculo).
- **Não rodado aqui:** `just medidor` do aprendizado (depende da troca da seção 3
  no app). Os números que ele deve dar (149, 25, 6, 7, 56 e nenhum 506 nos hinos,
  LM14/LM15) não foram reproduzidos neste repositório.

## 9. Vetores e oráculo

- Fixture: `docs/formato/musica/m02-entrada.musicxml` (MusicXML sintético, duas
  partes, seis compassos) e `m02-esperado.json`.
- Vetores: `docs/formato/musica/vetores/` (`*.music.json` e `vetores.json`).
- Oráculo: `compare/scripts/music_oracle.py` (subcomandos `verificar`, `varredura`,
  `vetores`). Lê o MusicXML direto, sem o Verovio; o MEI só é conferido em parte.
  As causas conhecidas (R2, R3, R4) estão no cabeçalho do script.
- Schema: `docs/formato/schema-v1.json`, `$defs/musicDocument` (o `music.json`) e
  `$defs/musicJsonDocument` (o retorno de `renderToMusicJson`).

## 10. Pendências do lado do app, em ordem

1. Trocar `getElementAttr(id, '')` por `getElementAttr(id)` (seção 3) e rodar
   `just medidor`.
2. Recompilar a `libverovio` de cada plataforma que o app empacota, para ter
   `renderToMusicJson`. Linux: `build_linux_so.sh`; Android: `build_android_so.sh`.
   **Web (wasm):** o `emscripten/exports.txt` já tem `_vrvToolkit_renderToMusicJson`,
   mas o build wasm não foi refeito aqui (ver "Notas de execução", M08, no M00). O
   `verovio.js` que está em `verovio/emscripten/build` é de 2026-11-05 e não tem a
   função. Quem usa o worker Web precisa de `tool/build_verovio_web.sh` de novo, e o
   `verovio_worker.js` ganhar a chamada (hoje ele só chama `renderToBridgeJson`).
3. Fazer o M06 (seção 7).
4. Decidir o nome das partes de MEI, se o app precisar dele (seção 6).

Os números de cada passo estão em `docs/plano/M00-dados-musicais-para-o-aprendizado.md`,
"Notas de execução".
