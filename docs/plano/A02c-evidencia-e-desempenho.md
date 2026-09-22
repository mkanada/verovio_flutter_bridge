# A02c — Evidência visual e orçamento de frame

**Depende de:** A02b · **Decisão necessária:** não

## Objetivo

Provar, com imagem, o requisito que o projeto anterior não conseguiu
entregar: várias notas acesas ao mesmo tempo, **cada uma em uma fase
diferente do fade**, convivendo — e medir se isso cabe no orçamento de frame.

## Ler antes (só isto)

- [`docs/licoes-do-verovio-lottie.md`](../licoes-do-verovio-lottie.md), item 1
  ("vozes com onsets diferentes se cancelavam").
- Notas de execução de A01c (tempos medidos) e A02b.

## Contexto que você precisa (não vá procurar, está aqui)

- O caso que **era impossível** no Lottie e precisa aparecer na imagem: um
  acorde de 4 notas aceso num instante, mais uma voz separada acesa num
  instante **diferente**, tudo visível ao mesmo tempo em fases distintas do
  fade. No mecanismo antigo (playhead único, agrupamento por instante), a
  segunda chamada cancelava a primeira.
- Peça boa para o caso: qualquer uma com duas vozes claras — Clair de Lune ou
  Chopin Nocturne. A Gymnopédie (melodia + acompanhamento em acordes) é a mais
  legível para a imagem.
- Orçamento: **abaixo de 8 ms** por frame (notificação + repaint) com 64 notas
  animando, na máquina de desenvolvimento. 60 fps dá 16,6 ms por frame, e
  metade disso é a margem para o resto do app.
- Captura de frames determinística: dirija o tempo pelo motor (tempo
  simulado), renderize e salve — não capture "ao vivo" tentando acertar o
  instante.
- Se estourar o orçamento, os suspeitos, em ordem: alocação por nota por
  frame (A02a), notificação por nota em vez de por tick (A02b), e `Picture`
  estático sendo recompilado (A01b).

## O que fazer

1. Roteiro determinístico: lista de `(instante, ação)` — acorde de 4 notas em
   t=0, voz separada em t=180 ms, com `attack`/`release` diferentes.
2. Capturar 5 frames em instantes escolhidos e salvá-los em
   `compare/out/a02/` (e uma cópia dos melhores em `docs/exemplos/`, se o
   usuário quiser mostrar).
3. Medir, com 64 notas ativas: tempo de `notifyListeners` + repaint (mediana
   de 100 frames). Registrar máquina, backend e números.
4. Conferir que `pictureBuilds` não se mexe durante toda a sequência.

## Fora de escopo

- Medição em dispositivo (fica no `zywny`) — aqui é a máquina de desenvolvimento.
- Playback automático pelo timemap (A05).

## Critérios de aceite

1. Cinco frames capturados mostram, **na mesma imagem**, notas em fases
   diferentes do fade (cores distintas convivendo). As imagens estão anexadas
   nas notas de execução, com o roteiro (instantes exatos) que as gerou.
2. Tempo médio de frame com 64 notas animando **abaixo de 8 ms**; número,
   máquina e backend registrados. Se passar, a causa foi investigada e está
   registrada.
3. Nenhum `ui.Picture` estático recompilado durante as animações.
4. O teste widget-vs-harness de R05c continua em 0 pixels.
5. `flutter analyze` limpo, `flutter test` verde.

## Notas de execução

Executado em 2026-09-21 com `flutter test tool/a02c_evidence.dart`.
Máquina: Intel i5-4440 @ 3,1 GHz, 4 núcleos, Linux; `flutter_tester` (Skia,
rasterização por software). **Não é** medição em dispositivo (fica no `zywny`).

**Roteiro** (tempo simulado pelo relógio do teste; Gymnopédie, página 1)

| Instante | Ação |
| --- | --- |
| t = 0 | `highlightAll` no **acorde de 4 notas** com mais notas da página (`w15g98jj`, `ytdvz43`, `z1t9tkxl`, `afdnkq9`), `#D32F2F`, attack 100, hold 150, release 700, `easeOut` |
| t = 180 ms | `highlightAll` na **voz separada** (2 notas, `yw90mxt`, `t1mebzmw`), `#1565C0`, attack 40, hold 100, release 500, `easeInOut` |

Frames capturados em t = 60, 200, 320, 480 e 750 ms (página inteira em
`compare/out/a02/`, git-ignorado; **recortes em `docs/exemplos/a02/`**):

| t | Acorde | Voz |
| --- | --- | --- |
| 60 | `#a62525` (meio do attack) | repouso |
| 200 | `#d32f2f` (hold) | `#0b3360` (meio do attack) |
| 320 | `#b12727` (release começando) | `#1565c0` (hold) |
| 480 | `#6d1818` (release) | `#104f97` (release começando) |
| 750 | `#190606` (quase de volta) | `#010408` (quase de volta) |

Em t = 200, 320 e 480 as duas famílias convivem em **fases diferentes na mesma
imagem** — o caso que o playhead único do Lottie não permitia (a segunda
chamada cancelava a primeira). O script verifica isso por asserção (≥ 2 cores
distintas por frame) e ainda o confere a olho nos recortes.

**Orçamento** — 64 notas animando (`attack` 3 s, `hold` 1 s, `release` 3 s),
100 `pump` de 16 ms (tick + notificação + build + gravação do paint):
**mediana 1,83 ms, média 2,02 ms, máximo 5,76 ms**, contra o orçamento de
8 ms. Só a rasterização por software da página inteira custa ~46 ms (A01c),
mas isso é o `flutter_tester` em CPU e fica para o `zywny`.

**`pictureBuilds`:** 98 antes e 98 depois de toda a sequência (5 capturas, 64
notas animando, `clearAll`). Nenhum `Picture` estático recompilado.

**Critérios**

1. Cinco frames com cores distintas convivendo (tabela e recortes acima).
2. Frame médio com 64 notas: 2,02 ms (< 8 ms). Dentro do orçamento; nada a
   investigar.
3. Nenhum `Picture` recompilado durante as animações (98 = 98).
4. `widget_vs_harness_test.dart` (R05c) em 0 pixels.
5. `flutter analyze` limpo, `flutter test` verde (130/130).
