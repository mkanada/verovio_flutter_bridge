# Lições do `verovio_lottie` — o que foi provado e o que travou

Este documento existe para que ninguém reabra caminhos já percorridos. O
projeto anterior fica em `../verovio_lottie` (repositório git próprio, último
commit `f6269a0`, 2026-09-16) e continua consultável.

## O que o projeto anterior provou que funciona

Tudo isto é **reaproveitado** aqui (ver F01) e não precisa ser redescoberto:

| Fato provado | Onde |
| --- | --- |
| Um `DeviceContext` alimentado pelo mesmo `View` do SVG produz geometria equivalente à do SVG | `verovio/src/lottiedevicecontext.cpp` (980 linhas) |
| IR de cena (grupos com `xml:id`/classe/cor, formas, runs de texto, rotação) | `verovio/include/vrv/lottiegeometry.h` |
| Parser dos paths dos glifos SMuFL (`M c h l s v z`, `transform="scale(1,-1)"`) | `verovio/src/svgpathparser.cpp` (429 linhas) |
| Aritmética de avanço de glifo idêntica à do SVG (inteira, não float) | `LottieDeviceContext::GetGlyphAdvance` |
| `DrawSvgShape` (SVG embutido no MEI, inclui o rodapé "MEI engraved with Verovio") | passo D02 |
| Rotação (`RotateGraphic`): sinal e pivô confirmados | passo D04 |
| Casos de borda de estilo (opacidade, tracejado, visibilidade, cue) | passo D05 |
| Regras CSS por classe resolvidas na exportação (bold/italic por `g.tempo`, `g.dir`, `g.label`…) | `verovio/src/lottiewriter.cpp` L426-L530 |
| Texto comum em 4 estilos (Regular/Italic/Bold/BoldItalic), Liberation Serif | passos D01, D01-5 |
| Run de texto cujos caracteres são códigos SMuFL deve virar vetor, não texto | passo D01-6 |
| `resvg` (não `flutter_svg`/Impeller) é o renderizador de referência confiável para o SVG | `compare/README.md` |
| Escrita de zip dentro do Verovio (`ZipFileWriter`, miniz do `zip_file.hpp`) | passo A11 |
| Paridade final medida no corpus: **0,0135% – 0,3946%, média 0,1251%** de pixels divergentes (tolerância 32/255) | `docs/plano/README.md`, linha do D01-6 |

## O que travou — e por que some aqui

Cinco limites, todos do **runtime dotLottie/Lottie**, nenhum do Verovio:

1. **Playhead único.** `PlaybackState`+`segment` só mantém um estado ativo por
   engine, então só uma nota (ou um grupo) fica destacada por vez. A saída foi
   agrupar notas do mesmo instante do `timemap` (mecanismo "M2"), aceitando que
   vozes com onsets diferentes se cancelassem.
   → No Flutter cada nota tem seu próprio `Animation`/valor de cor; não existe
   playhead compartilhado.

2. **Modos mutuamente exclusivos.** Slots de cor (`set_color_slot`, mecanismo
   "M3") acendem N notas ao mesmo tempo, mas **sem fade**; M2 tem fade mas é um
   por vez. O protocolo de handoff entre os dois nunca chegou a ser desenhado.
   → No Flutter os dois casos são o mesmo código: um `ValueNotifier<Color>` por
   `xml:id`, animado ou setado direto.

3. **Dois engines não compositáveis.** A virada de página precisou de uma
   segunda instância de `Player` (B01 provou que dividir engine com o destaque
   faz a virada cancelar o fade). O `dotlottie-rs` não expõe a posição/transform
   de camada de uma instância para compositar na outra (`get_layer_obb` vive
   atrás de `renderer: pub(crate)`) — risco aberto até o fim.
   → No Flutter virar página é transição de widget; não há engine para dividir.

4. **Bug de renderização no runtime oficial.** Todo texto em itálico saía com
   inclinação dupla (itálico sintético aplicado sobre fonte já itálica). A
   correção exigiu **vendorizar e corrigir o ThorVG** localmente; os players
   oficiais continuam errados (D01-4, seção "Pendências").
   → O Flutter é o renderizador e não tem esse bug.

5. **Tamanho × cor por nota.** Sem `<use>`, cada glifo era "assado" em cada
   ocorrência; embutir as 4 fontes custava ~600-870 KB fixos por peça. A
   otimização óbvia (precomp compartilhado) é **incompatível** com slot de cor
   por nota: o `sid` do slot vive dentro do asset compartilhado, então mudar a
   cor de uma nota mudaria a de todas. O passo D06 ficou bloqueado nisso.
   → Aqui o dicionário de glifos guarda **só geometria**; a cor é da instância,
   resolvida por herança no painter. Reuso total e cor por nota convivem.

## O que muda de premissa

- **Fonte embutida deixa de ser obrigatória no arquivo.** O Flutter carrega as
  TTFs Liberation/SMuFL como assets do app; o `.vsb` não precisa carregá-las.
- **O formato não precisa descrever animação.** Ele descreve *cena estática +
  identidade dos elementos*. Toda a animação é responsabilidade do Flutter.
- **A state machine some inteira.** Não há `s/*.json`, `inputs`, `guards`,
  `GlobalState`, `markers`, `frames`. O host chama métodos Dart.
