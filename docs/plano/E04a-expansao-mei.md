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

_(preencher ao executar)_
