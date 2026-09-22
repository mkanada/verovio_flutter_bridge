# E04a — Expansão de MEI com várias `section` e com `<ending>`

**Depende de:** E01a · **Decisão necessária:** **sim — D-EXPAND** (pare e
pergunte antes de escrever código; bloqueia também E04b)

## Objetivo

Hoje, **4 das 5 peças MEI do corpus tocam sem repetir**, embora tenham
ritornelo. O gerador de expansão do Verovio recusa partituras com mais de uma
`<section>` e ignora `<ending>`. O `zywny` abre MEI, e o `ScorePlayer` toca a
peça errada, sem aviso nenhum ao usuário.

Este passo corrige o gerador **no fork**, sem tocar em nada do desenho.

## Decisão necessária — D-EXPAND

**Corrigir a geração de expansão dentro do fork do Verovio?**

- **(a) Sim, no fork, isolado (recomendado).** A mudança fica em
  `expansionmap.cpp`/`.h` (E04a) e em `MusicXmlInput::CreateExpansion`
  (E04b). `View`, `SvgDeviceContext` e `BBoxDeviceContext` não são tocados.
  O desenho não muda: para `-t svg`/`-t vsb`, a expansão só acontece no
  `m_midiDoc` (a cópia usada para o timemap), e o critério 3 prova isso byte
  a byte. O patch sai pronto para um PR upstream em `rism-digital/verovio`;
  enviar ou não é decisão sua.
- **(b) Não corrigir.** Documentar a limitação. O `zywny` teria de avisar
  que partituras MEI com várias `section` tocam sem repetição, ou converter
  o MEI antes.

## Ler antes (só isto)

- `verovio/src/expansionmap.cpp` inteiro (477 linhas): `Expand` (L49),
  `GeneratePredictableIDs` (L340), `GenerateExpansionFor` (L367),
  `CreateSection` (L425) e os `IsRepeat*` (L441-L476).
- `verovio/src/doc.cpp`: `Doc::ExpandExpansions` (L1660).
- `verovio/src/toolkit.cpp`: `SetMidiDoc` (L283).
- `verovio/src/iomusxml.cpp`: `CreateExpansion` (L1322), como referência de
  um gerador que já trata casas, D.C. e D.S.

## Contexto que você precisa (não vá procurar, está aqui)

- `GenerateExpansionFor(score)`:
  - sai com aviso se a partitura tem conteúdo editorial ou **mais de uma
    `section`** (`FindAllDescendantsByType(SECTION).size() > 1`);
  - percorre só os filhos **diretos** da única `section` que são `measure`.
    Um `<ending>` é pulado, e um `rptend` dentro de uma casa nunca é visto;
  - a cada `rptend` (à direita de um compasso, ou à esquerda do seguinte)
    move o trecho `[início da repetição, compasso]` para uma `section` nova e
    põe a referência dela **duas vezes** no `plist` do `<expansion>`.
- As 4 peças MEI com ritornelo têm cada trecho numa `section` própria,
  irmãs na partitura (padrão do conversor que as gerou):

  | Peça | `section` na partitura | Ritornelos (compassos, base 1) | Ocorrências esperadas |
  | --- | --- | --- | --- |
  | Mazurka Op. 6 nº 1 | 3 | `rptend` 17; `rptstart` 18 … `rptend` 42 | 117 (75 compassos) |
  | Butterfly | 2 | `rptend` 6 (do início) | 48 (42) |
  | Little bird | 3 | `rptend` 9; `rptstart` 10 (anacruse) … `rptend` 30 | 69 (39) |
  | Scarlatti | 2 | `rptend` 31 (do início) | 99 (68) |

  (O `grep -c '<section'` dá uma a mais em cada uma, a do `<incip>` no
  `meiHead`, que não entra na partitura. As sequências exatas estão nos
  `.esperado` de E01a.)
- A Étude (MEI, sem ritornelo, uma `section` na partitura e 67 compassos)
  tem que continuar tocando igual.
- Para `-t timemap`, `-t midi` e `-t expansionmap`, o **documento principal**
  é expandido (`Doc::ExpandExpansions` no import). Para `svg`/`vsb`, só o
  `m_midiDoc`. Um erro aqui pode, portanto, mudar a saída `-t mei` ou `-t
  timemap`, mas não o desenho.
- Os ids dos clones seguem `GeneratePredictableIDs` (`-rend<N>`). E02a
  depende disso: não mude a convenção.

## O que fazer

1. Estender `GenerateExpansionFor` para:
   - **várias `section` consecutivas** na partitura: tratar os compassos em
     ordem de documento, atravessando as fronteiras de `section`. Uma
     repetição pode começar numa `section` e terminar em outra; o `rptstart`
     pode estar na primeira de uma `section` nova;
   - **`<ending>`**: `rptend` dentro da casa 1 repete o trecho sem a casa 1 e
     segue para a casa 2 (mesma semântica do `CreateExpansion` do MusicXML);
   - manter a recusa para conteúdo editorial e o `m_isProcessed`.
2. Não mexa em `Expand` nem em `GeneratePredictableIDs`, a menos que seja
   inevitável. Se for, justifique nas notas.
3. Rodar de novo o `repeat-order.py` (E01a) e a verificação da regra do
   sufixo (o script do critério 2 de E02a, se E02a já foi executado; senão,
   compare os ids `-rendN` do timemap com o `-t expansionmap`, com o mesmo
   `--xml-id-seed`).

## Fora de escopo

- D.C./D.S./coda/fine em MEI (`repeatMark@func`): o corpus não tem. Registre
  o comportamento das partituras de E01a, se houver, e não implemente.
- MusicXML (E04b).
- Modo "sem repetições": `--expand-never` **não** serve, porque toca a ordem
  notada com as duas casas (Gymnopédie: 289 notas em 111 s, contra 469 em
  185 s expandida). Um modo correto precisaria de uma segunda expansão, que
  fica fora da fase E.

## Critérios de aceite

1. `repeat-order.py --expected` passa em r02, r04, r07, r11 e r12 (E01a).
2. Corpus MEI: Mazurka 117, Butterfly 48, Little bird 69 e Scarlatti 99
   ocorrências, cada uma batendo com o seu `.esperado`. O aviso `An expansion
   cannot be generated with more than one section` some das quatro. Étude
   inalterada.
3. **O desenho não muda:** `-t svg` das 10 peças e `scene.json`/`glyphs.json`
   do `-t vsb` (MusicXML com `--xml-id-seed`) byte-idênticos antes e depois.
4. Timemap das 5 peças MusicXML **byte-idêntico** (com `--xml-id-seed`), sem
   regressão fora do MEI.
5. `-t expansionmap` das 4 peças MEI deixa de ser `{}`, e a regra do sufixo
   dá 0 divergências nelas (verificação do passo 3).
6. Patch restrito a `expansionmap.cpp`/`.h`, formatado com o
   `.clang-format` do fork, e com uma descrição de PR upstream nas notas
   (título, motivo e casos de teste).

## Notas de execução

**D-EXPAND resolvida pelo usuário: (a) sim, no fork, isolado.**

**`GenerateExpansionFor` reescrito em torno de uma lista achatada.** Em vez
de operar só nos filhos diretos de uma única `<section>`, a função agora:

1. Coleta todas as `<section>` da partitura (`score->FindAllDescendantsByType(SECTION)`
   — a mesma chamada que antes só servia para o bloqueio de ">1 seção").
2. Achata os filhos diretos de cada uma (`Measure`/`Ending`, em ordem de
   documento) numa única `ListOfObjects` (`std::list`, iteradores estáveis
   mesmo com `CreateSection` mutando a árvore).
3. Percorre essa lista com a **mesma lógica de sempre**
   (`IsPreviousRepeatEnd`/`IsRepeatStart`/`IsNextRepeatStart`/`IsRepeatEnd`)
   para compassos soltos — agora atravessando fronteiras de `<section>` sem
   perceber a diferença — mais um ramo novo para grupos de `<ending>`
   consecutivos.

**`<ending>` (casas).** Ao encontrar um grupo de `<ending>` consecutivos,
verifica se a **primeira casa** tem um compasso com `rptend`
(`EndingHasRepeatEnd`, novo). Se tiver, o trecho compartilhado antes das
casas vira uma `<section>` nova (via `CreateSection`) e o `plist` recebe
`[compartilhado, casa 1, compartilhado, casa 2, …, casa N]` — a alternância
de refs, não uma segunda extração. Isso funciona **sem tocar em `Expand()`
para esse caso**: como cada ref nova é usada no lugar (1ª vez) e clonada
logo depois do `prevSect` anterior (2ª vez em diante), o `plist` alternado
já posiciona cada casa exatamente onde precisa, porque as casas nunca saem
do lugar onde já estavam na árvore (só o trecho compartilhado é clonado).
Verificado à mão com r03/r04 antes de rodar: bate com o resultado real.

**`Expand()` precisou de uma mudança (a exceção "a menos que inevitável"
do passo).** Uma repetição que atravessa `<section>` pode extrair seu
trecho compartilhado para dentro de uma seção que **não** é descendente de
`expansion->GetParent()` (a 1ª seção da partitura, de onde o `<expansion>`
sempre é lido) — `parent->FindDescendantByID(id)` falhava
("Element referenced in @plist not found") para qualquer ref criada a
partir da 2ª seção em diante. Corrigido com um **fallback aditivo**: se a
busca em `parent` falhar, busca de novo a partir do `Score` ancestral,
antes de desistir. Para todo caso anterior a E04a (uma seção só), a busca
em `parent` **sempre** dá certo, então o fallback nunca é exercitado — 0
mudança de comportamento no caminho antigo (testado: nenhuma peça
MusicXML mudou nada, ver critério 3/4). `GeneratePredictableIDs` não foi
tocado.

**Por que `CreateSection` não precisou de mais mudança para o caso
cross-section:** ela já pegava o pai **atual** de `*first`
(`(*first)->GetParent()`), então inserir a seção nova "onde o trecho
compartilhado estava" já funciona não importa de qual `<section>` original
o trecho veio — o problema era só a *busca* em `Expand()`, não a
*extração*.

**`.clang-format` do fork:** não existe no repositório (`find` não achou
nenhum, e a máquina não tem `clang-format` instalado) — a instrução do
`CLAUDE.md` pressupõe um arquivo que este fork não trouxe do
`verovio_lottie`. O patch foi formatado à mão para bater com o estilo ao
redor (2 espaços, `//` de uma linha para comentários curtos, sem chaves em
`if` de uma linha só, como o resto de `expansionmap.cpp`).

**Critérios de aceite:**

1. `repeat-order.py --expected` passa em r02, r04, r07, r11, r12 (E01a).
2. Corpus MEI: Mazurka **117**, Butterfly **48**, Little bird **69**,
   Scarlatti **99** ocorrências, cada uma batendo com o `.esperado`. O
   aviso `An expansion cannot be generated with more than one section`
   sumiu das quatro (não sobrou nenhuma peça do corpus emitindo esse
   aviso). Étude (MEI, uma seção, sem repetição) inalterada: `1-67`.
3. **O desenho não muda**: comparado o binário antes/depois (`git stash`)
   nas 10 peças (MusicXML com `--xml-id-seed 42`): `scene.json`,
   `glyphs.json` e `meta.json` **byte-idênticos** nas 10.
4. Timemap das 5 peças MusicXML **byte-idêntico** (mesmo `--xml-id-seed`):
   Gymnopédie, Maple Leaf Rag, Nocturne, Clair de Lune, Prelude. O Étude
   (MEI sem repetição) também ficou idêntico — só as 4 peças MEI **com**
   repetição tiveram o timemap alterado (crescendo, do jeito esperado).
5. `-t expansionmap` das 4 peças MEI deixa de ser `{}`.
   `compare/scripts/check-suffix-rule.py` (E02a) confirma **0
   divergências em 13 847 ids** no corpus inteiro + as 13 partituras de
   E01a (antes de E04a: 12 388, sem os ids novos das 4 peças MEI que
   passaram a expandir).
6. Patch restrito a `expansionmap.cpp`/`.h` (mais o fallback de duas
   linhas em `Expand()`, justificado acima). Descrição de PR upstream:

   > **Título:** Support repeat generation across multiple `<section>` and
   > with `<ending>` (voltas)
   >
   > **Motivo:** `ExpansionMap::GenerateExpansionFor` refuses to generate a
   > repeat expansion for any score with more than one top-level
   > `<section>`, and silently ignores measures inside an `<ending>`. Both
   > patterns are common in MEI produced by MusicXML-to-MEI converters
   > (one `<section>` per formal section, `<ending>` for first/second
   > endings), so such scores play back (MIDI, timemap, `-t expansionmap`)
   > without any of their written repeats.
   >
   > **Mudança:** `GenerateExpansionFor` now flattens the direct
   > measure/ending children of every `<section>` in document order before
   > looking for repeat barlines, so a repeat spanning (or starting at) a
   > section boundary is still found. A run of `<ending>` elements whose
   > first casa ends in a repeat barline is expanded into
   > `[shared, ending 1, shared, ending 2, …]`. `Expand()` gets a one-line
   > fallback: if the referenced id is not a descendant of the expansion's
   > own parent section, search the whole score before giving up (needed
   > because a repeat can now create its child section under a *different*
   > original `<section>`).
   >
   > **Casos de teste:** `corpus/repeticoes/r02/r04/r07/r11/r12` (novas
   > partituras mínimas de um projeto downstream, um caso por padrão:
   > seção única, `<ending>` sem `<expansion>` codificada, quebra de
   > página no meio de uma repetição, várias `<section>` em sequência,
   > `<expansion>` codificada explícita); mais 4 peças reais do
   > `MEI Sample Collection` (Mazurka, Butterfly, Little bird, Scarlatti)
   > que já tinham repetição encoded incorretamente ignorada. Nenhuma
   > mudou de desenho (`-t svg` byte-idêntico); só o timemap/MIDI/
   > `-t expansionmap`.

   Enviar ou não ao `rism-digital/verovio` é decisão do usuário — o patch
   está pronto, mas nada foi submetido.

**Fora de escopo, como previsto:** D.C./D.S./coda/fine em MEI (o corpus
não tem; não implementado). MusicXML (E04b, próximo passo).
