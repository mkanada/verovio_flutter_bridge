# Nota para o `zywny` — nota fantasma (fase G, G03-G05)

Fechada em 2026-09-29 no lado deste repositório (formato, exportador,
referência e vetores). **Toda a execução Dart é no `zywny`**: parser,
fórmula, camada de pintura, ciclo de vida. As decisões estão em
[`docs/plano/G03-visao-geral-nota-fantasma.md`](plano/G03-visao-geral-nota-fantasma.md)
(D-FANT-*); o contrato normativo é a **§10** de
[`docs/formato/especificacao-v1.md`](formato/especificacao-v1.md).

## 1. O que mudou no `.vsb`

Tudo aditivo (`version` continua `1`; um leitor antigo ignora):

| O quê | Onde | Para quê |
| --- | --- | --- |
| `pitchpos.json` (novo) | §2.8, `manifest.files.pitchpos`, propriedade `pitchpos` no JSON único | contexto de notação de cada nota/pausa: `co` (clave), `sh` (8va/transposição), `key` (armadura), `acc` (acidentes em vigor), `pn`/`o`/`alt`/`loc` (só nota). **Indexado pelo id notado** — de um id expandido do timemap (`-rend<N>`) chega-se a ele pelo `VsbDocument.sceneIdOf` |
| `lines`, `ledger`, `ledgerCue`, `gs` no nó `staff` | §5.1 | geometria da pauta: y da linha de cima, `unit` (meio-espaço), nº de linhas; espessura/extensão das linhas suplementares; escala de um glifo normal. Valem também nas páginas alternativas (mesmo `BridgeDeviceContext`) |
| `staff` no nó de nota/acorde/pausa cross-staff | §5.1 | id do nó `staff` em que o elemento é desenhado (ausente = ancestral) |
| glifos reservados | §4 | `E0A4` (cabeça preta), `E260`/`E261`/`E262`, `E511`/`E512`, `E515`/`E516` sempre no `glyphs.json`, mesmo sem uso |
| `restsOn`/`restsOff` no timemap | §2.4 | quando cada pausa (`rest`, `mRest`, `multiRest`) está ativa — D-FANT-PAUSA-TEMPO. Só essas chaves são novas |
| `--no-vsb-pitchpos` (CLI/`Options`) | — | desliga só o `pitchpos.json` (padrão: gerar) |

**Regenerar as fixtures** (`.vsb` do corpus e de teste) com o binário novo. O
custo, medido nas 10 peças do corpus (antes de G04 → depois): `.vsb` +2,4% a
+11,2% (mediana ≈ +6,8%; a maior parte são ~11 KB fixos dos glifos
reservados e o `pitchpos.json`, 26 KB a 199 KB por peça grande); `scene.json`
+1% (campos de pauta); tempo de exportação inalterado (soma das 10 peças:
3,58 s → 3,58 s). `pitchpos.json` das peças com repetição é indexado por id
notado, então **não** cresce com o número de passagens.

## 2. Conferir no que já existe

- O parser do timemap e o `ScoreTimeline`/`ScorePlayer` devem aceitar
  `restsOn`/`restsOff` nos instantes. Os instantes só com pausa **já
  existiam**, vazios (o número de entradas e todos os campos antigos são
  idênticos — conferido peça a peça em G04c); só as chaves são novas.
  Rode os testes existentes contra as fixtures regeneradas antes de qualquer
  outra coisa.
- Nada mais muda no desenho: `scene.json` só ganha campos em nós (a
  paridade é a mesma; conferi que a cena, tirados os campos novos, é
  idêntica byte a byte à anterior nas 23 peças).

## 3. Modelo e parser (sugestão, no molde de `VsbMidi`)

- `VsbPitchPos`: `Map<String, PitchEvent>` por id notado. `PitchEvent`:
  `isNote`, `co`, `sh` (0), `key` (`Map<String,int>`, `{}`), `acc`
  (`Map<String,int>`, `{}`), `pn`/`o`/`alt`/`loc` (só nota). `null` em
  `VsbDocument.pitchPos` quando o arquivo não existe (peça sem nota nem
  pausa, ou `--no-vsb-pitchpos`) — nesse caso não há fantasma, e nada mais
  quebra.
- `StaffGeometry` no nó `staff`: `topY`, `unit`, `lines`, `ledger`
  (`thickness`, `extension`), `ledgerCue`, `glyphScale`.
- No nó de nota/acorde/pausa: `staffRef` (String?). A regra para achar a
  pauta de um elemento: `staffRef` se houver, senão o `staff` ancestral.

## 4. Cálculo: `ghostsFor`

```dart
List<GhostNote> ghostsFor({
  required List<String> expectedIds,   // ids NOTADOS do instante (notas e/ou pausas)
  required List<int> wrongKeys,        // teclas MIDI erradas
  PageRef? page,                       // onde procurar os nós; normal por padrão
});
```

É a **porta da §10** — os 8 passos, na ordem. A referência executável é
[`compare/scripts/ghost_ref.py`](../compare/scripts/ghost_ref.py) (uns 200
linhas); leia-a junto com a §10. `GhostNote`: pauta (id), `loc`, cabeça
(`x`, `y`, `sx`, `sy`), acidente (glifo + posição, se houver), linhas
suplementares (lista de `y`/`x1`/`x2`/espessura) e marcador de oitava (glifo
+ posição, se houver).

**Validação obrigatória:** [`docs/formato/fantasma/vetores.json`](formato/fantasma/vetores.json)
— 26 casos, cada um com o `.vsb` que ele usa na mesma pasta, os ids
esperados, as teclas, um `resumo` escrito à mão (pauta, `loc`, acidente,
nº de linhas, `m`) e os `fantasmas` completos com todos os números.
A porta Dart tem de bater o `resumo` **exatamente** e os números com
tolerância de **0,5 unidade de viewBox**. Os casos cobrem: cada regra da §10
(alvo por proximidade e empate para cima, grafia por armadura de ♯/♭/mista/
sem armadura acima e abaixo, bequadro necessário, acidente já em vigor por
armadura e por acidente escrito antes, colisão no mesmo `loc` e em segunda,
duas fantasmas em segunda, 8va, 8vb, 15mb presa em 4 linhas), pausa (e
pausa × nota em pautas diferentes), `mRest`, cross-staff, clave mudando no
meio do compasso, 8va/8vb escritas, instrumento transpositor, armadura não
padronizada e mudança de armadura.

`python3 compare/scripts/ghost_ref.py --self-test` roda a referência contra
os mesmos vetores.

**O que foi provado contra o Verovio** (G04d, `compare/scripts/ghost_oracle.py`):
2 400 alvos sorteados (corpus + `corpus/fantasma/`, teclas a ±1, ±2, ±3,
±12 semitons e além de 4 linhas suplementares), a nota esperada trocada
pela grafia prevista numa cópia MEI e renderizada pelo próprio Verovio:
**100%** de acerto em `loc` (medido contra as linhas da própria cópia),
glifo do acidente e número de linhas suplementares. O que o oráculo **não**
cobre — e que só os vetores escritos à mão cobrem —: deslocamento de
oitava (8va/15ma são invenção do plano), colisão, escolha de pauta num
acorde entre duas pautas, posição do marcador de oitava.

## 5. Pintura

Uma camada de overlay `CustomPaint` **por cima** das notas, no molde da
camada dinâmica (A01b): nunca um widget por forma. Glifos pelo `GlyphCache`
existente (`glyphId` = `"<fonte>:E0A4"` etc. — a fonte é a da peça, a mesma
que prefixa os demais), com a cor da fantasma definida pelo host; linhas
suplementares como segmentos com a espessura da pauta (`ledger`). A camada
repinta só quando o conjunto de teclas erradas muda.

## 6. Ciclo de vida (D-FANT-DURACAO)

Note-on de tecla errada → a fantasma aparece; note-off → fade curto e some.
Tempo de fade e tempo mínimo na tela são parâmetros do host, **não** do
formato (sugestão inicial: fade de 150 ms, mínimo de 250 ms, a ajustar no
uso). Uma fantasma por tecla; a mesma tecla pressionada de novo reaproveita
ou recria a fantasma conforme o host preferir.

## 7. Qual evento é o "esperado"

É decisão da avaliação do aluno no host (`N03`, `PerformanceTrack`), não do
formato: `ghostsFor` recebe os ids. Duas notas para a decisão:

- Durante uma **pausa**, passe o id da pausa (de `restsOn` do timemap,
  convertido por `sceneIdOf`) — a fantasma vai na coluna da pausa (D-FANT-PAUSA).
  Um instante com notas e pausas em pautas diferentes: passe todos, a
  fórmula escolhe o mais próximo em altura.
- Um evento esperado com notas tocadas juntas (acorde): passe **todas** as
  notas do acorde — a colisão (D-FANT-COLISAO) precisa conhecê-las.

## 8. Limitações aceitas da v1

- O acidente da fantasma pode colidir com acidentes reais da coluna (a
  fantasma não entra no empilhamento do Verovio).
- Acidente trazido por ligadura através da barra de compasso não conta como
  "em vigor" no compasso novo; mudança de armadura no meio do compasso não
  zera `acc`.
- Além de duas oitavas fora de 4 linhas suplementares (ex. lá 0 na clave
  de Sol), a fantasma fica presa em 4 linhas: a posição deixa de
  representar a altura.
- Percussão, tablatura e notação mensural: fora de escopo (sem `loc` de
  altura). Nota sem `@pname` na fonte não tem entrada em `pitchpos.json`.
- **Som e notação podem divergir na fonte** (`alt` é o que soa, `key`/`acc`
  o que está escrito): 473 de 9 039 notas do corpus (457 do Étude Op. 10
  nº 9, sem `key.sig` na `<scoreDef>`). O efeito é só na grafia da
  fantasma, nunca na altura; detalhes na §2.8.
- A posição do marcador de oitava é convenção visual sem oráculo; o host
  pode ajustá-la.
