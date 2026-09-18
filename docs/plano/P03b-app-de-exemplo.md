# P03b — App de exemplo

**Depende de:** P03a · **Decisão necessária:** não

## Objetivo

Um aplicativo pequeno que demonstra os quatro requisitos numa tela só — o que
o usuário abre para ver o projeto funcionando, e o que serve de referência de
uso da API para quem for integrar no zywny.

## Ler antes (só isto)

- `score_bridge/lib/score_bridge.dart` (a API pública exportada).
- Notas de execução de A02c, A03b, A04b e A05b (as APIs a demonstrar).

## Contexto que você precisa (não vá procurar, está aqui)

- Os quatro requisitos do [`CLAUDE.md`](../../CLAUDE.md) que a tela precisa
  tornar visíveis: paridade visual, animação individual por nota, cor
  individual em runtime, virada de página + overlays.
- O exemplo é **cliente da API pública**: se ele precisar importar
  `package:score_bridge/src/...`, a API pública está incompleta — conserte a
  API, não o exemplo.
- Peça boa para demonstrar: uma com 3+ páginas e duas vozes claras (Chopin
  Nocturne, Clair de Lune) — mostra virada e vozes simultâneas.
- Se P02 tiver sido executado com decisão (a)/(c), o exemplo abre um `.mei` e
  gera o `.vsb` na hora; senão, embute um `.vsb` pré-gerado como asset.

## O que fazer

1. `example/` demonstrando, numa tela só:
   - abrir uma peça do corpus;
   - playback automático pelo timemap (A05);
   - tocar numa nota para acendê-la/apagá-la (A02 + A04);
   - trocar a cor de destaque em runtime (um seletor simples);
   - alternar entre `pagedPeek` e `continuousScroll`.
2. Nada de estado global nem de gambiarra de cache no exemplo: ele é a prova
   de que a API basta.
3. Rodar em Linux desktop e Android.

## Fora de escopo

- Publicar no pub.dev.
- Integração com o zywny propriamente dita.
- Áudio.

## Critérios de aceite

1. O app roda em Linux desktop **e** Android e demonstra os 5 itens acima.
2. Cinco capturas (ou um vídeo curto) anexadas nas notas, uma por item.
3. O exemplo importa **apenas** `package:score_bridge/score_bridge.dart` —
   nenhum import de `src/`.
4. `flutter analyze` limpo em `example/`.
5. O `README.md` do exemplo diz como rodá-lo nas duas plataformas.

## Notas de execução

(a preencher por quem executar)
