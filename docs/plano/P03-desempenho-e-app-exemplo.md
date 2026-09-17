# P03 — Desempenho em dispositivo, app de exemplo e documentação final

**Depende de:** A05, P01 · **Decisão necessária:** não

## Objetivo

Fechar o projeto: provar que roda bem num dispositivo real, deixar um exemplo
que demonstre os quatro requisitos, e documentar tudo para quem chegar depois.

## Ler antes (só isto)

- Notas de execução de A01, A02 e P01 (os números de desktop, que são a base de
  comparação).
- [`docs/relatorio-paridade.md`](../relatorio-paridade.md) (R06).

## O que fazer

1. **Perfil em dispositivo** (Android real, não emulador), na peça mais pesada
   disponível:
   - `flutter run --profile` + DevTools timeline;
   - medir: tempo até o primeiro frame com a partitura na tela; frames acima de
     16 ms durante 64 notas animando; durante a virada de página; durante a
     rolagem contínua;
   - registrar o modelo do aparelho.
2. Corrigir o que estiver ruim **nos passos de origem** (A01/A02/A03), não com
   remendos no app de exemplo. Cada correção exige rodar de novo o critério 1
   de A01 (render segmentado byte-idêntico) — otimização é a forma clássica de
   quebrar paridade sem perceber.
3. **App de exemplo** (`example/`) demonstrando, numa tela só:
   - abrir uma peça do corpus;
   - playback automático pelo timemap (A05);
   - tocar numa nota para acendê-la/apagá-la (A02+A04);
   - trocar a cor de destaque em runtime;
   - alternar entre `pagedPeek` e `continuousScroll`.
4. **Documentação final**:
   - `README.md` da raiz: estado real, como buildar, como usar;
   - `score_bridge/README.md`: a API pública com exemplos curtos;
   - `docs/formato/especificacao-v1.md`: atualizado com tudo que a
     implementação descobriu (o "Histórico de revisões" tem que refletir);
   - `CLAUDE.md`: decisões que mudaram durante a execução.

## Fora de escopo

- Publicar o pacote no pub.dev.
- Integração com o zywny propriamente dita.

## Critérios de aceite

1. Números de dispositivo registrados em `docs/medicoes.md`, ao lado dos de
   desktop, com o modelo do aparelho.
2. Nenhum frame acima de 16 ms em regime permanente durante o playback de A05
   no dispositivo (jank isolado na abertura é aceitável se registrado).
3. O app de exemplo roda em Linux desktop e Android e demonstra os 5 itens
   acima; anexe um vídeo curto ou 5 capturas nas notas.
4. `flutter analyze` limpo em `score_bridge/`, `compare/` e `example/`.
5. Os quatro requisitos do `CLAUDE.md` estão declarados como atendidos, cada um
   apontando para a evidência que o prova:
   - paridade > 99,9% → `docs/relatorio-paridade.md` (R06);
   - animação individual por nota → critério 2 de A02;
   - cor individual em runtime → critérios 1 e 3 de A02;
   - virada de página + overlays → A03 e A04.
6. A tabela de passos do [README do plano](README.md) está com todos os passos
   marcados como `concluído`, cada um com suas notas de execução preenchidas.

## Notas de execução

(a preencher por quem executar)
