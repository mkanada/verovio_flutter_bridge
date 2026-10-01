# G07 — Visão geral: nota escondida e pausa substituta (trilha do decorar)

**Não é um passo executável.** É o documento de referência de G08a-G09:
leia este arquivo inteiro antes de executar qualquer um deles. Cada passo
repete o que precisa, mas as regras abaixo são o contrato comum.

## O problema

O `zywny` vai ganhar uma **trilha do decorar** (fase L do plano de lá,
`docs/plano/L00-trilha-do-decorar.md`): a partitura aparece inteira e, etapa
após etapa, mais notas **somem**; o aluno toca o que lembra. No lugar de
cada nota que sumiu entra uma **pausa de outra cor**, com a figura da nota:
o ritmo continua escrito, a altura é o que se decora.

Para o host fazer isso sem adivinhar nada, o `.vsb` precisa responder a três
perguntas:

1. **O que apagar** para a nota sumir de verdade — cabeça, haste e acidente
   são fáceis (filhos do nó `note`); a barra de ligação e as linhas
   suplementares, não.
2. **Que pausa desenhar** — a cena não traz a figura (duração notada) da
   nota, e o dicionário de glifos só traz as pausas que a peça usa.
3. **Onde desenhá-la** — a posição vertical de uma pausa na pauta é regra do
   Verovio, não do host.

## Decisões do usuário (2026-10-01, entrevista no `zywny`) — não reabrir

| Id | Decisão |
| --- | --- |
| **D-SUM-UNIDADE** | A unidade que some é a **coluna**: todas as notas de **uma pauta** que começam no mesmo instante (nos hinos, as duas vozes da mão). Nunca uma voz só. Quem escolhe as colunas é o host. |
| **D-SUM-PAUSA** | No lugar da coluna entra **uma** pausa, numa cor do host, com a figura da nota **mais curta** da coluna, na posição normal de pausa da pauta. |
| **D-SUM-FICA** | Ficam na tela: pauta, clave, armadura, fórmula de compasso, barras de compasso, pausas de verdade, a letra (`verse`), ligaduras de expressão e de prolongamento, dedilhado e as notas que não sumiram. |
| **D-SUM-BARRA** | A barra de ligação (`beam`) some quando **todas** as notas dela estão escondidas. |
| **D-SUM-SUPLEMENTAR** | As linhas suplementares de uma coluna escondida somem; as de uma coluna visível, não. |
| **D-SUM-ERRO** | Errar uma coluna escondida a **revela** (a pausa sai, as notas voltam). É comportamento do host; o formato só precisa permitir esconder e mostrar sem recompilar a página. |

## Decisões a fechar com o usuário antes de codar

| Id | Pergunta | Bloqueia | Recomendação |
| --- | --- | --- | --- |
| **D-SUM-FIGURA** | De onde o host tira a figura da nota? | G08a, G08b | **(a) `pitchpos.json` ganha `dur` e `dots`** por nota (e por pausa, de graça): é o arquivo de "como está escrito", indexado pelo id notado, e o Verovio tem o valor exato (`DurationInterface::GetActualDur`, `GetDots`). Rejeitar (b) deduzir do timemap (`qstamp` do `off` menos o do `on`): erra em quiáltera (52 dos 600 hinos do `zywny`), em nota ligada e em fermata/andamento, e obriga o host a uma tabela de arredondamento. |
| **D-SUM-NATIVO** | A regra das linhas suplementares precisa de dado novo na cena? | G08c | **"Sem nativo novo primeiro"** (a mesma linha de G06): a regra é geométrica (§ Regras, 3) e G08c a varre no corpus. Só se a varredura achar traço ambíguo, o exportador passa a gravar no traço os ids das notas que o geraram (`LedgerLine::Dash::m_events` já existe no Verovio). |

## Fatos medidos (2026-10-01)

Cena de `Chopin_Etude_Op10_No9.vsb` (fixture do `zywny`) e fonte do fork:

| Fato | Onde / quanto |
| --- | --- |
| O nó `note` (com `id`) contém `notehead`, `stem`, `accid`, `artic`, `dots` | trocar a cor do id da nota alcança tudo isso por herança (§6 da spec) |
| A letra (`verse`) é filha da nota | o host já a deixa fora da troca de cor (`kOverrideExemptClasses`, no `score_bridge`) |
| A barra de ligação é uma forma `p` solta, filha direta do grupo `beam` (que tem `id`), irmã das notas | 340 de 353 notas do Étude estão dentro de `beam` |
| Linhas suplementares: grupos `ledgerLines above`/`below` (e as variantes `cue`), filhos de `staff`, **sem `id`** | `View::DrawLedgerLines`, `view_page.cpp` L1420 |
| Cada **traço** é uma forma `p` própria, de um segmento | 396 folhas, todas com 1 caminho de 2 pontos |
| O Verovio só funde traços que se sobrepõem em mais de 1,5 extensão: "os do mesmo acorde fundem, os de notas vizinhas não" | `LedgerLine::AddDash`, `staff.cpp` L381-L409 |
| Cada traço guarda as notas que o geraram | `LedgerLine::Dash::m_events`, `staff.h` L50 |
| Pausa de verdade: `g class="rest"` com um uso de glifo | glifo por figura em `Rest::GetRestGlyph`, `rest.cpp` L260-L320 |
| Posição padrão da pausa: `loc` da linha do meio; **+2 para a semibreve** em pauta de mais de uma linha; depois ajuste por camada | `calcalignmentpitchposfunctor.cpp` ~L186 e L311 (`GetOptimalLayerLocation`) |
| Glifos reservados hoje: `E0A4`, `E260`-`E262`, `E511`/`E512`/`E515`/`E516` | `BridgeDeviceContext::AddReservedGlyphs`, `bridgedevicecontext.cpp` L1254; spec §4 |
| `pitchpos.json` não traz figura nem pontos | spec §2.8 |
| O corpus não tem nenhuma peça com duas vozes por pauta e letra, que é o caso de **598 dos 600** hinos do `zywny` | `corpus/` |

## Regras (contrato comum a G08a-G09)

Tudo o que é musical vem do Verovio; o host só faz a conta. A especificação
(G08a) é normativa; aqui fica o resumo que orienta os passos.

1. **Esconder a nota.** O host troca a cor do nó `note` por transparente.
   Cabeça, haste, colchete (`flag`), acidente, articulação e pontos vão
   junto. `verse` fica. A continuação de uma nota ligada é outra `note`, e o
   host a esconde pelo id (`midi.json` → `tied`).
2. **Barra de ligação.** As formas filhas diretas de um `beam` somem quando
   toda `note` descendente dele está escondida. Barras aninhadas: a regra
   vale para cada `beam` com as suas descendentes.
3. **Linhas suplementares.** Um traço (forma `p` dentro de `ledgerLines …`)
   **pertence** às notas da mesma pauta de desenho cuja cabeça (`bbox` do
   `notehead`) ele cobre em x **e** cujo `loc` (`pitchpos.json`) alcança a
   linha dele — acima: `loc ≥ 2·(n − 1) + 2·k`; abaixo: `loc ≤ −2·k`, sendo
   `k` a ordem da linha a partir da pauta. O traço some quando todas as
   notas a que pertence estão escondidas. Um traço sem dona (não deve
   existir) fica visível.
4. **Figura.** `dur` e `dots` da nota mais curta da coluna (D-SUM-FIGURA).
   Quiáltera não muda a figura: usa-se a escrita.
5. **Glifo.** `E4E3` (semibreve), `E4E4`, `E4E5`, `E4E6`, `E4E7`, `E4E8`
   (fusa), `E4E9` (semifusa); figuras fora dessa faixa não têm pausa
   substituta (a coluna some sem pausa). Ponto de aumento: `E1E7`.
6. **Posição.** x = menor `x` de cabeça da coluna. `loc` = linha do meio
   (`n − 1`), **+2** para a semibreve quando `n > 1`; sem o ajuste por
   camada do Verovio (a pausa substituta é uma só por pauta).
   `y = topY + (2·(n − 1) − loc) · unit` (o `y` da §10). Escala: `gs` do nó
   `staff`. Pontos: à direita do glifo, na regra de `View::DrawDots` — G08c
   fixa a conta.
7. **Uma pausa por (pauta de desenho, instante).** Coluna cross-staff: a
   pauta é a de desenho (`staff` do nó, §5.1).

## O que muda em cada lado

| Onde | O quê | Passo |
| --- | --- | --- |
| Especificação | glifos reservados novos (§4); `dur`/`dots` em `pitchpos.json` (§2.8, se D-SUM-FIGURA = a); **§11 Nota escondida e pausa substituta** (normativo) | G08a |
| C++ | pausas e ponto em `AddReservedGlyphs`; `dur`/`dots` em `bridgepitchpos.cpp` | G08b |
| Prova | referência Python das regras 1-7, varredura do corpus (traços × donas, barras), oráculo Verovio para a pausa, vetores de teste para o `zywny`; hino no corpus | G08c |
| `zywny` | esconder/revelar no `score_bridge`, camada da pausa, e a trilha em si | G09 (nota para o host; execução em L02/L03 de lá) |

O `score_bridge` mora no `zywny` (commit `276bdf6`): o lado Dart inteiro é
executado lá. Este repositório entrega formato, exportador, referência e
vetores de teste.

## Invariantes

- **Nada muda no desenho.** `scene.json` não ganha campo nenhum (salvo o
  plano B de D-SUM-NATIVO); `glyphs.json` ganha entradas não usadas por
  nenhuma instância. Paridade das páginas normais e alternativas
  byte-idêntica no PNG.
- **Aditivo** (§9 da spec): `version` continua `1`; leitor antigo ignora os
  campos e os glifos novos. `.vsb` antigo, sem os glifos: o host esconde a
  coluna sem desenhar pausa.
- **Ids**: `pitchpos.json` continua indexado pelo id notado; o host chega
  lá por `VsbDocument.sceneIdOf`.
- **Páginas alternativas**: as regras 1-3 e 6 usam só o que está na página
  (nós, `bbox`, geometria da pauta), então valem igual nas duas.
- **Critério de correção é visual** (oráculo em G08c), nunca comparação
  estrutural de JSON.

## Limitações aceitas na v1

- A pausa substituta pode ficar apertada contra uma nota visível vizinha: o
  espaçamento da página foi calculado para a nota, não para a pausa.
- Ligadura de prolongamento ou de expressão que começa ou termina numa nota
  escondida continua desenhada.
- Dedilhado (`fing`, filho do compasso) continua desenhado.
- Pauta que não tem 5 linhas, tablatura, percussão, notação mensural: sem
  pausa substituta.
- Apojaturas e ornamentos não somem (o host não os cobra).
