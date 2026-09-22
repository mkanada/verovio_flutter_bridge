# E04b — MusicXML: casa 1 sem casa 2

**Depende de:** E04a (e D-EXPAND = a) · **Decisão necessária:** não

## Objetivo

Na Maple Leaf Rag, o **1º ritornelo não é repetido**: a casa 1 está marcada
no compasso 17, a casa 2 não está, e o importador de MusicXML descarta a
repetição inteira. Esse padrão (só a casa 1 marcada, com a 2 implícita no
compasso seguinte) é comum em arquivos exportados por editores. Este passo
faz o importador tocar a repetição.

## Ler antes (só isto)

- `verovio/src/iomusxml.cpp`: o laço de `section`/`ending` (L1193-L1245) e
  `CreateExpansion` (L1322 até o fim da função).
- `.esperado` da Maple Leaf Rag e de r05 (E01a).

## Contexto que você precisa (não vá procurar, está aqui)

- Marcação da Maple Leaf Rag. Índices de `<measure>` na parte, base 0 como
  no arquivo; o compasso 0 vem antes do 1º ritornelo:

  | Índice | Marcação |
  | --- | --- |
  | 1 | `repeat forward` |
  | 16 | `ending 1 start/stop`, `repeat backward` (**sem casa 2 depois**) |
  | 18 | `repeat forward` |
  | 33 / 34 | casa 1 + `backward` / casa 2 |
  | 51 | `repeat forward` |
  | 66 / 67 | casa 1 + `backward` / casa 2 |
  | 68 | `repeat forward` |
  | 83 / 84 | casa 1 + `backward` / casa 2 |

- Em `CreateExpansion`, um grupo de casas é juntado num
  `std::map<número, iterador>`. O trecho só é repetido **a partir da 2ª
  casa** do mapa (`if (ending != endings.begin())`). Com só a casa 1 no
  mapa, o laço acrescenta a casa 1 uma vez, e a repetição some.
- A correção esperada: um grupo com **só a casa 1** é tratado como se a
  `section` seguinte fosse a casa final implícita. A sequência fica: trecho
  e casa 1, trecho de novo, pula a casa 1, segue. Nos índices base 1 do
  script de E01a, a sequência começa `1-17 2-16 18-…`.
- Com a correção: 145 ocorrências (hoje 130), 60 na 2ª passagem (hoje 45).
  Confirme contra o `.esperado`.
- E01a pode ter apontado outros casos MusicXML errados (D.C., D.S., `times`).
  **Não amplie este passo:** registre e proponha um E04c.

## O que fazer

1. Em `CreateExpansion`, tratar o grupo de casas com um único número 1, com
   `repeat backward`, como casa 1 + casa final implícita (a `section`
   seguinte).
2. Rodar `repeat-order.py` nas 5 peças MusicXML e nas partituras MusicXML de
   E01a.

## Fora de escopo

- MEI (E04a).
- Outros defeitos do importador de MusicXML (E04c, se E01a apontar).

## Critérios de aceite

1. r05 passa com `--expected`. r01, r03, r06, r08, r09, r10 e r13 não mudam
   de resultado em relação à tabela de E01a (os corretos continuam corretos).
2. Maple Leaf Rag: 145 ocorrências, 60 na 2ª passagem, sequência igual ao
   `.esperado`.
3. Gymnopédie: timemap **byte-idêntico** (com `--xml-id-seed`). Nocturne,
   Clair de Lune e Prelude também.
4. **O desenho não muda:** `-t svg` e `scene.json`/`glyphs.json` das 5 peças
   MusicXML byte-idênticos (com `--xml-id-seed`).
5. Regra do sufixo com 0 divergências na nova Maple Leaf Rag (mesma
   verificação do passo 3 de E04a).
6. Patch restrito a `iomusxml.cpp`, formatado com o `.clang-format`, e com a
   descrição de PR upstream nas notas.

## Notas de execução

**Causa raiz, mais sutil do que "o laço só repete a partir da 2ª casa".**
Isso é verdade (`CreateExpansion`, laço `for (auto ending = endings.begin();
...)`: só quando `ending != endings.begin()` é que o trecho compartilhado é
repetido), mas não bastava saber onde repetir — faltava **saber que devia**.
Um compasso com `ending type="stop"` **e** `repeat backward` no mesmo
lugar (exatamente o padrão da casa 1 sozinha) tinha a informação do
repeat **descartada**: em `Handle Barline` (perto de onde `m_sectionStop`
é montado), o código fazia
`if (m_sectionStop->m_classId == ENDING) { …só endingInfo… } else { …só
repeatInfo… }` — como o `merge()` do `<ending>` muda o `m_classId` para
`ENDING` depois de o `repeat backward` já ter posto `m_repeatInfo` (2, do
padrão `times` de um repeat sem atributo) em `m_sectionStop`, o `else`
nunca rodava para uma casa com repeat, e o `m_repeatInfo` da entrada da
casa 1 em `m_sections` ficava sempre no default (`times = 1`) — **mesmo
para a Gymnopédie**, que tem casa 1 e casa 2 e funciona hoje. A diferença
é que, com 2 casas, o laço de `CreateExpansion` nunca **precisa** olhar
`m_repeatInfo` (a repetição sai da estrutura: `endings.size() > 1`); só
quando sobra **uma** casa é que falta um sinal para saber se era "só uma
casa, sem repetir" ou "casa 1 sem casa 2 escrita". Corrigido copiando
`m_repeatInfo` para `m_sections.back().first` **sempre**, não só no
`else` — sem tocar em nada do que já funcionava (a cópia de `endingInfo`
continua exatamente igual).

**A correção em si**, em `CreateExpansion`: quando `endings.size() == 1`
e essa casa tem `m_repeatInfo.m_times > 1` (repeat de verdade, não o
default), repete o trecho compartilhado mais uma vez (o mesmo bloco de
código do `if (ending != endings.begin())`, sem laço adicional) e deixa o
`while` externo continuar para o próximo `<section>`/`<ending>` de
`m_sections` normalmente — que passa a ser, de fato, a "casa 2 implícita".
Nenhuma marca de "em qual passagem estou" foi necessária: a alternância
sai da mesma mecânica de sempre (primeira referência de um id usa o
original, as seguintes clonam).

**Critérios de aceite:**

1. r05 passa com `--expected` (`1-4 1-3 5-6`, igual a r03/r04). r01, r03,
   r06, r08, r09, r10, r13 continuam exatamente como em E01a (nenhum
   ficou diferente).
2. Maple Leaf Rag: **145** ocorrências, **60** na 2ª passagem,
   sequência `1-17 2-16 18-34 19-33 35-67 52-66 68-84 69-83 85` — bate
   com o `.esperado` derivado à mão em E01a (que já antecipava esses
   números a partir da marcação).
3. Timemap **byte-idêntico** (com `--xml-id-seed 42`, binário antes/depois
   via `git stash`): Gymnopédie, Nocturne, Clair de Lune, Prelude. Só a
   Maple Leaf Rag muda (cresce de 130 para 145 entradas de `measureOn`).
4. **O desenho não muda**: `scene.json`/`glyphs.json`/`meta.json`
   byte-idênticos nas 5 peças MusicXML.
5. `compare/scripts/check-suffix-rule.py`: 0 divergências, agora em
   **14 149** ids (subiu de 13 847: os ids novos de r05 e da Maple Leaf
   Rag expandida).
6. Patch restrito a `iomusxml.cpp` (duas mudanças pequenas: preservar
   `m_repeatInfo` ao fechar uma `<ending>`, e o `if` novo em
   `CreateExpansion`). Descrição de PR upstream:

   > **Título:** Support a lone first ending with an implicit second
   > ending in `CreateExpansion`
   >
   > **Motivo:** A measure marking both `<ending number="1">` and
   > `<repeat direction="backward"/>` — a first ending with no second
   > ending written, common in scores exported by notation editors, where
   > the repeat's second pass is just whatever comes next — made the
   > whole repeat disappear: `CreateExpansion` only repeats the shared
   > material starting from the *second* entry in the endings map, and
   > with only one ending present that never happens. The repeat
   > information on that measure was also being discarded whenever the
   > same barline closed both a repeat and an ending, which hid the
   > problem from a `m_repeatInfo.m_times` check.
   >
   > **Mudança:** stop discarding `m_repeatInfo` when a section entry is
   > also classified as an ending; in `CreateExpansion`, a lone ending
   > whose measure had a real repeat now repeats the shared material once
   > more and falls through to whatever comes next as the implicit second
   > ending.
   >
   > **Casos de teste:** `corpus/repeticoes/r05-casa-1-sozinha.musicxml`
   > (novo, downstream) and the "Maple Leaf Rag" score in the MusicXML
   > sample corpus (its first repeat, casa 1 only, was silently dropped).
   > `-t svg`/`scene.json` unaffected; only the timemap/MIDI expansion
   > changes, and only for scores with this exact pattern.

   Enviar ou não é decisão do usuário.

**Fora de escopo, como previsto:** nenhum outro defeito do importador de
MusicXML apareceu ao rodar as partituras de E01a (D.C./D.S./`times` já
funcionavam, testados em E01a/aqui de novo); nada para um E04c.
