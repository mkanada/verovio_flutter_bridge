# A03b — Virada por haste: `pagedSweep` (e `pagedSlide`)

**Depende de:** A03a, A02b, A04a · **Decisão necessária:** não (mas confirme
com o usuário o tom exato de azul e a largura da haste antes de fixá-los)

## Objetivo

A virada de página **por haste** (a "cortina"): a página atual e a próxima
ficam renderizadas ao mesmo tempo, uma sobre a outra, e uma haste vertical azul
varre a página atual da esquerda para a direita, revelando a próxima atrás dela.
Este passo entrega o **mecanismo visual** (camadas, recorte e haste, dirigidos
por uma posição x). **Quando** a haste anda — a regra por compasso e nota — é do
A05b.

E a prova de que, aqui, virar página **não cancela** o destaque das notas — a
limitação que o projeto anterior não conseguiu remover.

## Ler antes (só isto)

- `score_bridge/lib/src/score_view.dart` (A03a).
- `score_bridge/lib/src/score_page_view.dart` (A01b) — o recorte é feito por
  cima dela, sem tocar nas camadas internas.
- A04a (`rectForId`) — é dele que sai o x de um compasso ou de uma nota.
- `../verovio_lottie/docs/plano/C04-paginas-virada.md`, só a parte do
  `pagedSlide` (a trilha horizontal). O `peek` daquele documento **não** vale
  mais: foi substituído pela haste.

## Comportamento decidido com o usuário (2026-09-21)

Trate como fixo — não reabra sem confirmar.

**Camadas.** A página atual (**A**) fica na frente; a próxima (**B**) fica atrás,
na mesma posição, coberta por A. As duas estão pintadas ao mesmo tempo.

**A haste.** Uma faixa vertical **opaca e azul**, de **altura total** da página,
com largura de **cerca de duas notas** (ver "Contexto"). Sua borda **direita** é
o ponto de corte: à **esquerda** da haste aparece B, à **direita** continua A,
em **todos os sistemas** da página (não só no último). A haste é desenhada por
cima de tudo, inclusive de overlays.

**Etapas de uma virada** (a posição da haste é sempre dada por `edgeX`, a borda
direita, em unidades de viewBox da página A):

1. **Entrada** — a haste entra pela borda esquerda (`edgeX` vai de `0` até o x
   de destino);
2. **Estacionada** — a haste fica parada no x de destino, enquanto A continua
   sendo destacada normalmente à direita dela;
3. **Conclusão** — a haste segue até a borda direita (`edgeX` vai de x até
   `larguraDaPágina + larguraDaHaste`, de modo que a haste saia inteira). B fica
   totalmente à mostra, vira a página atual e uma nova página seguinte (C) passa
   a ficar atrás.

**Duração de cada movimento:** `min(1 s, duraçãoDoCompasso / 4)`, com o teto de
1 s **configurável no futuro** (parâmetro, não constante espalhada).

**Sem virada:** na última página da peça não há haste nem página de trás.

Quem decide o x de destino, quando cada etapa começa e como isso se comporta em
`seek` ou no compasso de nota única é o A05b. Aqui o widget só obedece a
`edgeX`.

## Contexto que você precisa (não vá procurar, está aqui)

- **Os dois `ScorePageView` são independentes.** Cada um tem seu cache de
  `Picture` (A01b) e suas camadas de destaque. Como o destaque é cor por nó, uma
  nota de B acesa enquanto B está atrás/à esquerda da haste já aparece: a
  primeira nota da página seguinte pode ser destacada na etapa 3 e já estará
  visível na parte revelada. Nada disso exige código novo — é por isso que o
  destaque atravessa a virada "de graça".
- **O recorte é em pixels de tela**, não em unidades de viewBox: converta
  `edgeX` com a mesma conversão de A04a/A03c,
  `x_tela = (x + origin.x) * fit.scale + fit.tx`. Não invente uma segunda
  fórmula.
- **Repouso pixel-idêntico** (critério de A03a): no repouso — sem haste — **não
  há `ClipRect` nem haste na árvore**, só a página atual. O recorte só existe
  enquanto `edgeX` estiver estritamente entre `0` e o fim. Um `ClipRect`
  com borda fracionária durante a animação é aceitável; deixar um recorte
  "ligado" no repouso, não.
- **Páginas de tamanhos diferentes** (A03a): A e B ficam centradas uma sobre a
  outra; o recorte é em coordenadas de tela do widget, então funciona igual.
  A haste tem a altura da página **A** (a que está sendo varrida).
- **Largura da haste:** `2 ×` a largura da cabeça de nota preta
  (`noteheadBlack`), medida no dicionário de glifos em unidades de viewBox
  (bbox do glifo × escala de uso). Meça o número no corpus e registre nas notas.
  É um parâmetro (`barWidth`), com esse valor como padrão.
- **Cor:** azul opaco. O tom exato ainda não foi escolhido (parâmetro
  `barColor`); use um azul de contraste alto sobre papel branco e confirme com o
  usuário.
- **Custo:** durante a virada há duas páginas pintadas. Como cada uma reusa seu
  `Picture` (A01b), o custo por frame é dois `drawPicture`, sem recompilar
  nada; o perfil em dispositivo é feito no `zywny`.
- **Vida útil das páginas:** no máximo A, B e (depois da conclusão) C precisam de
  `Picture` vivo. Ao concluir, a página A antiga é liberada (`dispose`) —
  registre o contador de `Picture` nas notas, como em A03a.

## O que fazer

1. Parâmetros no `ScoreView`:

   ```dart
   ScoreView({
     ScorePageMode mode = ScorePageMode.pagedSweep,   // pagedSweep | pagedSlide
     Color barColor = const Color(0xFF...),           // azul, a confirmar
     double? barWidth,                                // null = 2 × noteheadBlack
     Duration maxSweepDuration = const Duration(seconds: 1),
     ValueListenable<SweepCurtain?>? curtain,         // A05b dirige por aqui
   })

   /// Estado da haste, sempre derivado de fora (A05b) — o widget não decide.
   class SweepCurtain {
     const SweepCurtain({required this.pageIndex, required this.edgeX});
     final int pageIndex;   // a página A que está sendo varrida
     final double edgeX;    // borda direita da haste, em unidades de viewBox de A
   }
   ```

   `curtain == null` (ou `edgeX` fora do intervalo aberto) é o repouso: só a
   página atual, sem haste nem recorte.

2. Modo `pagedSweep` em `score_view.dart`: `Stack` com B embaixo, A em cima
   recortada por um `ClipRect` que deixa passar só `x_tela >= borda direita da
   haste`, e a haste por cima. Quando `edgeX` chega ao fim, o widget executa a
   troca (equivalente a `nextPage()` instantâneo de A03a) e volta ao repouso.

3. Modo manual, para quem usa `ScoreView` sem o `ScorePlayer`:
   `sweepTo(double edgeX, {Duration? duration})` e `finishSweep({Duration?
   duration})`, que só animam o mesmo `edgeX` com um `AnimationController`. Em
   `pagedSweep`, `nextPage()` sem `SweepCurtain` externo faz a varredura inteira
   (`0` → fim) em `maxSweepDuration`.

4. Interrupção — **defina, documente e teste**:
   - `goToPage`, `previousPage` e qualquer mudança externa de `curtain` para
     `null`: cancelam a virada e vão direto ao repouso da página de destino;
   - `nextPage()` durante uma varredura em curso: conclui a varredura (vai ao
     fim), sem reiniciar;
   - `previousPage()` **nunca** anima com haste: é instantâneo.

5. `pagedSlide`: a trilha horizontal de A03a com uma transição só, sem haste.
   Continua sendo o modo alternativo para navegação manual.

6. Ao terminar a transição, a posição tem que assentar **exatamente** na página
   de destino (critério 1 de A03a: repouso pixel-idêntico).

## Fora de escopo

- A regra de quando a haste anda, o cálculo do x de cada compasso/nota, o caso
  de compasso único e a sincronia com o relógio (A05b).
- Rolagem contínua (A03c): não há virada nesse modo.
- Zoom/pan (não é requisito).

## Critérios de aceite

1. Com `sweepTo` manual, sequência de **5 frames** capturada e anexada nas
   notas: (1) repouso de A; (2) meio da entrada; (3) haste estacionada no início
   de um compasso; (4) meio da conclusão; (5) repouso de B. No frame 3, à
   esquerda da haste vê-se B e à direita A, **em todos os sistemas**; no frame
   4, a haste é opaca e azul e a largura é visivelmente a de ~2 notas.
2. O repouso ao fim da virada é **byte-idêntico** ao render estático da página
   de destino (0 pixels). Idem o repouso **antes** da virada: sem haste e sem
   `ClipRect` na árvore (verifique com `find.byType(ClipRect)`).
3. **Destaque sobrevive à virada**: acenda uma nota de A, à direita da haste,
   com `release` de 2 s; complete a varredura no meio do fade; confirme por
   frames que o fade continuou sem interrupção e que a cor final é a original.
   Acenda também uma nota de B na parte já revelada durante a varredura e
   confirme que ela aparece colorida. Anexe os frames.
4. Interrupções testadas: `nextPage()` durante a varredura, `goToPage()` no
   meio, `previousPage()` logo depois — nenhuma deixa haste ou recorte na
   árvore no repouso, nem posição inválida.
5. Na última página, `curtain` não desenha nada e `nextPage()` satura sem
   lançar (comportamento de A03a).
6. `maxSweepDuration`, `barColor` e `barWidth` estão registrados nas notas, e o
   tom de azul foi confirmado com o usuário (ou consta que ele aceitou o padrão).
7. `flutter analyze` limpo, `flutter test` verde; widget-vs-harness em 0
   pixels no repouso.

## Notas de execução

Concluído em 2026-09-21 (`score_view.dart`, `test/score_view_test.dart`).

- **Parâmetros registrados**: `barColor = 0xFF1565C0` (azul de alto contraste;
  **o usuário não confirmou o tom — é o padrão adotado, troque pelo
  parâmetro**), `barWidth = null` → `2 × noteheadBlack` medido no corpus:
  **452,2 unidades de viewBox** (45,2 px numa página de 2100 px; a cabeça de
  nota preta mede ≈ 226 unidades), igual nas 10 peças (mesma fonte/escala);
  `maxSweepDuration = kDefaultMaxSweepDuration = 1 s`.
- **Mecanismo**: `Stack` com B embaixo, A em cima sob `ClipRect(clipper:
  _RightOfClipper)` e a haste (`ColoredBox` opaca, altura da página A,
  aparada à página) por cima. Só existe com `edgeX` no intervalo aberto
  `(0, sweepEndX)`; `sweepEndX = xFromPagePx(widthPx) + barWidth`. A conversão
  viewBox→tela é a de `hit_test.dart` (uma fórmula só). Cada `ScorePageView`
  mora sob uma `GlobalKey` para o recorte aparecer/sumir sem recompilar
  `Picture`.
- **5 frames (critério 1)**: `test/score_view_test.dart` captura repouso de A,
  meio da entrada, haste estacionada, meio da conclusão e repouso de B
  (`compare/out/a03b/frame*.png`, git-ignorado; a sequência versionada, com
  o player, está em `docs/exemplos/virada-pagina/Nocturne/`). No frame
  estacionado, em **todos os sistemas**: à direita da haste A, à esquerda B,
  haste opaca `#1565C0` — 0 pixels fora da tolerância de 128/255.
  **Achado**: com o recorte ligado, o antialiasing de A muda em poucos níveis
  (ex.: 124 vs 119) por causa do `ClipRect`; por isso só o **repouso** exige
  0 pixels, e o frame de meio de virada usa a tolerância do projeto.
- **Repouso (critério 2)**: ao fim da virada o repouso de B é 0 pixels contra
  o harness; antes da virada e depois dela `find.byType(ClipRect)` é vazio.
- **Destaque atravessa a virada (critério 3)**: nota de A com `release: 2 s`,
  varredura concluída no meio do fade — a cor do controller cai
  monotonicamente antes/durante/depois da conclusão e termina na original;
  nota acesa em B na parte revelada aparece vermelha no frame.
- **Interrupções (critério 4)**, definidas e testadas: `goToPage` cancela e vai
  ao repouso do destino; `previousPage` é instantâneo (só `pagedSlide` anima);
  `nextPage` durante a varredura a **conclui**; nenhuma deixa haste/recorte.
  `curtain` externo tem a última palavra; `edgeX` fora do intervalo = repouso;
  `edgeX ≥ fim` executa a troca de página uma vez.
- **Última página (critério 5)**: `curtain`/`nextPage`/`sweepTo` não
  desenham nem lançam.
- **`pagedSlide`**: transição de 300 ms (`slideDuration`) por translação das
  duas páginas dentro de um `ClipRect`; anima nos dois sentidos.
- **Nota de teste**: o `Ticker` só conta a partir do primeiro quadro em que
  toca — depois de `forward()` é preciso um `pump()` antes do `pump(duração)`.
