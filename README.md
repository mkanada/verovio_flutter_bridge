# verovio_flutter_bridge

Fork do [Verovio](https://www.verovio.org/) (motor de gravação musical em C++,
MEI/MusicXML → SVG) que adiciona um **exportador de formato intermediário de
cena** (`.vsb` — *Verovio Score Bridge*), mais um **pacote Flutter que lê esse
formato e desenha a partitura** com `CustomPaint`, permitindo:

- **Renderização idêntica** à saída SVG do próprio Verovio (critério: > 99,9%
  dos pixels iguais na comparação SVG→PNG vs. Flutter→PNG).
- **Animação individual por nota**, sem limite de quantas notas animam ao mesmo
  tempo e com curvas independentes por nota.
- **Controle de cor individual** por `xml:id`, em tempo real, pelo app host.
- **Virada/navegação de página** e overlays de widget posicionados sobre
  qualquer elemento da partitura (via *bounding boxes* exportadas).

É a base do projeto de e-learning musical **zywny**, que cruza o `.vsb` com o
`timemap` que o Verovio já produz.

## Por que este projeto existe

O projeto anterior (`../verovio_lottie`) tentou o mesmo objetivo exportando
**dotLottie**. A paridade visual foi alcançada (média de 0,1251% de pixels
divergentes), mas a camada de animação do formato bateu em cinco limites
estruturais do runtime — playhead único, modos de destaque mutuamente
exclusivos, dois engines não compositáveis, bug de itálico que exigiu fork do
ThorVG, e conflito entre reuso de glifo e cor por nota. Todos os cinco somem
quando o renderizador é o próprio Flutter.

Ver [`docs/licoes-do-verovio-lottie.md`](docs/licoes-do-verovio-lottie.md) para
o detalhamento (o que foi provado, o que travou, e o que foi reaproveitado).

## Estrutura do repositório

- **`verovio/`** — o fork do Verovio vendorizado (6.3.0), onde vive o
  exportador `.vsb` (`src/bridge*.cpp`, `include/vrv/bridge*.h`).
- **`score_bridge/`** — pacote Flutter/Dart: parser do `.vsb`, `ScenePainter`,
  widget `ScorePageView` e `ScoreController` (cor/animação por nota).
- **`compare/`** — ferramenta de comparação visual SVG vs. Flutter
  (`svg_render/` em Rust/resvg para SVG→PNG; app Flutter para cena→PNG e diff
  pixel a pixel).
- **`corpus/`** — partituras de domínio público (MEI/MusicXML) de teste.
- **`docs/`** — especificação do formato, plano de implementação e decisões.

## Estado

Em implementação. O plano passo a passo, com critérios de aceite verificáveis
para cada passo, está em [`docs/plano/README.md`](docs/plano/README.md).
