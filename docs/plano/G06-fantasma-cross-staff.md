# G06 — Fantasma cross-staff: pauta onde a nota cabe, 8va só no extremo

**Depende de:** G04d, G05 · **Decisão necessária:** sim — fechar a métrica de
"cabimento" e os desempates abaixo antes de codar

**Origem:** verificação visual no `zywny` (Y01): nota grave tocada contra a
clave de sol aparece **na clave de sol com 8vb**, quando caberia —
lendo-se naturalmente — **na clave de fá, sem marcador**. Regra pedida:
a fantasma vai para a pauta onde a altura cabe; `8va`/`8vb`/`15ma`/`15mb`
só nas extremidades do sistema (acima da primeira pauta, abaixo da última)
ou com pauta única (comportamento atual).

## O que muda na §10 (proposta)

1. **Alvo (pauta e coluna)** — hoje: candidato com menor `|k − ref|`, pauta
   `S` do alvo. Proposta: para cada **pauta distinta** presente em `E`,
   calcular o `loc` da tecla nessa pauta (com o contexto da pauta — item 3)
   e as **linhas suplementares** resultantes; a fantasma vai para a pauta
   com **menos suplementares**. Desempates, nesta ordem: menor `|k − ref|`
   (como hoje); `ref` maior (o de cima, como hoje).
2. **Coluna (x)** — a do candidato mais próximo em `|k − ref|` **dentro da
   pauta escolhida** (hoje é global; com a pauta fixada primeiro, o alvo
   passa a ser por pauta). Colisão (passo 7) inalterada, já é por pauta.
3. **Contexto da pauta** — `co`/`sh`/`key`/`acc` do evento daquela pauta em
   `E` mais próximo de `k` (mesma coluna, mesma pauta: `key`/`acc`/`co`
   coincidem; `sh` pode divergir entre vozes — usar o do candidato mais
   próximo). Grafia (passo 3) e acidente (passo 6) usam esse contexto.
4. **Alcance (passo 5)** — deslocamento de oitava só se o **melhor**
   cabimento ainda passar de 4 suplementares (extremo do sistema), ou se o
   sistema tem **pauta única** (regra atual integral). Trava em 4 linhas
   além de `m = 2`: inalterada.
5. **Pauta única ou empate total** — cai no comportamento atual
   (menor `|k − ref|`, desempate para cima).

Exemplo (Satie, mão direita toca, tecla A2=45): hoje `8vb` na clave de sol;
novo: `loc` 1 na clave de fá, sem marcador. Tecla E7=100: continua `8va` na
clave de sol (extremo do sistema).

## Sem nativo novo — a confirmar

O `pitchpos.json` tem contexto **por evento**, e o host decide `E` (§10:
"o host converte... e decide quais são os esperados"). Proposta: o host
alimenta `E` com **as notas do passo + as pausas de todas as pautas nesse
instante** (`restsOn` do timemap, já pedido com `includeRests`; pausas têm
evento `t: "r"` com `co`). Pausas continuam candidatas (a §10 já prevê) e
nunca viram obrigação de tocar — são só contexto de pauta para o
cabimento. Se `restsOn` não cobrir algum caso (pauta sem evento algum no
instante), aí sim expor contexto por pauta no nativo (`bridgepitchpos.cpp`)
— decidir na implementação, após varrer o corpus com o oráculo.

## O que fazer (neste repositório)

1. Fechar as decisões acima (métrica, desempates, `sh` entre vozes).
2. Estender `compare/scripts/ghost_ref.py::ghosts` (passos 1 e 5) + `--self-test`.
3. Novos vetores em `docs/formato/fantasma/vetores.json` (reaproveitar
   `satie.vsb`: esperados nas duas pautas + teclas no vão; caso de pauta
   única mantendo `8vb`; empate de cabimento) via `g04d-make-vectors.py`,
   conferindo o `resumo` à mão como em G04d.
4. Spec §10 (passos 1 e 5) + exemplo, registro no histórico de revisões
   (aditivo: `version` continua 1; sem campo novo no `.vsb` se o item
   "sem nativo novo" se confirmar).
5. Copiar vetores/fixtures para o `zywny` (molde G05).

## Porta no `zywny` (fora deste repositório, registrado aqui)

- `score_bridge/lib/src/ghost.dart`: mesma mudança nos passos 1 e 5;
  `ghost_test.dart`/`ghost_layer_test.dart` contra os vetores novos.
- `PracticeController.setExpected`: passar notas do passo + pausas das
  demais pautas no instante (lookup `restsOn` por `onMs`; `sceneIdOf`
  resolve). Só alimenta a fantasma — sem efeito na avaliação.
- Abertos lá: cue/grace entre pautas, sistemas com 3+ pautas, `sh`
  divergente entre vozes (segue o decidido aqui).

## Fora de escopo

- Mudar `pitchpos.json`/schema sem a confirmação do item "sem nativo novo".
- Nota desenhada cross-staff (`f04`, atributo `staff`): inalterada.

## Notas de execução

Concluído em 2026-09-30 (neste repositório: itens 1-5; a porta Dart é
trabalho do `zywny`, pendente lá).

**Decisões fechadas com o usuário (2026-09-30)**, todas pela proposta do
passo: (a) cabimento = menos linhas suplementares **brutas** (antes de 8va),
desempates `|k − ref|` e depois `ref` maior; (b) contexto da pauta = evento
dela mais próximo de `k` (`sh` divergente: o do mais próximo), grafia e
acidente nesse contexto, coluna do mais próximo na pauta escolhida, colisão
inalterada; (c) 8va/15ma só no extremo do sistema ou com pauta única em `E`
(empate total = regra atual, pauta única = `E` com uma só pauta distinta);
(d) "sem nativo novo primeiro": varrer o corpus antes de mexer no C++.

**Varredura sem-nativo-novo** (script descartável, 18 peças, `.vsb`
regenerados com o binário atual): em 7 113 instantes com onset, `E` =
onsets + pausas ativas cobre as duas pautas em 3 391 (47,7%); com as notas
seguradas junto, em 6 930 (97,4%). Os 183 restantes (2,6%) são quase todos
de mão única soando sozinha (baixo do Satie/Rag/Prelude, melodia do
Nocturne sem o baixo, apojaturas) — nunca as duas pautas sem evento.
Medido por pauta de desenho cross-staff incluído. Conclusão: **sem nativo
novo** — `pitchpos.json`/schema inalterados, `version` 1.

**Referência** (`ghost_ref.py::ghosts`, passos 1 e 5): proposta por pauta
com o contexto dela; pauta única cai na regra antiga pelo mesmo código.
`--self-test`: **32 casos, 0 divergências** (26 antigos intactos —
pauta única, mesmo resultado bit a bit).

**Oráculo** (código inalterado, chamadas de um id só): `--targets 2400
--seed 42`: **2 400 alvos, 0 divergências**, 181 cópias, 72 s; `self`
idêntico a G04d (473 `plain_bad` de fonte, 0 `drawn_bad`, 0 `ghost_bad`).
Folga do acidente: mediana 0,4996 em 1 086 acidentes (G04d: 1 085 — um a
mais pelo binário atual, sem relação com G06, que não toca C++).

**Vetores** (`g04d-make-vectors.py`, `satie.vsb` + `CH`/`BASS` existentes):
6 casos novos, `resumo` à mão conferido conta a conta (o gerador parou uma
vez: eu tinha apontado o `target` do empate no ré4 quando o mais próximo é
o si3 — erro de conta meu, não da referência): grave no baixo sem 8vb
(45 → `loc` 1); **proximidade × cabimento** (55 → `loc` 7 no baixo, contra
`loc` −5 na sol pela regra antiga — o único vetor que distingue as duas
regras, confirmado contra o código anterior); empate de cabimento pela
proximidade (60 → sol com ♮); agudo extremo com 8va (100); grave extremo
com 8vb no baixo (21, que pela regra antiga ficava preso em 15mb na sol);
duas fantasmas uma em cada pauta (45 + 100). Fixtures `.vsb` regeneradas: cena/glifos/timemap/meta/
midi/pitchpos **byte-idênticos** (só o `generator` do manifest acompanha o
binário atual).

**Spec**: §10 passos 1 (+ "Contexto da pauta") e 5, Ex. 4 (lá2, conta
completa), histórico de revisões; aditivo, `version` 1.

**Cópia para o `zywny`** (item 5): `vetores.json` + os 9 `.vsb` em
`zywny/score_bridge/test/fixtures/fantasma/` (o `ghost_test.dart` itera os
casos sozinho: 33 passam, só o vetor "proximidade × cabimento" falha lá —
`loc` 7 esperado, −5 obtido — até a porta dos passos 1 e 5 em
`ghost.dart` + `setExpected`).
