# P03a — Perfil em dispositivo Android

**Depende de:** A05b, P01a · **Decisão necessária:** não

## Objetivo

Sair da máquina de desenvolvimento: medir no aparelho, achar o que está caro
e corrigir **nos passos de origem**. Números de desktop não provam nada sobre
uma partitura rolando num celular.

## Ler antes (só isto)

- Notas de execução de A01c, A02c e P01a (os números de desktop, que são a
  base de comparação).
- [`docs/relatorio-paridade.md`](../relatorio-paridade.md) (R06c).

## Contexto que você precisa (não vá procurar, está aqui)

- Alvo: **nenhum frame acima de 16 ms em regime permanente** durante o
  playback (jank isolado na abertura é aceitável, se registrado).
- Orçamento já medido em desktop (A02c): repaint com 64 notas animando abaixo
  de 8 ms. No aparelho, espere algo entre 2× e 5× disso — é por isso que a
  margem de 8 ms existe.
- Carga por página, medida no corpus: ~1 345 formas (mediana), até 2 463; ~196
  segmentos alternados (mediana), até 545; ~98 `Picture` estáticos por página
  na mediana.
- Onde procurar, em ordem: (1) compilação de `Picture` acontecendo durante a
  animação (não deveria — contador de A01b), (2) alocação por nota por frame
  no motor de A02a, (3) `TextPainter` reconstruído por frame (o texto é
  estático: se ele está sendo remontado, algo está no segmento errado),
  (4) páginas fora da janela mantendo `Picture` vivo (A03c).
- **Emulador não serve** para este passo: o perfil de GPU é diferente demais.
- `flutter run --profile` + DevTools timeline; registre **o modelo do
  aparelho** junto com cada número, senão o número não significa nada.

## O que fazer

1. Perfilar na peça mais pesada disponível (a peça grande de P01a, se houver;
   senão, o Chopin Nocturne, 7 páginas / 2 665 glifos):
   - tempo até o primeiro frame com a partitura na tela;
   - frames acima de 16 ms durante 64 notas animando;
   - frames acima de 16 ms durante a virada de página;
   - frames acima de 16 ms durante a rolagem contínua;
   - memória residente ao longo de uma peça inteira.
2. Corrigir o que estiver ruim **no passo de origem** (A01/A02/A03), nunca com
   remendo no app de exemplo.
3. Depois de **cada** correção, rodar de novo o critério 1 de A01b (render
   segmentado byte-idêntico) e o teste widget-vs-harness de R05c — otimização
   é a forma clássica de quebrar paridade sem perceber.

## Fora de escopo

- App de exemplo (P03b) e documentação final (P03c).
- Otimização especulativa sem número.

## Critérios de aceite

1. Números registrados em `docs/medicoes.md`, ao lado dos de desktop, com o
   **modelo do aparelho** e a versão do Flutter.
2. Nenhum frame acima de 16 ms em regime permanente durante o playback de
   A05b no dispositivo; jank de abertura registrado se houver.
3. Toda correção feita cita o passo de origem e foi revalidada pelos critérios
   daquele passo, incluindo o byte-idêntico de A01b e o 0 pixels de R05c.
4. A rolagem contínua de uma peça de 7+ páginas não cresce a memória de forma
   monotônica (gráfico ou números antes/durante/depois nas notas).
5. Se algum alvo não for atingido, a causa está registrada e levada ao
   usuário — não declare o passo concluído com um alvo em aberto.

## Notas de execução

(a preencher por quem executar)
