# G11 — Esconder um compasso inteiro: a pausa de compasso substituta

**Depende de:** G08c, G09 · **Decisão necessária:** só se a medição pedir dado
novo na cena — **D-SUM-COMPASSO** (abaixo)

> Pedido do `zywny-aprendizado` (T17, `docs/plano/T17-trilha-integrada.md`).
> Este passo, **neste repositório**, estende a §11 da spec, a referência, o
> oráculo, os vetores e a nota para o host. O código Dart é do host
> (`zywny-comum/score_bridge`, planos L02/L03 e T17) e **não** se faz aqui.

## Objetivo

A §11 esconde uma **coluna** (notas de uma pauta que começam no mesmo instante)
e põe no lugar uma pausa da figura da nota mais curta. A trilha integrada do
aprendizado esconde um **compasso inteiro, nas duas pautas**, e quer ver no
lugar **uma única pausa de compasso por pauta** (a semibreve centrada, como o
Verovio desenha o `<mRest/>`), não uma fileira de pausas pequenas que entregaria
o ritmo. Compassos escondidos vizinhos têm cada um a sua pausa de compasso.

Entregar ao host a regra, a prova e os vetores para isso, sem reabrir decisões.

## Ler antes (só isto)

- [`G07`](G07-visao-geral-nota-escondida.md) e as notas de execução de
  [`G08a`](G08a-especificacao-nota-escondida.md),
  [`G08c`](G08c-referencia-e-vetores-nota-escondida.md) e
  [`G09`](G09-nota-para-zywny-nota-escondida.md).
- Spec: §2.8 (a linha sobre `mRest` sem `dur`), §5.1 (nós `measure`, `staff`,
  `bbox`, `lines`, `gs`) e §11 inteira (regras 1 a 7).
- `docs/nota-para-zywny-sumico.md` (o que o host já recebeu).
- `compare/scripts/hide_ref.py` e `hide_oracle.py` (estender, não copiar).
- `verovio/src/view_element.cpp` (`View::DrawMRest`) e, em `measure.cpp`,
  `Measure::GetInnerCenterX`/`GetInnerLeftX`/`GetInnerRightX` (de onde sai o
  `x` da pausa de compasso).
- `zywny-aprendizado/docs/plano/T17-trilha-integrada.md`, seção "O que se
  esconde na etapa 3" (o que o host espera).

## Contexto que você precisa

- **O que o host faz** (e a §11 já cobre): `setHidden` com os ids das notas;
  a regra 1 (o que sai por nota: cabeça, haste, acidente, ponto), a regra 2
  (barra de ligação) e a regra 3 (linhas suplementares) valem como estão.
  Aqui, **todas** as notas do compasso, nas duas pautas, estão em `H`.
- **O que muda:** em vez de uma pausa por coluna (regras 4 a 7), o host precisa
  desenhar **uma pausa de compasso por pauta de desenho** do compasso.
  O `pitchpos.json` não dá `dur` para `mRest` (§2.8), e não deve: o
  glifo é sempre o da semibreve (`E4E3`, já reservado na regra 5) em qualquer
  fórmula de compasso. O que falta é **onde** (`x`, `y`) e **o que fazer com o
  que não é nota** dentro do compasso.
- **Hipótese a provar (não a assuma):** o `y`, o glifo e a escala saem da
  regra 6 já existente (`dur == 1`, `loc` do meio da pauta, `gs` do nó `staff`),
  mas o `DrawMRest` do Verovio pode escolher o `loc` de outro jeito (pauta de
  uma linha, `@loc` padrão, número de camadas). O `x` é o centro **interno**
  do compasso (entre o fim do cabeçalho — clave, armadura, fórmula, quando
  houver — e a barra final), não o centro da caixa do nó `measure`.
- **Cabeçalho no primeiro compasso do sistema.** Clave, armadura e fórmula
  estão dentro do nó `measure`/`staff`? Se o nó `measure` do `.vsb` já diz onde
  o miolo começa e acaba (ou se dá para deduzir de um filho identificável),
  o host calcula o `x`. Se não, o formato precisa de um campo novo.
- **Pausas de verdade no compasso.** Um compasso de duas pautas em que uma
  mão está em pausa (os níveis 1 a 3 do aprendizado, as mãos intercaladas)
  tem `rest` desenhadas na pauta que não toca. Esconder o compasso nessa pauta
  é um caso a decidir: a pausa de verdade fica (já é o que o aluno veria) ou
  some para dar lugar à pausa de compasso. **Proposta:** pauta cujo compasso
  não tem nenhuma nota: o host não faz nada (a pausa que existe já está lá, seja
  `rest` ou `mRest`); pauta com notas e pausas misturadas: as pausas de verdade
  somem e entra a de compasso. Confirme a proposta com a varredura e escreva o
  que sobrar como limitação.
- **O que mais mora num compasso e vaza o ritmo ou a altura:** tercina (colchete
  e número), ligaduras de prolongamento e de expressão, dedilhado, articulação,
  ornamento, arpejo, fermata, dinâmica, texto. A §11 já diz "ligadura continua
  desenhada" para a coluna; num compasso inteiro o resultado é uma ligadura
  pendurada no vazio, e o colchete da tercina mostra a figura. Faça a varredura
  e **classifique** cada um (some, fica, depende) com o número de ocorrências
  no corpus; o que deve sumir precisa de uma regra de "dono" como a das linhas
  suplementares, usando só o que a cena já tem (ids, ancestrais).
- **Anacruse e compasso incompleto.** A pausa de compasso do Verovio num
  compasso curto é de outro tamanho? Registre; o aprendizado não gera anacruses,
  mas o formato tem de dizer o que a regra faz (provavelmente: sem pausa
  substituta, como `dur` ≥ 128 hoje).
- **Corpus.** O caso real é a leitura do aprendizado, não os hinos. Traga ao
  menos 4 MusicXML do gerador (peça-os ao usuário ou gere com
  `just amostra <passo> --seeds 1` no `zywny-aprendizado`, que escreve o MusicXML):
  um passo de mão intercalada (2c), um com a melodia na esquerda (4b), um com
  tercinas e outro com 6/8 da fase 2, mais compassos com quiáltera. Registre a
  origem no `corpus/README.md`, como o G08c fez com os hinos.

## O que fazer

1. **Medir antes de escrever.** Para uns 200 compassos do corpus (os do G08c
   mais os novos), comparar o `mRest` que o Verovio desenha com o que a regra
   proposta calcularia a partir do `.vsb` já existente: glifo, `y`, escala e `x`.
   Saída: uma tabela de erro em unidades de viewBox, separada por
   (primeiro compasso do sistema, compasso comum, último compasso, compasso
   com armadura ou fórmula trocada no meio).
2. **Decidir D-SUM-COMPASSO** (com o usuário, só se o passo 1 falhar na
   tolerância de 0,5 unidade): o `x` do centro interno **não** se deduz do que
   o `.vsb` tem hoje. Plano B: um campo aditivo no nó `measure`
   (`inner: [x0, x1]` no mesmo referencial de `bbox`, vindo de
   `GetInnerLeftX`/`GetInnerRightX`), `version` continua `1`. Isso mexe no
   C++ (`verovio/`) e obriga o host a **refazer a `libverovio`** de Linux,
   Android e Web de novo — diga isso ao usuário antes de decidir.
3. **Spec §11, regra 8** (nova): "Pausa de compasso substituta". Entradas (os
   ids de todas as notas do compasso, a pauta, o nó `measure`), o glifo
   (`E4E3`), `x`, `y`, escala, o que acontece com pausas de verdade, com o
   compasso sem nota e com `n ≠ 5`; as regras 4 a 7 ficam para a coluna. Entrada
   no histórico de revisões. Se houve campo novo, §5.1 e o schema também.
4. **Classificar o que vaza** (a varredura do contexto): tabela na §11 com o
   que some e o que fica, e a regra de dono para o que some. Atualize
   "O que o host não deve fazer" e "Limitações da v1".
5. **Referência** (`compare/scripts/hide_ref.py`): `measure_stand_in(...)`, na
   mesma convenção da `stand_in` (entradas, saída `{g, x, y, sx, sy}` por
   pauta) e a regra de "dono" do que vaza.
6. **Oráculo** (`hide_oracle.py`): duas provas, como no G08c.
   - *Sem rodar o Verovio de novo:* todo `mRest` de verdade (pauta de uma
     camada) bate com a regra: glifo, `y`, escala e `x`.
   - *Rodando o Verovio:* numa cópia da peça, trocar **o conteúdo de todo o
     compasso, em cada pauta** por `<mRest/>` e conferir que o Verovio desenha
     o mesmo que a regra calcula. O `x` aqui **se compara**, porque o miolo do
     compasso muda de largura mas o centro interno não deve mudar de dono;
     se mudar (a troca de notas por pausa estreita o compasso), registre e
     defina o `x` pelo compasso **original** (o que o host vê), com o desvio
     medido na nota.
7. **Vetores** (`docs/formato/sumico/vetores.json`): casos novos de compasso
   (`esperado.measureStandIn`), no mesmo formato, mais `.vsb` novos em
   `docs/formato/sumico/` (um por cenário: mão intercalada, melodia na
   esquerda, tercina, 6/8, primeiro compasso do sistema). Tolerância 0,5.
8. **Nota para o host**: acrescentar uma seção a
   `docs/nota-para-zywny-sumico.md` (o que mudou, a regra 8, os vetores novos,
   as medições e as limitações). **Dizer claramente** se é preciso refazer a
   `libverovio` (só se o passo 2 trouxe campo novo).
9. **Fixtures no host:** copiar `docs/formato/sumico/` para
   `zywny-comum/score_bridge/test/fixtures/sumico/` (sobrescreve os da G09),
   rodar `cd score_bridge && flutter test` lá e conferir que continua verde
   (ainda sem código novo).
10. **Planos do host:** em `zywny-aprendizado`, atualizar o T17 onde as
    medições mudarem um fato (item 0 e "Pendente"); em `zywny-musicas`,
    L02/L03 só se a regra 8 também servir ao decorar. Linha da fase no
    `README.md` deste plano.

## Critérios de aceite

1. Spec §11 com a regra 8 e a classificação do que vaza, `version` ainda `1`;
   revisão no histórico.
2. A referência e o oráculo rodam sobre o corpus (hinos, o `s01` e os MusicXML
   do aprendizado): **0 divergências** de glifo, `y` e escala, e `x` dentro de
   0,5 unidade, ou os desvios contados e justificados.
3. Os vetores novos conferem; a suíte do host continua verde com as fixtures
   novas.
4. Se houve campo novo na cena: C++ e `compare/` verdes, `libverovio`
   regenerada **neste repositório**, e a nota diz ao host o que refazer.
5. `docs/nota-para-zywny-sumico.md` atualizada; o usuário avisado de que o
   trabalho segue no `zywny-comum` (T17, item 0) e do que precisa ser refeito.

## Fica fora

- O código Dart (esconder, pausa de compasso, a tela): T17 e L02/L03.
- Pausa de compasso com várias vozes em camadas (`GetOptimalLayerLocation`):
  limitação, como na coluna.
- Pausa multi-compasso (`multiRest`).

## Notas de execução

Concluído em 2026-11-05. Mexeu em `verovio/` (4 arquivos, +20 linhas; o desenho e o SVG não mudam) e
nas `libverovio` de Linux, Android e Web. Scripts novos em `compare/scripts/`: `g11_swap.py` (copia MEI com
compassos trocados por `<mRest/>`), `g11-sweep.py` (o que vaza), `g11-make-vectors.py` (os 15 vetores e os
PNGs); `hide_ref.py` e `hide_oracle.py --measures` estendidos. Saídas em `compare/out/g11/`.

- **Medição (passo 1) e D-SUM-COMPASSO (passo 2).** 2 642 `mRest` de 34 peças (todos os compassos de cada
  pauta trocados por `<mRest/>`, 1 379 compassos de sistema). Sem cabeçalho: `x` exato pelo que o `.vsb` já
  tinha (1 004 compassos, 0). Com cabeçalho (o primeiro de cada linha): o Verovio centra a partir de uma
  margem de 87 a 90 unidades depois do cabeçalho (125 se só há clave) que a cena não grava; usando a borda
  mais larga das duas pautas o erro do centro chegou a **1,36** unidade (81 de 122 compassos passam de 0,5),
  e a **18,3** com a borda de cada pauta. **Corrigi uma medição minha** durante a sessão: eu tinha dito "até
  ~190 unidades" misturando compassos com barra de repetição logo depois do cabeçalho (que têm regra exata)
  e a borda de uma pauta só. O usuário decidiu pela **opção 1: campo `inner: [x0, x1]` no nó `measure`**,
  mesmo com o erro real pequeno (~0,14 px).
- **C++.** `BridgeNode::inner`/`hasInner` (`bridgegeometry.h`), preenchido em `AnnotateNodeGeometry` com os
  mesmos operandos de `Measure::GetInnerCenterX` (`GetDrawingX() + GetLeftBarLineRight()` e
  `GetRightBarLineLeft()`; o plano chamava `GetInnerLeftX/RightX`, que não existem: usei os getters públicos
  que `GetInnerCenterX` já usa), gravado por `bridgewriter.cpp`. **A/B contra o binário anterior** (stash das 4
  edições): em 70 `.vsb` (todas as fontes do corpus) todos
  os arquivos do zip são byte-idênticos menos `inner` e a string de versão; 96 páginas SVG idênticas. A varredura de
  paridade do corpus (`compare-corpus.sh`, 34 páginas, Skia) rodou limpa (exit 0); o CSV versionado em
  `compare/corpus/resultado.csv` é de 2026-09-20, anterior a P01b, então não serve de linha de base (por isso o
  A/B). `flutter test` em `compare/`: 4 passam. Teste novo em `verovio/bindings/dart` (6 passam): todo nó
  `measure` traz `inner` e, numa `mRest` de verdade, o centro bate.
- **`libverovio` regenerada** (`build_linux_so.sh`, `build_android_so.sh arm64-v8a x86_64`,
  `build_wasm.sh`; o literal `"inner":[` está nas três; no wasm conferido rodando-o no node: 7 `inner` no JSON
  de `g11-compassos-especiais.mei`). Os `.so` e `android-libs/` são git-ignorados.
- **Prova 3 e 4 (`hide_oracle.py --measures`).** Prova 3: 11 `mRest` de verdade (pauta de uma camada), 0
  divergências. Prova 4: **5 170** pausas desenhadas pelo Verovio contra a regra, **0 divergências** de `x`,
  `y`, glifo e escala (|dx| máximo 0,00), por categoria: 612 primeiro do sistema, 3 699 comum, 742 último, 42
  primeiro com barra de repetição à esquerda, 54 só barra à esquerda, 21 cabeçalho no meio; mais 2 compassos
  de 4/2, onde o Verovio desenha `E4E2` e a regra, coerente, não dá pausa. **Anacruse** (1 semínima): o Verovio
  desenha a mesma semibreve, então a regra vale igual (o plano esperava "sem pausa": não). O oráculo não
  inclui o `x` "do compasso original": como `inner` é lido do compasso, a pausa do host cai no centro do
  compasso que o aluno vê, sem o desvio de largura que a troca de notas por pausa causaria.
- **O que vaza (passo 4, `g11-sweep.py`).** 70 partituras, 124 páginas, 1 517 compassos. Escondendo todos os
  compassos de cada página sobram desenhados só os nós da coluna "fica" (**0 vazamentos**). Achados que
  moldaram a regra: ligaduras que cruzam a quebra de sistema são filhas do `system` e **sem `id`** (116 `tie`,
  25 `slur`, 4 `phrase`): sem contá-las, sobravam no ar; o dono de um controle (`tie`, `slur`, `phrase`,
  `arpeg`, `beamSpan`) é o conjunto de compassos que a caixa dele toca (primeiro traço de linha de cada
  compasso, folga 1), e some se todos estão escondidos; **o `beamSpan` deixa de ser limitação**. Proposta do
  plano **confirmada**: pauta sem nota fica como está (35 pautas de compasso, mais 11 só `mRest`); pauta com
  notas e pausas perde as pausas (732). Pautas por compasso: 2 140 só notas.
- **Spec.** §5.1 (`inner`), **§11.2 regra 8** com a tabela do que some/fica e as contagens, histórico de
  revisões; schema (`measure.inner`, validado contra `scene.json`: 0 erros).
- **Vetores.** `vetores.json` ganha a chave **`casosCompasso`** (15 casos, m01 a m15), à parte de `casos`
  porque os testes do host leem `casos[*].coluna`: a chave nova mantém a suíte verde sem código novo. As
  contas à mão de m01 a m04 (`inner` → `x`) saíram iguais ao número da referência na primeira passada; as
  contagens de notas e de pausas que somem conferem com a contagem independente no MEI da fonte (0
  divergências em 15). PNGs em `compare/out/g11/vec/m01…m15-*.png` (olhados: m07, m13). `.vsb` novos em
  `docs/formato/sumico/`: `g11-{mao-intercalada,melodia-esquerda,tercina,6-8,especiais}.vsb`,
  `f06-mudanca-armadura.vsb`; os 4 de G08c regerados com `inner` (os 11 casos de coluna continuam 0
  divergências). **Corpus:** 35 MusicXML do `zywny-aprendizado` (commit `8fec648`, `dart run
  tool/sight_sample.dart`) e `g11-compassos-especiais.mei` em `corpus/sumico/`, origem em `corpus/README.md`.
- **Host.** Fixtures copiadas para `zywny-comum/score_bridge/test/fixtures/sumico/` (10 `.vsb` e o
  `vetores.json`); `cd score_bridge && flutter test` no `zywny-comum`: **365 passam, 7 ignorados, 0 falham** (2 min 30 s; ainda sem código novo para a regra 8, a suíte lê só `casos`). T17 (`zywny-aprendizado`) atualizado: item 0 e "Pendente". L02/L03
  do `zywny-musicas` não mudam (a regra 8 não serve ao decorar, que esconde colunas). `docs/nota-para-zywny-sumico.md`
  seção 9 escrita, dizendo que é preciso refazer a `libverovio` de novo.
