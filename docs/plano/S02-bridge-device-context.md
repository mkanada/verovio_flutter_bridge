# S02 — `BridgeDeviceContext`: renomear e limpar a IR

**Depende de:** F01, S01 · **Decisão necessária:** não

## Objetivo

Renomear o device context e a IR herdados do `verovio_lottie` para o vocabulário
deste projeto e remover o que só existia por causa do Lottie, **sem mudar uma
linha de geometria**. É uma refatoração mecânica, e o critério de aceite prova
que ela é mecânica.

## Ler antes (só isto)

- `verovio/include/vrv/lottiedevicecontext.h` (219 linhas, a superfície inteira).
- `verovio/include/vrv/lottiegeometry.h` (111 linhas).
- `verovio/src/lottiedevicecontext.cpp`: `MakeGlyphShape` L388-L429 e
  `DrawText` L446-L560 (são os dois trechos que S03/S05 vão mexer depois).

## O que fazer

1. Renomear arquivos e símbolos:

   | De | Para |
   | --- | --- |
   | `lottiedevicecontext.{h,cpp}` | `bridgedevicecontext.{h,cpp}` |
   | `lottiegeometry.h` | `bridgegeometry.h` |
   | `LottieDeviceContext` | `BridgeDeviceContext` |
   | `LottieVec`/`LottieBezier`/`LottieShape`/`LottieShapeKind` | `BridgeVec`/`BridgeBezier`/`BridgeShape`/`BridgeShapeKind` |
   | `LottieTextRun`/`LottieNode`/`LottieChild`/`LottiePage` | `BridgeTextRun`/`BridgeNode`/`BridgeChild`/`BridgePage` |
   | guardas `__VRV_LOTTIE_*__` | `__VRV_BRIDGE_*__` |

   Atualize o `ClassId` em `include/vrv/vrvdef.h` L289
   (`LOTTIE_DEVICE_CONTEXT` → `BRIDGE_DEVICE_CONTEXT`, na lista que já tem
   `BBOX_DEVICE_CONTEXT`/`SVG_DEVICE_CONTEXT`) e o `#include` em `src/toolkit.cpp`.

2. Remover da IR e do device context o que era exigência do Lottie e não tem
   lugar no formato novo (confira contra a tabela de correspondência de S01) —
   se **não houver nada** nessa situação, registre isso nas notas de execução e
   não invente remoção.

3. Ajustar comentários que citam Lottie/dotLottie/state machine para descrever
   o formato novo. Comentários que documentam **paridade com o SVG** (ex.: "a
   mesma aritmética inteira de `SvgDeviceContext::DrawMusicText`") são valiosos:
   mantenha-os palavra por palavra.

4. Compilar.

## Fora de escopo

- Mudar o tratamento de glifos (S03) ou acrescentar bbox (S04).
- Escrever qualquer serializador (S05).
- Qualquer mudança de comportamento de desenho.

## Critérios de aceite

1. Compila: `cd verovio/tools && cmake ../cmake && make -j4`.
2. Nenhum resíduo de nome: `grep -rni "lottie" verovio/src verovio/include` só
   pode casar dentro de comentários que citem explicitamente o projeto anterior
   como referência histórica (idealmente, vazio).
3. **A refatoração não mudou a cena.** Antes de renomear, gere a IR serializada
   com um dump temporário (ou use o binário antigo do `verovio_lottie` com
   `-t lottie`) para 3 peças do corpus e guarde. Depois de renomear, gere de
   novo e compare byte a byte. Se o serializador ainda não existir (S05), use
   este critério substituto, que é igualmente forte:

   ```sh
   # o SVG não pode mudar, e o binário deve continuar carregando as 5 peças
   for f in corpus/mei/*.mei corpus/musicxml/*.mxl; do
     ./verovio/tools/verovio -t svg -a --resource-path verovio/data -o /tmp/s2 "$f" || exit 1
   done
   ```

   mais uma execução do `RenderToDeviceContext` com o `BridgeDeviceContext` em
   todas as páginas do corpus sem crash nem assert (ver S05 para o gancho de
   CLI; até lá, um teste temporário em `tools/` serve — apague-o no fim).
4. `git diff --stat` mostra só renomeações e ajustes de comentário; nenhum
   arquivo com mudança de lógica de desenho.

## Notas de execução

(a preencher por quem executar)
