# E01b — Timemap com compassos no `.vsb` e contrato dos ids expandidos

**Depende de:** E01a · **Decisão necessária:** **sim — D-EXPMAP** (pare e
pergunte antes de escrever código)

## Objetivo

Duas mudanças pequenas no contrato do `.vsb`, antes de mexer no Dart:

1. O timemap embutido passa a trazer **`measureOn`**, o id do compasso que
   começa em cada instante (com `-rendN` nas repetições). É a sequência de
   compassos em ordem de execução, dada pelo próprio Verovio, sem depender de
   haver nota começando no compasso.
2. A especificação passa a dizer o que é um id `-rend<N>` do timemap e como o
   leitor chega ao nó da cena.

## Decisão necessária — D-EXPMAP

**Como o leitor sabe que `abc-rend2` é o nó `abc` da cena?**

- **(a) Regra do sufixo (recomendado).** A especificação documenta a
  convenção do próprio Verovio (`ExpansionMap::GeneratePredictableIDs`): se
  um id do timemap não existe na cena e termina em `-rend<N>` (N ≥ 2), com a
  base existindo na cena, ele é a N-ésima execução da base. O formato não
  ganha arquivo novo. Verificado em 2026-09-21: **0 divergências** entre a
  regra e o `-t expansionmap` do Verovio em 2 933 ids de timemap (1 063 deles
  `-rend2`; Gymnopédie e Maple Leaf Rag com `--xml-id-seed 42` nas duas
  saídas). E02a repete a verificação sobre todo o corpus e as partituras de
  E01a.
- **(b) Embutir o mapa.** Gravar um `expansion.json` no pacote. O
  `-t expansionmap` completo tem **50 KB (Gymnopédie) e 207 KB (Maple Leaf
  Rag)** de JSON cru, porque lista todo elemento clonado (pauta, camada,
  haste…), não só os ids do timemap. Teria que ser filtrado para os ids do
  timemap (id expandido → id notado). É uma mudança aditiva do formato, como
  foi a do `meta.json`.

Com (a), este passo só grava `measureOn` e documenta a regra. Com (b), grava
também o `expansion.json` filtrado (spec §2, manifest `files.expansion`,
parser em `score_bridge`) e E02a passa a ler o mapa em vez de aplicar a regra.

## Ler antes (só isto)

- `verovio/src/toolkit.cpp`: `RenderToBridgeFile` (L2114; o timemap é pedido
  na L2147, `this->RenderToTimemap()` **sem opções**) e `RenderToTimemap`
  (L1901: opções `includeMeasures`, `includeRests` e `useFractions`, todas
  `false` por padrão).
- `docs/formato/especificacao-v1.md` §2 (pacote e timemap) e o histórico de
  mudanças no fim do arquivo.
- `score_bridge/lib/src/parser.dart` L657 (`measureOn` já é lido) e
  `model.dart` L502 (`TimemapEntry`).

## Contexto que você precisa (não vá procurar, está aqui)

- Hoje o timemap embutido **nunca** traz `measureOn` (0 entradas nas 10
  peças). `ScoreTimeline` deduz o compasso pela cena (ancestral `measure` da
  nota). Um compasso sem nenhuma nota começando nele (só ligaduras, ou só
  pausas, já que `includeRests` também está desligado) não aparece hoje.
- `--timemap-options '{"includeMeasures":true}'` no `-t timemap` produz, na
  Gymnopédie, 78 entradas com `measureOn` (31 com `-rend2`).
- `-t vsb-json` (`RenderToBridgeJson`, L2069) **não** embute timemap (passa
  `""`). Não mude isso aqui.
- S07 comparou o timemap embutido com o `-t timemap` avulso e achou uma
  diferença conhecida: o último dígito de `tempo` pode divergir em peças com
  expansão (`Att::StrToDbl` usa `std::stof` na ida e volta pelo MEI). Essa
  diferença continua tolerada.
- MusicXML sorteia ids a cada execução: para comparar dois `.vsb` byte a byte,
  gere os dois com `--xml-id-seed <n>`.

## O que fazer

1. Em `RenderToBridgeFile`, pedir o timemap com
   `{"includeMeasures": true}`. Não acrescente `includeRests` nem
   `useFractions`: mudariam outras colunas que o `score_bridge` já lê.
   Explique no comentário que fica ao lado da chamada.
2. Especificação §2: `measureOn` presente no início de cada compasso tocado;
   ids do timemap podem ser de elementos expandidos (`-rend<N>`) e como
   resolvê-los (conforme D-EXPMAP). Linha nova no histórico (mudança aditiva,
   `version` continua `1`).
3. Regenerar os `.vsb` do corpus em `compare/out/e01b/` e a fixture
   `score_bridge/test/fixtures/erik-satie.vsb`. Atualize os testes que contam
   entradas do timemap, explicando cada número que mudou.
4. Corrigir o README do plano: a linha "`measureOn` no timemap — nunca
   preenchido" da tabela de fatos.

## Fora de escopo

- Usar `measureOn` no Dart (E02b).
- Corrigir expansões erradas (E04a/E04b).
- Timemap no `-t vsb-json`.

## Critérios de aceite

1. Nas 10 peças e nas 13 partituras mínimas, o número de `measureOn` no
   `timemap.json` embutido é igual ao de ocorrências que o script de E01a
   conta pelas notas, ou a diferença é explicada caso a caso (compasso sem
   nota começando nele). Gymnopédie: 78, sendo 31 com `-rend2`.
2. O timemap embutido é idêntico ao de `-t timemap --timemap-options
   '{"includeMeasures":true}'` (MEI byte a byte; MusicXML com
   `--xml-id-seed`), salvo o último dígito de `tempo` já conhecido de S07.
3. `scene.json`, `glyphs.json` e `meta.json` são **byte-idênticos** antes e
   depois nas 10 peças (MusicXML com `--xml-id-seed`): o desenho não mudou.
   `manifest.json` só muda se D-EXPMAP = (b).
4. Especificação atualizada (§2 + histórico). Se D-EXPMAP = (b): schema,
   parser e testes do `expansion.json` também.
5. `flutter analyze` limpo e `flutter test` verde em `score_bridge`.

## Notas de execução

**D-EXPMAP resolvida pelo usuário: (a) regra do sufixo.** Documentada em
`docs/formato/especificacao-v1.md` §2.4 (nova). Sem `expansion.json`; sem
mudança no `manifest.json`.

**Mudança de código.** Uma linha em `Toolkit::RenderToBridgeFile`
(`verovio/src/toolkit.cpp`): `this->RenderToTimemap()` passa a
`this->RenderToTimemap("{\"includeMeasures\": true}")`, com um comentário
explicando por que `includeRests`/`useFractions` continuam de fora. Nada
mais em `verovio/src` ou `verovio/include`.

**Critério 1 (contagem de `measureOn`).** Nas 10 peças e nas 13 partituras
mínimas de E01a, o nº de `measureOn` no timemap embutido é **idêntico** ao nº
de ocorrências que `repeat-order.py` já contava pelas notas (E01a): Gymnopédie
78 (31 `-rend2`), Maple Leaf Rag 130 (45), r01 10, r02 10, r03 9, r04 6, r05 6,
r06 18, r07 18, r08 6, r09 8, r10 7, r11 9, r12 5, r13 3, e uma ocorrência por
compasso nas 4 peças sem repetição de verdade (Étude/Nocturne/Clair de
Lune/Prelude) e nas 4 MEI que hoje não expandem. Nenhuma diferença por
"compasso sem nota começando nele" apareceu neste corpus.

**Critério 2 (timemap embutido == `-t timemap --timemap-options
'{"includeMeasures":true}'`).** Idêntico nas 10 peças (MEI byte a byte,
MusicXML com `--xml-id-seed`), exceto o último dígito de `tempo` na
Gymnopédie — o quirk já conhecido de S07 (arredondamento float32 no
round-trip de `SetMidiDoc`), não uma regressão.

Armadilha do processo de verificação: comparar o timemap embutido (saída de
`-t vsb`) com o de `-t timemap` avulso só é válido se as duas chamadas
usarem `--xml-id-seed` — isso vale tanto para MusicXML (já sabido, S07)
quanto para **MEI**, que também tem elementos sem `xml:id` explícito (feixes,
hastes, pausas) recebendo id automático a cada execução do binário. Sem o
seed nos dois lados, `scene.json`/`timemap.json` "divergem" só por isso, sem
relação com este passo — quase virou um falso positivo aqui.

**Critério 3 (`scene.json`/`glyphs.json`/`meta.json` byte-idênticos).**
Confirmado nas 10 peças, comparando o binário antes e depois do patch, ambos
com `--xml-id-seed 42` para as 5 MusicXML e para as 5 MEI (mesma armadilha
do parágrafo acima). Faz sentido por construção: o patch só troca o argumento
de uma chamada a `RenderToTimemap`, que não participa da montagem da cena.

**Achado colateral, fora do escopo deste passo mas registrado aqui.** A
fixture `score_bridge/test/fixtures/erik-satie.vsb` (gerada antes de S08)
estava desatualizada em relação ao exportador atual: o `scene.json`
regenerado (com o binário de antes deste patch, sem nenhuma mudança de
código) já vinha ~20% menor, porque o exportador atual grava o run de texto
de uma classe `text` como **irmão** do `g` (`{"t":"g","class":"text",
"children":[]}` seguido de `{"t":"t",...}`), enquanto a fixture antiga tinha
o `t` **dentro** de `children`. Não há passo no plano documentando quando
essa mudança aconteceu (não é do S08, que só mexeu em bbox de glifo). A
fixture foi regenerada como parte da tarefa 3 deste passo (que já pedia
regenerá-la para embutir `measureOn`); `flutter test` (207/207) e
`flutter analyze` continuam limpos com a fixture nova, porque nenhum teste
existente dependia da forma exata dessa aninhação (só de contagens de
elementos com id e do `nodePath` do percurso completo, que não mudam de
valor com essa reestruturação). Nenhum teste precisou de número corrigido.

**Regeneração.** `.vsb` das 10 peças regenerados em `compare/out/e01b/`
(git-ignorado). Fixture `erik-satie.vsb` regenerada com `-x 42`.

**Fora do escopo, confirmado que continua assim:** `-t vsb-json`
(`RenderToBridgeJson`) não foi tocado e continua sem timemap embutido
(passa `""` para o parâmetro correspondente, inalterado).
