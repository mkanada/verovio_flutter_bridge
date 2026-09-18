# A03b — Virada animada: `pagedPeek` e `pagedSlide`

**Depende de:** A03a, A02b · **Decisão necessária:** não (mas confirme as
constantes de tempo com o usuário antes de fixá-las)

## Objetivo

A virada de página no estilo Synthesia: a próxima página **espreita** antes de
cobrir. E a prova de que, aqui, virar página **não cancela** o destaque das
notas — a limitação que o projeto anterior não conseguiu remover.

## Ler antes (só isto)

- `../verovio_lottie/docs/plano/C04-paginas-virada.md`, seções "Decisões de
  escopo" e "Notas de execução" — as constantes já calibradas e o erro já
  cometido.
- `score_bridge/lib/src/score_view.dart` (A03a).

## Contexto que você precisa (não vá procurar, está aqui)

Constantes **já calibradas visualmente** no projeto anterior (a 30 fps):

| Parâmetro | Valor | Origem |
| --- | --- | --- |
| `peekFraction` | **0,08** (8% da distância até a próxima página) | C04 |
| duração do peek | ~500 ms (15 frames) | C04 |
| duração do cover | ~667 ms (20 frames) | C04 |

E o erro que já custou uma rodada: a primeira versão do C04 usava
`peekFraction = 0.6`. Com 60%, a página atual já sai quase inteira de cena
antes de o "cobrir" começar — não é um espreitar sutil, é a virada inteira em
duas etapas. **Não repita.**

Duas fases, como no projeto anterior:

- (A) `peekNextPage()` revela `peekFraction` da próxima página e **para** —
  é o aviso visual de que a virada vem;
- (B) `nextPage()` completa a transição.

O host (A05) chama (A) ao entrar no último compasso da página e (B) ao entrar
no primeiro compasso da seguinte.

**O ponto que justifica o projeto**: no Lottie, a virada exigia uma segunda
instância de engine, e isso cancelava o fade das notas (item 3 de
`docs/licoes-do-verovio-lottie.md`). No Flutter, virada é transformação de
widget e destaque é cor por nó: são independentes por construção. O critério 3
deste passo existe para provar que saiu de graça, não para implementar algo.

## O que fazer

1. Parâmetros no `ScoreView`, com os defaults calibrados acima:

   ```dart
   ScoreView({
     ScorePageMode mode = ScorePageMode.pagedPeek,   // pagedPeek | pagedSlide
     Duration peekDuration  = const Duration(milliseconds: 500),
     Duration coverDuration = const Duration(milliseconds: 667),
     double peekFraction = 0.08,
     Curve peekCurve = Curves.easeOut,
     Curve coverCurve = Curves.easeInOut,
   })
   ```

2. API: `peekNextPage()`, `nextPage()`, `previousPage()`, e o comportamento de
   interrupção (o que acontece se `nextPage()` chegar durante o peek, ou um
   `goToPage` no meio do cover) — **defina, documente e teste**; é o tipo de
   caso que o host real vai produzir.

3. `pagedSlide`: a mesma trilha, sem a fase de peek (uma transição só).

4. Ao terminar a transição, a posição tem que assentar **exatamente** na
   página de destino (ver o critério 1 de A03a: repouso pixel-idêntico).

## Fora de escopo

- Rolagem contínua (A03c).
- Disparo automático por compasso (A05b).
- Zoom/pan (não é requisito).

## Critérios de aceite

1. Sequência `peekNextPage()` → `nextPage()` capturada em **5 frames**
   (repouso, meio do peek, fim do peek, meio do cover, repouso da próxima) e
   anexada nas notas. No fim do peek, a página atual ainda está quase inteira
   visível — é o erro do C04 que este critério previne.
2. O repouso ao fim da virada é **byte-idêntico** ao render estático da página
   de destino (0 pixels).
3. **Destaque sobrevive à virada**: acenda uma nota com `release` de 2 s,
   dispare a virada no meio, e confirme por frames que o fade continuou sem
   interrupção e que a cor final é a original. Anexe os frames.
4. Interrupções testadas: `nextPage()` durante o peek, `goToPage()` durante o
   cover, `previousPage()` logo após `nextPage()` — nenhuma deixa a câmera
   fora de uma posição de repouso válida.
5. As constantes usadas estão registradas nas notas e foram confirmadas com o
   usuário (ou está registrado que ele aceitou os defaults do C04).
6. `flutter analyze` limpo, `flutter test` verde.

## Notas de execução

(a preencher por quem executar)
