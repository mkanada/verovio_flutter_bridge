# A01c — `ScoreController` (cor instantânea) e medições

**Depende de:** A01b · **Decisão necessária:** não

## Objetivo

Dar ao host o controle de cor por `xml:id` — instantâneo, sem animação — e
medir o custo real das operações que a fase A inteira vai depender. Animação
é A02; aqui o objetivo é a API e os números.

## Ler antes (só isto)

- `score_bridge/lib/src/score_page_view.dart` (A01b).
- Requisito 3 do [`CLAUDE.md`](../../CLAUDE.md) (controle de cor individual
  em runtime).

## Contexto que você precisa (não vá procurar, está aqui)

- A cor de uma nota é **uma cor só**: o formato foi desenhado para que trocar
  a cor do nó da nota recolora toda a subárvore por herança (cabeça, haste,
  pontos, acidente quando faz parte do nó). É isso que torna a operação
  barata — não há varredura de formas.
- A cor "de volta" não é preto fixo: é a **cor herdada original** daquele nó
  na cena (partituras com `@color` no MEI têm notas coloridas). Resolva e
  guarde essa cor ao montar os segmentos (A01a), não por frame.
- `ChangeNotifier` + `repaint:` no `CustomPainter` repinta sem `setState` —
  não chame `setState` numa mudança de cor, senão você reconstrói a árvore de
  widgets 60 vezes por segundo.
- `notifyListeners()` chamado N vezes num frame provoca N repaints agendados;
  agrupe as mudanças de um mesmo instante (isso vira essencial em A02, quando
  64 notas mudam de cor no mesmo tick).

## O que fazer

1. `score_bridge/lib/src/score_controller.dart`:

   ```dart
   class ScoreController extends ChangeNotifier {
     Color? colorOf(String id);
     void setColor(String id, Color color);
     void clearColor(String id);
     void clearAll();
     void setColors(Map<String, Color> colors);   // uma notificação só
   }
   ```

2. Ligar ao `ScorePageView`: o painter consulta o controller ao pintar os
   segmentos dinâmicos; os estáticos ignoram o controller por construção.

3. Um id no controller que **não** está em `animatableIds` não tem efeito
   (ele está dentro de um `Picture` estático). Isso precisa ser explícito:
   ou documentado como limitação, ou o widget promove o id a dinâmico e
   recompila a página. Escolha, documente e teste o comportamento escolhido —
   um `setColor` silenciosamente ignorado é um bug difícil no app do usuário.

4. **Medir e registrar** (a máquina e o backend também):
   - tempo de compilação dos `Picture` por página (mediana de 10);
   - tempo de um repaint com 1 cor alterada (mediana de 100);
   - tempo de um repaint com 64 cores alteradas (mediana de 100);
   - segmentos por página (da instrumentação de A01a).

## Fora de escopo

- Curvas, fade, tempo (A02).
- Disparo por timemap (A05).

## Critérios de aceite

1. `flutter analyze` limpo, `flutter test` verde.
2. Teste de cor: `setColor(id, vermelho)` recolore **toda** a subárvore
   daquele nó (cabeça e haste), e nenhum outro elemento da página — verificado
   por render e comparação de pixels contra o estado de repouso.
3. Teste de restauração: `clearColor(id)` devolve a página a um estado
   **byte-idêntico** ao repouso (0 pixels), inclusive num nó cuja cor original
   vem de `@color` no MEI (use um fixture com cor, ou crie um).
4. `setColors` com 64 ids dispara **uma** notificação (teste com contador de
   listeners).
5. Nenhum `Picture` estático recompilado em nenhuma das operações acima
   (`pictureBuilds` constante).
6. Os quatro números medidos estão nas notas, com máquina e backend.
7. Comportamento escolhido para id não-animável documentado e testado.

## Notas de execução

(a preencher por quem executar)
