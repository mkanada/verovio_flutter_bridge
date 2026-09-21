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

Executado em 2026-09-21. Medições na máquina de desenvolvimento
(Intel i5-4440 @ 3,1 GHz, 4 núcleos, Linux) sob o `flutter_tester` — Skia com
rasterização por software na CPU; **não** é o backend de produção nem GPU.

**O que foi feito**

- `lib/src/score_controller.dart` (novo): `ScoreController extends
  ChangeNotifier` com `colorOf`, `colors` (visão somente leitura, a mesma
  para sempre), `setColor`, `setColors`, `clearColor`, `clearAll`,
  `attachDocument`. O `ScorePageView` chama `attachDocument` sozinho.
- Ligação: o painter recebe `controller.colors` como `colorOverrides` **só dos
  segmentos dinâmicos**; os estáticos ignoram o controller por construção.

**Decisões**

- **Precedência de cor de um id:** animação ativa > cor "fixa" de `setColor` >
  cor original do nó. `setColor` é a **cor de repouso**: um destaque parte
  dela e volta a ela. `clearColor` volta à original (e, durante um destaque, o
  `release` passa a ir para a original).
- **Cor original resolvida uma vez por documento** (visitante de `walkScene`
  sobre todas as páginas, no primeiro uso), não por frame; vem com o `@color`
  do MEI (`node.color`) e a herança.
- **Id não-animável: o widget o promove a dinâmico e recompila a página**
  (escolha entre "documentar como limitação" e "promover"): quando o controller
  tem cor para um id que existe na página e não está em `animatableIds`, o
  `ScorePageViewState` acrescenta o id e recria as camadas (uma recompilação
  por promoção; o custo aparece em `pictureBuilds`). O caminho barato continua
  sendo declarar os ids em `animatableIds` (padrão: timemap). Testado com
  `animatableIds: {}` (página = 1 segmento; `setColor` recolore, recompila uma
  vez, a segunda troca não recompila, `clearAll` volta byte-idêntico).
- **Id que não existe no documento é ignorado em silêncio** (com documento
  associado) — necessário para os ids `-rend2` do timemap. Sem documento tudo
  é aceito.
- Uma notificação por operação pública, e nenhuma se nada mudou.

**Medições** (`flutter test tool/measure_a01c.dart`; 34 páginas; mediana entre
páginas / máximo)

| Medida | Mediana | Máximo |
| --- | ---: | ---: |
| Segmentos por página (A01a) | 197 | 545 |
| `Picture` estáticos por página | 99 | 273 |
| Compilação dos `Picture` (mediana de 10 por página) | **1,85 ms** | 4,01 ms |
| Repaint (gravar a página) sem cor alterada (mediana de 100) | 1,16 ms | 2,27 ms |
| Repaint com **1** cor alterada (mediana de 100) | **1,16 ms** | 2,29 ms |
| Repaint com **64** cores alteradas (mediana de 100) | **1,19 ms** | 2,37 ms |
| Repaint + `toImage` da página inteira (software; mediana de 30) | 45,7 ms | 62,3 ms |

Ler: o repaint custa o mesmo com 0, 1 ou 64 cores — o custo é percorrer os nós
dinâmicos, não colori-los. A linha "raster" é só a ordem de grandeza da
rasterização por CPU, a medir em dispositivo em P03. (A mediana de segmentos é
197 aqui contra 196 no plano: número par de páginas, escolha do elemento
superior.)

**Critérios**

1. `flutter analyze` limpo, `flutter test` verde (130/130).
2. `setColor` recolore a nota inteira — cabeça **e** haste — e nenhum outro
   elemento: todos os pixels diferentes ficam dentro da bbox da nota, cobrem
   mais de 80% da altura dela e são avermelhados.
3. `clearColor` → 0 pixels contra o repouso, e com nota de `@color` azul o
   repouso volta ao **azul**, não ao preto.
4. `setColors` com 64 ids → 1 notificação (uma segunda chamada idêntica → 0).
5. `pictureBuilds` constante em todas as operações de cor.
6. Números na tabela acima, com máquina e backend.
7. Id não-animável (promoção) e id inexistente (ignorado): documentados e
   testados.
