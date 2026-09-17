# CLAUDE.md

Guia para trabalhar no `verovio_flutter_bridge`. O plano executável está em
[`docs/plano/README.md`](docs/plano/README.md) — leia o `README.md` do plano e
o arquivo do passo que for executar. O histórico do que já foi provado (e do
que falhou) no projeto anterior está em
[`docs/licoes-do-verovio-lottie.md`](docs/licoes-do-verovio-lottie.md).

## O que é este projeto

Fork do Verovio que exporta um **formato intermediário de cena** (`.vsb`),
lido por um **pacote Flutter** que desenha a partitura com `CustomPaint` e
anima/colore notas individualmente, endereçadas por `xml:id`.

Requisitos herdados do projeto anterior, inegociáveis:

1. **Paridade visual** — o render do Flutter deve bater com o SVG do Verovio
   em **mais de 99,9% dos pixels** (tolerância 32/255 por canal, mesma
   metodologia do `verovio_lottie`).
2. **Animação individual por nota** — N notas acesas ao mesmo tempo, cada uma
   com sua curva/fade, sem agrupamento forçado por instante.
3. **Controle de cor individual** por `xml:id`, em runtime, pelo host.
4. Virada de página e overlays posicionados sobre elementos.

## Decisões arquiteturais já tomadas

Trate como fixas — não reabra sem confirmar com o usuário:

- **Exportador nativo em C++ dentro do Verovio**, alimentado pelo mesmo `View`
  que desenha o SVG (é isso que garante a paridade). Nada de pós-processar SVG.
- **Base do repositório: cópia do fork já validado** do `verovio_lottie`
  (`LottieDeviceContext` → `BridgeDeviceContext`, IR de cena, `svgpathparser`,
  `ZipFileWriter`, `DrawSvgShape`, texto comum, rotação). O código Lottie
  específico (writer, state machine, highlight, page turn) é **removido**.
- **Identificadores = `xml:id`** — os mesmos que aparecem no `timemap`. Não
  invente esquema de IDs paralelo.
- **Glifos SMuFL: dicionário de contornos + metadados de codepoint** — cada
  glifo usado aparece uma vez no arquivo (contorno em unidades de fonte) e cada
  ocorrência é uma referência `{glyphId, x, y, sx, sy}`, equivalente ao `<use>`
  do SVG. O formato **também** carrega `font`/`codepoint`/`unitsPerEm` de cada
  glifo, permitindo um segundo caminho de render por TTF no Flutter no futuro
  (decisão do usuário: carregar os dois; o caminho de contorno é o canônico e
  o único que precisa bater a paridade).
- **Encoding: JSON** (compacto, chaves legíveis, geometria em arrays planos de
  números), empacotado em zip no formato `.vsb`. Encoding binário só entra se o
  passo de medição (P01) mostrar necessidade real — **decisão do usuário, não
  decida sozinho**.
- **Render no Flutter: `CustomPaint` em camadas** — conteúdo estático da página
  compilado uma vez em `ui.Picture` e reusado; elementos endereçáveis (notas)
  numa camada separada que repinta só quando uma cor muda. Widgets reais
  (`Positioned`) entram **por cima**, opcionalmente, via bbox exportada — nunca
  um widget por path.
- **Coordenadas do formato = unidades de viewBox do Verovio** (o que o
  `DeviceContext` recebe; `DEFINITION_FACTOR = 10`), com a transformação de
  ajuste página→pixels pré-computada no arquivo (`fit`), reproduzindo
  `preserveAspectRatio="xMidYMid meet"` do `<svg class="definition-scale">`.
- **Cor por herança, como no SVG** — nós carregam `color` opcional, formas com
  `fill`/`stroke` ausentes herdam do ancestral mais próximo. É isso que faz
  "pintar a nota inteira de vermelho" ser uma troca de uma cor só, em runtime.
- **Estilo resolvido na exportação** — as regras CSS por classe que o SVG usa
  (`g.tempo{bold}`, `g.dir,g.dynam,g.mNum{italic}`, `g.label{normal}`,
  `path,rect,...{stroke:currentColor}`) são resolvidas pelo exportador; o
  formato carrega o resultado final, o Flutter não interpreta CSS.
- **Critério de correção é visual**, por diff de PNG contra o SVG renderizado
  pelo `resvg` — nunca comparação estrutural de JSON.
- **Timemap embutido no pacote** `.vsb` (o Verovio já sabe gerá-lo), para o
  host não precisar cruzar dois arquivos.

## Decisões registradas e itens abertos

- **Nome final do formato/extensão e flags de CLI:** `.vsb` (**Verovio Score
  Bridge**), `-t vsb` para o pacote zip e `-t vsb-json` para o JSON único;
  resolvido em S01 em 2026-09-17.
- Encoding binário (P01) — só após medição real.
- Backend gráfico do Flutter para a comparação (Impeller vs. Skia) — decidido
  por medição em R05, registre o resultado.
- Estratégia de geração em runtime no app (FFI com `libverovio.so` vs. `.vsb`
  pré-gerado no servidor) — ver P02.

## Convenções de trabalho

- Código do exportador vive em `verovio/src` e `verovio/include`, seguindo as
  convenções do Verovio (classes `Io*`/`*DeviceContext`, cabeçalho de arquivo,
  separadores `//----`, `.clang-format` do próprio fork).
- **Não altere** `SvgDeviceContext`, `BBoxDeviceContext` nem as classes `View`:
  o exportador é só mais um `DeviceContext` alimentado pelo mesmo `View`.
- Build do Verovio: `cd verovio/tools && cmake ../cmake && make -j4`. Rode
  `cmake ../cmake` de novo sempre que criar um `.cpp` (o CMake coleta por glob).
- Saídas temporárias de teste vão em `compare/out/` (git-ignorado). Nunca em
  `verovio/`.
- Paridade incremental: caso simples antes de complexo; cada passo mede antes
  de seguir.
- Não faça commit nem push sem o usuário pedir.
