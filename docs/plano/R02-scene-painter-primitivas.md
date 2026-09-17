# R02 — `ScenePainter`: primitivas, cor herdada e ajuste de página

**Depende de:** R01 · **Decisão necessária:** não

## Objetivo

Desenhar a cena no `Canvas`: transformação de página, percurso da árvore com
herança de cor, e as primitivas geométricas (path, rect, ellipse) com traço e
preenchimento. Glifos ficam para R03 e texto para R04 — este passo já produz
pentagramas, hastes, barras de compasso, ligaduras e feixes.

## Ler antes (só isto)

- Especificação, seções 3 (unidades/ajuste), 5.2 (formas) e 6 (ordem de
  pintura e estado herdado).
- Seção 4.1 da especificação (conversão v/i/o → `Path`) — vale para as formas
  `p` também, não só para glifos.
- `verovio/src/svgdevicecontext.cpp` L686-L1017 (as primitivas que o SVG emite,
  para conferir semântica quando houver dúvida).

## O que fazer

1. `lib/src/scene_painter.dart`:

   ```dart
   class ScenePainter {
     ScenePainter(this.page, this.glyphs, {this.colorOverrides = const {}});
     void paint(Canvas canvas);
   }
   ```

2. Transformação de página, **nesta ordem** (seção 3):

   ```dart
   canvas.translate(fit.tx, fit.ty);
   canvas.scale(fit.scale);
   canvas.translate(origin.dx, origin.dy);
   ```

3. Percurso recursivo com uma pilha de cor corrente (inicial `0xFF000000`):
   - nó `hidden` → não desenha nada, nem filhos;
   - nó com `color` → empilha;
   - nó com `rotate` → `canvas.save(); canvas.translate(ox,oy);
     canvas.rotate(radians(angle)); canvas.translate(-ox,-oy);` … `restore()`
     (confirme o sinal contra o SVG: `rotate(a, ox, oy)` é horário em graus com
     y para baixo — o passo D04 do projeto anterior já validou a convenção);
   - filhos em ordem: o último pinta por cima.

4. Formas:
   - `fill` ausente → cor herdada; `"none"` → não preenche;
   - `stroke` ausente → cor herdada **quando o exportador marcou traço**
     (o formato já traz `strokeWidth` resolvido; se não há `strokeWidth`, não
     há traço);
   - `Paint` com `isAntiAlias: true`, `style` separado para fill e stroke (dois
     `drawPath`, não um `Paint` híbrido);
   - `strokeCap`/`strokeJoin` mapeados de `lineCap`/`lineJoin`;
   - `dash`: implemente com um utilitário próprio de `PathMetrics` (o Flutter
     não tem tracejado nativo). Se o corpus não tiver nenhum tracejado, faça
     mesmo assim, mas registre nas notas que não há caso de teste real.
   - `fillOpacity`/`strokeOpacity` multiplicam o alfa da cor.

5. Cache: converta cada `ScenePath` em `ui.Path` **uma vez** e guarde no objeto
   (lazy), porque A01 vai repintar a camada dinâmica muitas vezes.

## Fora de escopo

- Glifos (R03), texto (R04).
- Widget, camadas e cache de `Picture` (A01).
- `colorOverrides` já aparece na assinatura, mas o comportamento por nota é
  especificado e testado em A02; aqui basta ele existir e ser respeitado na
  herança.

## Critérios de aceite

1. `flutter analyze` limpo; `flutter test` verde.
2. Teste unitário de conversão v/i/o → `Path`: para um Bézier conhecido,
   compare `path.computeMetrics().first.length` e 10 pontos amostrados com
   valores calculados à mão (tolerância `1e-6`).
3. Teste de herança de cor: árvore sintética com 3 níveis (`color` no meio),
   conferindo a cor efetiva de cada forma via um `Canvas` de mentira que grava
   as chamadas (`RecordingCanvas` de teste, ou `TestRecordingCanvas` própria).
4. Teste do ajuste de página: para uma página do corpus, o ponto `origin` em
   coordenadas de viewBox tem que cair, depois da transformação, exatamente no
   pixel esperado por `fit` (calcule à mão no teste).
5. **Primeira evidência visual**: renderize a página 1 de uma peça simples do
   corpus (Gymnopédie ou Scarlatti) e compare com o PNG do SVG. Ainda vai faltar
   todo o conteúdo de glifo e texto, então o critério aqui não é a %, e sim:
   pentagramas, barras de compasso e hastes **em cima** das do SVG (sobreponha
   as duas imagens; nenhum deslocamento visível). Anexe a imagem nas notas.

## Notas de execução

(a preencher por quem executar)
