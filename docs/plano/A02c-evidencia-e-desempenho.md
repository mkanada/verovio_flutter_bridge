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

- Medição em dispositivo (P03) — aqui é a máquina de desenvolvimento.
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

(a preencher por quem executar)
