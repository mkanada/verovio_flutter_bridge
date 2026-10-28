# G10 — Marcas de expressão no `midi.json`: dinâmica, staccato e ligadura

**Depende de:** G01 · **Decisão necessária:** D-MARCAS (a forma, abaixo; não
decidida)

> Pedido aberto pelo `zywny-aprendizado` no passo **EX07** (medidores de
> execução: legato, staccato, dinâmica, acentos). O EX07 segue sem isto: põe as
> marcas por outro caminho (`ExpressionMarks`, vazio nas partituras de autor).
> Este passo só escreve o que falta no bridge; a leitura no Dart fica lá.

## Objetivo

O `midi.json` (G01) diz **o que soa**: altura, início, fim, velocity e pedal.
Não diz **como** soa a partitura escrita. Para medir a execução do aluno
(legato, staccato, dinâmica e acentos), o `zywny` precisa saber, por nota:

- a dinâmica escrita (p, mf, f… e os trechos de crescendo e diminuendo);
- se a nota é staccato;
- se a nota é acentuada (`<accent>` escrito);
- quais pares de notas são ligados por **ligadura de expressão** (a `<slur>`
  do MusicXML, não a ligadura de valor, que o `midi.json` já une).

## Evidência (medida em 2026-10-28)

Partitura de teste: `G10-marcas-de-teste.musicxml` (neste diretório), dois
compassos de semínimas: C5 `p`, D5 em staccato, E5→F5 com `<slur>`; no
compasso 2, G5 `f`, A5 em staccato, B5 mínima. Renderizada pelo
`renderToBridgeJson()` do fork (o mesmo `midi.json` que o `.vsb` leva):

| O que se pergunta | Resposta |
| --- | --- |
| A velocity segue `p` e `f`? | **Não.** As 7 notas saem com `v: 90`, nos dois trechos. |
| A nota em staccato é mais curta? | **Não.** D5 (`on` 500, `off` 1000) e A5 (`on` 2500, `off` 3000) duram a semínima inteira. |
| A ligadura de expressão aparece? | **Não.** `midi.json` não tem campo de ligadura além de `tied` (que é de valor): E5 e F5 saem sem nenhuma marca comum. |

Conclusão: as três marcas se perdem no exportador MIDI. O `@vel` explícito é o
único caminho que a velocity tem hoje (ver `midifunctor.cpp`, `VisitNote`).

## Ler antes (só isto)

- `docs/plano/G01-gravador-de-notas-midi.md`: o gravador de eventos e o
  molde do `midi.json` (aditivo, `version` continua `1`).
- `verovio/src/midifunctor.cpp`, `VisitNote`: onde a velocity e a duração são
  decididas. Ver se o `Dynam`, o `Artic` (staccato, accent) e o `Slur` já
  chegam ao functor antes de a nota ser emitida.
- `docs/formato/especificacao-v1.md` §2.7 (`midi.json`).

## Decisão necessária (D-MARCAS)

Recomendação: um campo **`marks`** aditivo no `midi.json`, com ids de
`xml:id` de origem (como o resto do arquivo):

```json
"marks": {
  "dynamics": [{ "id": "...", "timeMs": 0, "level": "p" }],
  "wedges":   [{ "startMs": 0, "endMs": 1000, "crescendo": true }],
  "staccato": ["<id>", "..."],
  "accents":  ["<id>", "..."],
  "slurs":    [["<id de a>", "<id de b>"], "..."]
}
```

Alternativa: um `marks.json` à parte no `.vsb`, com a mesma forma. A
recomendação é o campo no `midi.json`, porque o `zywny` já o lê e não precisa
de um arquivo novo. Quem decide é o usuário.

## O que fazer

1. Decidir D-MARCAS (o usuário).
2. Medir no fork, com `G10-marcas-de-teste.musicxml`, a origem de cada marca
   (o `Dynam`, o `Artic`, o `Slur`) no `midifunctor.cpp`.
3. Gravar as marcas no gravador do G01, sem mudar nenhuma nota do `.mid`
   (o `midi.json` novo é só um campo a mais).
4. Schema e §2.7 da especificação: o campo novo, marcado como opcional.
5. Teste: o `midi.json` da partitura de teste traz `p` em C5, `f` em G5,
   staccato em D5 e A5, a ligadura E5→F5 e nenhuma nota nova.

## Fora de escopo

- Mudar a velocity do `.mid` (o som continua o que o Verovio toca hoje; o
  `marks` é só para medir). Dinâmica que soa no áudio é outro passo.
- O staccato que **encurta** a nota no MIDI (o som). Isto é só a marca.
- A leitura das marcas no Dart (é o `zywny`: EX07 e EX08).

## Critérios de aceite

1. `midi.json` da partitura de teste traz as marcas do item 5, e o `.mid`
   continua byte a byte igual ao de antes (a velocity fica 90).
2. Schema (`docs/formato/schema-v1.json`) e §2.7 aceitam o campo novo; um
   leitor antigo continua lendo o arquivo.
3. A suíte do bridge continua verde.

## Notas de execução

(pendente: nenhum passo executado. Pedido aberto em 2026-10-28, pelo EX07 do
`zywny-aprendizado`.)
