# A05b — Virada automática por haste e evidências visuais

**Depende de:** A05a, A03b · **Decisão necessária:** não (mas os pontos
marcados "a confirmar" abaixo devem ser confirmados com o usuário)

## Objetivo

Fechar o ciclo: o player dirige a haste de A03b sozinho, na fronteira certa,
sem interromper o destaque — e o projeto ganha as imagens que provam os
requisitos para quem não vai rodar o código.

## Ler antes (só isto)

- [A03b](A03b-virada-animada.md), seção "Comportamento decidido com o
  usuário" — a haste, as etapas e a duração.
- `score_bridge/lib/src/score_player.dart` (A05a): `measures`, `position`,
  `speed`.
- `score_bridge/lib/src/score_view.dart` (A03b): `SweepCurtain`.
- A04a (`rectForId`).
- `../verovio_lottie/docs/plano/C05-host-simulado-timemap.md` **não** serve para
  a regra de fronteira: aquela era `peek` + `cover` por compasso; foi
  substituída pela regra abaixo.

## Contexto que você precisa (não vá procurar, está aqui)

Regra decidida com o usuário em 2026-09-21. Seja `P` uma página com mais de um
compasso, `M` o seu último compasso e `M+1` o primeiro compasso da página
seguinte. Com `D = min(1 s, duração de M / 4)`:

| Instante | Estado da haste (`edgeX`) |
| --- | --- |
| antes de `M.startMs` | sem haste (repouso) |
| `M.startMs` → `M.startMs + D` | **entrada**: `0` → `xInício(M)` |
| `M.startMs + D` → `(M+1).startMs` | **estacionada** em `xInício(M)` |
| `(M+1).startMs` → `(M+1).startMs + D` | **conclusão**: `xInício(M)` → fim |
| depois | repouso, com a página seguinte na frente |

`xInício(M)` é a borda esquerda da bbox do compasso `M` **no último sistema da
página**, convertida com A04a. `edgeX` é a borda **direita** da haste, então a
haste fica imediatamente à esquerda do compasso. `D` usa a duração do compasso
**M** nas duas etapas. Se `M` começar um sistema (com clave), a bbox do compasso
já inclui a clave; meça em uma peça do corpus onde isso ocorra e registre
nas notas onde a haste realmente cai.

**Página de um único compasso com várias notas:** não há "entrada até o início
do último compasso" — a haste **acompanha as notas**. Ela entra assim que a
página aparece e fica logo **antes** da nota atual (borda direita da haste na
borda esquerda da bbox da nota, incluindo acidente). Notas simultâneas (acorde,
vozes no mesmo instante do timemap): use a mais à esquerda. A cada nota
destacada, a haste **salta** para a seguinte com o mesmo `D`. **Antes** da
primeira nota a haste já está posicionada antes dela. A conclusão é a mesma da
regra geral: começa quando a primeira nota do compasso seguinte é destacada.

**Caso extremo — página com um único compasso e uma única nota:** a haste entra
assim que a página aparece, ao lado da nota, e a conclusão começa **0,5 s
depois** do destaque dessa nota (não espera o compasso seguinte). O 0,5 s vale
**só** neste caso.

**Sem virada:** na última página da peça não há haste.

**A posição é derivada, não guardada.** `SweepCurtain` é uma função pura de
`(position, measures, layout)`. Por isso `seek`, `pause` e `speed` funcionam sem
código extra: no `seek` para dentro do último compasso, a haste já aparece
onde a reprodução normal a colocaria; se o alvo cair na página seguinte, ela já
aparece em repouso (sem animação); um `seek` que sai de qualquer virada em curso
recalcula do zero. O relógio da haste é o **mesmo** do player (ms musicais):
com `pause` ela congela, com `speed = 2` ela anda o dobro.

Pontos **a confirmar com o usuário** (não estavam decididos):

- No compasso único, a duração do salto entre notas é `min(1 s, compasso / 4)`
  como no resto, mas se a próxima nota vier antes disso o salto termina no
  instante dela (a haste nunca fica atrasada em relação à nota). Confirme.
- Se a primeira nota de `M` for mais curta que `D` (a entrada ainda não
  terminou quando a segunda nota chega), nada muda: a entrada continua até `D`.

O **ponto de prova do projeto**: no Lottie, a virada cancelava o fade (dois
engines não compositáveis). Aqui, o destaque tem que atravessar a virada sem
soluço. A03b já provou isso com chamada manual; aqui a prova é com o player
real dirigindo.

## O que fazer

1. Função pura `SweepCurtain? curtainAt(Duration position)` (no `ScorePlayer`
   ou em arquivo próprio, sem dependência de widget), implementando a tabela
   acima e os dois casos especiais. É a peça mais testável do passo.

2. Ligar o player a `ScoreView.curtain` (A03b): a cada tick, atualizar o
   `ValueListenable<SweepCurtain?>`. Quando a conclusão terminar, a `ScoreView`
   troca a página atual (A03b, item 2) e o player passa a considerar a nova
   página como corrente.

3. `maxSweepDuration` (padrão 1 s) vem de `ScoreView`; o player o lê para o
   `D`. Não duplique a constante.

4. Desligar a virada quando o modo for `continuousScroll` — ali a rolagem
   acompanha a posição (use `scrollToId` da nota corrente, com alinhamento
   configurável).

5. Gerar as **evidências visuais** em `docs/exemplos/`:
   - `docs/exemplos/destaque-notas/<peça>/` — 4 a 5 frames com notas em fases
     diferentes;
   - `docs/exemplos/virada-pagina/<peça>/` — a sequência da virada por haste: no
     mínimo (1) repouso, (2) meio da entrada, (3) haste estacionada com o último
     compasso tocando, (4) meio da conclusão, (5) repouso da página seguinte;
   - em cada diretório, o **roteiro exato** (instantes, comando) que gerou as
     imagens, de forma reproduzível.

## Fora de escopo

- Áudio e sincronização real.
- Otimização de desempenho e perfil em dispositivo (ficam no `zywny`).
- Configuração pelo usuário final do teto de 1 s (só o parâmetro existe).

## Critérios de aceite

1. Uma peça de 3+ páginas toca do início ao fim com viradas automáticas, sem
   exceção, terminando com a última página em repouso e **sem haste**.
2. **Nenhum resíduo**: um frame capturado no fim da execução é
   **pixel-idêntico** ao render estático da página final (0 pixels).
3. **Tempos da regra**, com relógio simulado, comparados com os `tstamp` do
   timemap calculados no teste: a entrada começa em `M.startMs`; a haste está
   estacionada em `xInício(M)` de `M.startMs + D` até `(M+1).startMs`; a
   conclusão começa em `(M+1).startMs` e termina em `(M+1).startMs + D`. `D` é
   `min(1 s, duração de M / 4)` — teste com um compasso curto (`D` < 1 s) e um
   longo (`D` = 1 s).
4. **Compasso único**: numa página de um compasso com várias notas (fabrique o
   documento se o corpus não tiver), a haste está antes da primeira nota assim
   que a página aparece, salta para antes de cada nota destacada e conclui na
   primeira nota do compasso seguinte. Com uma nota só, a conclusão começa 0,5 s
   após o destaque.
5. **`seek`**: para dentro do último compasso, para a página seguinte e para
   antes da virada — o estado da haste em cada caso é o que a reprodução normal
   produziria naquele instante, sem animação residual.
6. **Destaque atravessa a virada** dirigido pelo player: notas acesas antes e
   durante a virada continuam animando durante e depois dela (frames anexados).
7. `docs/exemplos/destaque-notas/<peça>/` e
   `docs/exemplos/virada-pagina/<peça>/` existem, com imagens e roteiro
   reproduzível.
8. Modo contínuo: a rolagem acompanha a nota corrente sem saltos bruscos
   (frames ou vídeo curto anexado), e nenhuma haste aparece.
9. `flutter analyze` limpo, `flutter test` verde.

## Notas de execução

Concluído em 2026-09-21 (`score_timeline.dart` `curtainAt`, `score_player.dart`,
`test/score_timeline_test.dart`, `test/score_player_test.dart`,
`tool/generate_examples.dart`).

- **`ScoreTimeline.curtainAt(ms, maxSweep:, barWidth:)`** é a função pura; o
  player a chama a cada avanço/`seek` e publica em `player.curtain`
  (`ValueListenable<SweepCurtain?>` → `ScoreView.curtain`). Sem haste, o
  player leva a vista à página de repouso (`goToPage`) só se ela difere.
  `maxSweepDuration` e `barWidth` são lidos da vista (`ScoreViewController`)
  quando o player não recebe os seus — a constante existe uma vez
  (`kDefaultMaxSweepDuration`).
- **Onde a haste realmente cai** (medido): `xInício(M)` é a borda esquerda do
  nó `measure` — no Nocturne, p. 1, `M = m1vrmzxb` (3 103 ms, `D = 775,75 ms`),
  `xInício = 12 082,5` unidades. Quando `M` começa um sistema a bbox inclui a
  clave; a haste então fica à esquerda dela (visível no frame 3 de
  `docs/exemplos/virada-pagina/Nocturne/`, em que ela cai na coluna do
  compasso da última linha). O corpus **não tem** compasso ≥ 4 s antes de uma
  virada com mais de um compasso na página; o caso `D = 1 s` é coberto no
  documento sintético (`test/support/fake_doc.dart`).
- **Critério 3 (tempos)**: entrada em `M.start`, estacionada de `M.start + D`
  a `(M+1).start`, conclusão até `(M+1).start + D`, repouso depois — corpus
  (D curto) e sintético (D = 1 s).
- **Critério 4 (compasso único)**, decisões tomadas onde o plano deixou
  aberto (**a confirmar com o usuário**): (a) a haste está no x da nota
  **seguinte** a cada nota destacada: o salto para a nota k+1 **começa** no
  instante da nota k e dura `min(D, t(k+1) − t(k))` — assim chega **no mais
  tardar** quando a nota acende ("nunca atrasada"); antes da primeira nota já
  está posicionada nela; (b) a página só "aparece" quando termina a conclusão
  da virada anterior (`first.start + D(anterior)`): a entrada dela começa aí;
  (c) com **uma** nota a conclusão começa em `max(destaque + 0,5 s, aparição +
  D)`, limitada ao início do compasso seguinte — se a página aparece depois
  de 0,5 s do destaque, a haste termina de entrar antes de concluir, em vez
  de surgir no meio da conclusão; (d) acorde = uma nota (mais à esquerda).
- **Critério 5 (`seek`)**: dentro do último compasso a haste é a que a
  reprodução normal produziria (`curtainAt` no mesmo instante); na página
  seguinte, repouso sem haste; antes da virada, repouso da página 1.
- **Critérios 1, 2 e 6**: Scarlatti (3+ páginas) toca com viradas a 20×, sem
  exceção; a página final é **0 pixels** contra o render estático; com o
  player real, `highlightedCount > 0` em todos os quadros da virada
  (Nocturne, `release: 2 s`).
- **Critério 8 (contínuo)**: sem haste (`curtain` nunca não-nulo);
  `scrollToId(compasso, alignment: 0,3, 300 ms)`; em 60 s de execução a 1×,
  **maior deslocamento por quadro de 50 ms = 231 px** (página de 2970 px).
- **Critério 7**: `docs/exemplos/destaque-notas/Gymnopedie/` (5 frames com
  notas em fases diferentes) e `docs/exemplos/virada-pagina/Nocturne/`
  (5 frames da virada), cada um com `roteiro.md`; regenerar com
  `cd score_bridge && flutter test tool/generate_examples.dart`.
- Suíte final: `flutter analyze` limpo, `flutter test` 207 verdes.
