# G03 — Visão geral: nota fantasma (feedback de tecla errada na pauta)

**Não é um passo executável.** É o documento de referência de G04a-G05:
leia este arquivo inteiro antes de executar qualquer um deles. Cada passo
repete o que precisa, mas as regras abaixo são o contrato comum.

## O problema

O aluno toca num piano/teclado MIDI e o `zywny` compara cada tecla com a
nota esperada (`midi.json`, G01/G02). Quando a tecla está errada, a solução
comum é mostrar um teclado virtual com a tecla destacada — o usuário **não**
quer isso, porque tira o aluno da notação.

O que o usuário quer: uma **cabeça de nota fantasma**, de cor diferente,
desenhada na própria pauta:

- **vertical** = onde a nota **tocada** ficaria escrita (linha/espaço,
  acidente, linhas suplementares), na clave e contexto vigentes;
- **horizontal** = a coluna da nota que o aluno **deveria** tocar.

O aluno vê a nota certa (escrita) e a errada (fantasma) na mesma coluna e lê
o intervalo pela pauta. O objetivo é pedagógico: ligar tecla ↔ posição na
pauta sem sair da notação.

## Decisões do usuário (2026-09-29) — não reabrir

| Id | Decisão |
| --- | --- |
| **D-FANT-CALCULO** | O `.vsb` carrega as **regras** (contexto de notação por evento: clave vigente, 8va/transposição, armadura, acidentes já em vigor no compasso) e a **geometria explícita da pauta**; o host aplica uma fórmula curta, normativa na especificação. Rejeitadas: (A) o host deduzir tudo da cena (clave pelo desenho do glifo, 8va e grafia adivinhados — erra em mudança de clave, 8va, cross-staff e enarmonia) e (B) o `.vsb` trazer a posição pronta das 88 teclas por nota (~3,4 MB estimados na Maple Leaf Rag, o dobro do `scene.json`, com grafia e limites congelados no arquivo). |
| **D-FANT-PAUTA** | A fantasma aparece na **pauta da nota esperada** (a pauta onde ela está desenhada, inclusive cross-staff). |
| **D-FANT-ACORDE** | **Uma fantasma por tecla errada**, na coluna do evento esperado; num evento com notas em mais de uma pauta, cada fantasma vai para a pauta da nota esperada **mais próxima em altura** (§ Regras, 1). |
| **D-FANT-GRAFIA** | Tecla preta segue a **armadura**: armadura com sustenidos → ♯; com bemóis → ♭. **Sem armadura** (Dó maior/Lá menor): ♯ se a tecla tocada está **acima** da nota esperada, ♭ se **abaixo**. Tecla branca é sempre a letra natural (nunca Mi♯/Dó♭). |
| **D-FANT-ACIDENTE** | Acidente **só quando necessário**, como na notação real: considera a armadura e os acidentes já escritos antes, no mesmo compasso e pauta, inclusive ♮. |
| **D-FANT-COLISAO** | Se a fantasma cai na mesma linha/espaço de uma cabeça real da coluna, ou a uma segunda dela, **desloca para o lado** (como a segunda num acorde); entre fantasmas vale a mesma regra. |
| **D-FANT-ALCANCE** | Até **4 linhas suplementares** desenha direto; acima disso, desloca por oitavas até caber e marca **8va/8vb** (uma oitava) ou **15ma/15mb** (duas). |
| **D-FANT-CABECA** | Cabeça **sempre preta** (`noteheadBlack`, U+E0A4), no tamanho da pauta/nota esperada (cue/grace herdam a escala). |
| **D-FANT-DURACAO** | Visível **enquanto a tecla está pressionada** (aparece no note-on, some no note-off, com fade curto). Parâmetro do host, não do formato. |
| **D-FANT-PAUSA** | Tecla tocada durante uma **pausa**: a fantasma vai na **coluna da pausa**, na pauta dela. Havendo pausas em mais de uma pauta, vale a regra de proximidade (§ Regras, 1) usando a linha do meio da pauta como altura de referência. |
| **D-FANT-PAUSA-TEMPO** | O host precisa saber **quando** cada pausa está ativa, e o timemap do `.vsb` hoje não tem pausas (`RenderToTimemap("{\"includeMeasures\": true}")`, sem `includeRests`, `toolkit.cpp` ~L2417). Decisão: **ligar `includeRests` no timemap embutido** — o Verovio já gera `restsOn`/`restsOff` (`Timemap::ToJson`, `timemap.cpp` L69). Consequência aceita: o `timemap.json` ganha as chaves `restsOn`/`restsOff`. Instantes só com pausa **já existem hoje**, vazios (o `GenerateTimemapFunctor` cria a entrada da pausa com ou sem `includeRests`, `midifunctor.cpp` L1338-L1413; a Maple Leaf Rag já tem 1 entrada sem `on`/`off`/`measureOn` em 1 013), então o esperado é que só as chaves sejam novas — G04c confere, e o `ScoreTimeline`/`ScorePlayer` do `zywny` é conferido em G05. Rejeitada: gravar os tempos das pausas no `pitchpos.json` (dois relógios em dois arquivos). |

## Regras (contrato comum a G04a-G05)

Tudo o que é musical vem do Verovio; o host só faz a conta. A especificação
(G04a) é normativa; aqui fica o resumo que orienta os passos.

**Unidade vertical.** O Verovio já posiciona toda nota por um inteiro `loc`
(linha/espaço a partir da linha de baixo, 1 por meio-espaço):
`loc = (oct − 4) × 7 + (pname − 1) + clefLocOffset`
(`PitchInterface::CalcLoc`, `pitchinterface.cpp` L188), com o
`clefLocOffset` da clave vigente para aquela nota (`Layer::GetClefLocOffset`,
cross-staff via `GetCrossStaffClefLocOffset`, L161-165). O y na cena é
`y = topoDaPauta + (2 × (linhas − 1) − loc) × unit`
(`Staff::CalcPitchPosYRel`, `staff.cpp` L287, com o eixo y da cena para
baixo). Conferido no Satie (`erik-satie.vsb`, 1ª pauta): linhas em
y = 808…1528, `unit` = 90; a cabeça `orw55dt` em y = 1798 dá `loc` = −3. ✔

**Da tecla à fantasma** (para um evento esperado `E` e uma tecla `k`, MIDI):

1. **Pauta e evento-alvo.** Entre as notas/pausas de `E` (e, num acorde que
   ocupa duas pautas, entre as notas de cada pauta), escolhe-se a de altura
   de referência mais próxima de `k` (nota: sua altura sonora; pausa: a
   altura sonora da linha do meio da sua pauta). Empate → a de cima.
2. **Altura escrita.** `w = k − shift`, com `shift` = semitons entre som e
   escrita no ponto de `E` (transposição de instrumento + 8va/8vb vigentes,
   o mesmo que `GetMIDIPitch` soma).
3. **Grafia** (D-FANT-GRAFIA): tecla branca → letra natural; tecla preta →
   ♯ ou ♭ pela armadura, ou pelo sentido do erro quando não há armadura
   (sentido medido contra a altura **escrita** da nota esperada; numa pausa,
   contra a linha do meio). Resultado: `pname`, `oct`, alteração ∈ {−1, 0, +1}.
4. **`loc`** pela fórmula acima, com o `clefLocOffset` do evento.
5. **Alcance** (D-FANT-ALCANCE): linhas suplementares acima =
   `⌊(loc − 2×(linhas−1)) / 2⌋` quando positivo; abaixo = `⌊−loc / 2⌋`
   quando positivo. Enquanto passar de 4, `loc ∓= 7` e sobe o marcador
   (nenhum → 8va/8vb → 15ma/15mb).
6. **Acidente** (D-FANT-ACIDENTE): a alteração em vigor para aquele
   `pname`+`oct` é a do último acidente escrito antes de `E` no compasso e
   pauta, senão a da armadura. Se a da grafia for diferente, desenha-se
   ♯/♭/♮ (U+E262/U+E260/U+E261).
7. **x** = x da cabeça (ou do glifo da pausa) do evento-alvo; se a fantasma
   estiver a ≤ 1 `loc` de uma cabeça real da coluna ou de outra fantasma,
   desloca uma largura de cabeça para a direita (D-FANT-COLISAO).
8. **Linhas suplementares** com a espessura e a extensão do Verovio para
   aquela pauta.

## O que muda em cada lado

| Onde | O quê | Passo |
| --- | --- | --- |
| Especificação | `pitchpos.json` novo (§2.8), campos novos no nó `staff` da cena (§5.1), glifos reservados (§4), fórmula normativa | G04a |
| C++ (cena) | nó `staff` ganha a geometria das linhas e das linhas suplementares; nó de nota/acorde cross-staff aponta a pauta onde é desenhado; dicionário de glifos sempre inclui os glifos da fantasma | G04b |
| C++ (semântica) | `pitchpos.json`: contexto por nota/acorde/pausa (clave, `shift`, armadura, acidentes em vigor, altura escrita); timemap embutido com `includeRests` (D-FANT-PAUSA-TEMPO) | G04c |
| Prova | implementação de referência da fórmula (Python, `compare/scripts/`) + **oráculo Verovio** (trocar a nota pela tecla errada numa cópia da partitura e conferir que o Verovio desenha a cabeça exatamente onde a fórmula diz) + vetores de teste em JSON para o `zywny` | G04d |
| `zywny` | modelo/parser de `pitchpos.json`, fórmula, camada de overlay que desenha as fantasmas | G05 (nota para o host; execução fora deste repo) |

O `score_bridge` mudou para o `zywny` (commit `276bdf6`): o lado Dart
inteiro — parser, fórmula, pintura — é executado lá. Este repositório entrega
formato, exportador, referência e vetores de teste.

## Invariantes

- **Timemap: só as chaves `restsOn`/`restsOff` são novas.** Número de
  entradas, `on`/`off`/`tstamp`/`qstamp`/`measureOn`/`tempo` continuam
  iguais (conferido em G04c).
- **Nada muda no desenho.** `scene.json` ganha só campos aditivos em nós
  (a paridade das 34 páginas + alternativas tem de continuar
  byte-idêntica no PNG); `glyphs.json` ganha entradas não usadas por
  nenhuma instância.
- **Aditivo** (§9 da spec): `version` continua `1`; leitor antigo ignora
  o arquivo e os campos novos.
- **Ids**: `pitchpos.json` é indexado pelo id **notado** (o contexto de
  notação é o mesmo em todas as passagens de uma repetição); o host chega
  lá pelo `VsbDocument.sceneIdOf` (regra do sufixo, §2.4). Os tempos das
  pausas vêm do timemap (`restsOn`/`restsOff`, ids expandidos).
- **Páginas alternativas**: a geometria da pauta está no nó `staff` de
  cada página (normal ou alternativa, o mesmo `BridgeDeviceContext`), então
  a fantasma funciona igual nas duas sem dado extra.
- **Critério de correção é visual** (oráculo Verovio em G04d), nunca
  comparação estrutural de JSON.

## Limitações aceitas na v1

- O acidente da fantasma pode colidir com acidentes reais da coluna (o
  Verovio empilha acidentes em colunas; a fantasma não entra nesse
  empilhamento).
- Acidente trazido por ligadura através da barra de compasso não conta como
  "em vigor" no compasso novo (a regra do passo 6 olha só o compasso atual).
- Percussão/tablatura/notação mensural: fora de escopo (sem `loc` de altura).
