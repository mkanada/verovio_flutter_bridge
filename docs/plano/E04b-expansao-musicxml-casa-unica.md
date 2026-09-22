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

_(preencher ao executar)_
