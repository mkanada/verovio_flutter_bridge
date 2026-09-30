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
