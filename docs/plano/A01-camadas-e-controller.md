# A01 — Camadas, cache de `Picture` e `ScoreController`

**Depende de:** R06 · **Decisão necessária:** não

## Objetivo

Transformar o painter num widget de produção: conteúdo estático compilado uma
vez em `ui.Picture` e elementos endereçáveis pintados ao vivo, **sem alterar a
ordem de pintura**. É o passo que torna a cor por nota barata o suficiente para
rodar a 60 fps.

## Ler antes (só isto)

- `score_bridge/lib/src/scene_painter.dart` (R02) e o percurso da árvore.
- Seção 6 da [especificação](../formato/especificacao-v1.md) (ordem de pintura).
- Riscos 3 do [README do plano](README.md).

## O que fazer

1. **Segmentação por ordem de documento** (o ponto delicado): percorrendo a
   árvore da página em ordem, produza uma lista de segmentos alternados:

   ```
   [estático_0][dinâmico: id=note-1][estático_1][dinâmico: id=note-2]…
   ```

   Um nó é **dinâmico** se seu `id` está no conjunto `animatableIds` passado ao
   widget (padrão: os ids que aparecem no `timemap` do documento). Todo o resto
   é estático. Runs estáticos consecutivos são fundidos num único `ui.Picture`.

   Isso preserva a ordem exatamente: nada que o Verovio desenha por cima de uma
   nota (ligadura, dinâmica, articulação) vai parar embaixo dela.

2. `ScorePageView`:
   - `CustomPaint` com um painter que desenha os segmentos em ordem;
   - `Picture`s estáticos recriados **só** quando muda a página, o tamanho do
     canvas ou o documento (nunca quando muda cor);
   - `repaint:` ligado ao `ScoreController` (um `Listenable`), para que mudança
     de cor repinte sem reconstruir widget nem refazer layout;
   - `RepaintBoundary` em volta.

3. `ScoreController extends ChangeNotifier`:

   ```dart
   Color? colorOf(String id);
   void setColor(String id, Color color);
   void clearColor(String id);
   void clearAll();
   ```

   Neste passo, só cor instantânea — animação é A02.

4. Medir e registrar: nº de segmentos por página no corpus (mediana e máximo),
   tempo de compilação dos `Picture`s e tempo de um repaint com 1 cor alterada.

## Fora de escopo

- Animação/curvas (A02), navegação de página (A03), overlays (A04).
- Qualquer otimização baseada em palpite: meça primeiro (o nº de segmentos por
  página é o número que decide se algo mais é necessário).

## Critérios de aceite

1. **A segmentação não muda um pixel.** Para as 34 páginas do corpus, o render
   segmentado (sem nenhuma cor sobrescrita) é **byte-idêntico** ao render de
   passada única de R02/R05 (`cmp` nos PNGs). Este é o critério mais importante
   do passo: ele prova que a ordem de pintura foi preservada.
2. Trocar a cor de uma nota **não** recria nenhum `ui.Picture` estático (teste
   com contador de compilações).
3. Números registrados nas notas: segmentos por página (mediana/máx), tempo de
   compilação por página, tempo de repaint com 1 cor alterada (mediana de 100
   medições).
4. `flutter analyze` limpo, `flutter test` verde, incluindo o teste
   widget-vs-harness de R05 (que continua dando 0 pixels).

## Notas de execução

(a preencher por quem executar)
