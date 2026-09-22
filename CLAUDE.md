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
   em **mais de 99,99% dos pixels** (tolerância 128/255 por canal, decisão do
   usuário em 2026-09-19: afrouxa de um lado — ignora diferenças de
   antialiasing — para restringir do outro, 99,9% → 99,99%; mesma
   metodologia do `verovio_lottie`, que media a 32/255).
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
  uso real no app `zywny` mostrar necessidade — **decisão do usuário, não
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
- Encoding binário — só após medição real no `zywny`; decisão do usuário.
- Backend gráfico do Flutter para a comparação (Impeller vs. Skia) — resolvido
  em R05a (2026-09-19) como Impeller, **revisto em 2026-09-20 para Skia**
  (decisão do usuário: o Impeller no Linux não aplica antialiasing). O runner
  do `compare` desliga o Impeller; re-medição do corpus: média 0,008800% Skia ×
  0,008456% Impeller (praticamente igual); ver `compare/README.md`.
- **Geração em runtime no app:** o app **gera o `.vsb` no dispositivo**, via
  FFI com `libverovio.so` (D-RUNTIME, opção (a), decisão do usuário em
  2026-09-20). Consequência: a `libverovio.so` e os dados de `verovio/data`
  (fontes SMuFL e métricas de texto) precisam ser empacotados no app. A
  biblioteca e o wrapper C já existem (`verovio/bindings/dart/`); o
  empacotamento e o isolate ficam no app `zywny`, fora deste repositório.
  Não há app de exemplo neste projeto (decisão do usuário, 2026-09-21): o
  consumidor é o `zywny`.
- **Fase E (repetições), quatro decisões, todas em 2026-09-21/22:**
  - **D-EXPMAP** — como o leitor resolve um id expandido (`-rend<N>`) do
    timemap ao nó da cena: **regra do sufixo**, documentada em
    `docs/formato/especificacao-v1.md` §2.4, sem `expansion.json` à parte
    (0 divergências contra `-t expansionmap` em 14 149 ids do corpus +
    partituras de teste). Implementada em `VsbDocument.sceneIdOf`/`passOf`
    (E02a).
  - **D-EXPAND** — corrigir a geração de expansão no fork: **sim, isolado**
    em `expansionmap.cpp`/`.h` (MEI, E04a) e `iomusxml.cpp` (MusicXML,
    E04b), sem tocar `View`/`DeviceContext`; o desenho continua
    byte-idêntico. Patch pronto para PR upstream em
    `rism-digital/verovio` — enviar ou não é decisão à parte, ainda não
    tomada.
  - **D-SALTO** — o que a vista faz num salto de repetição para outra
    página: **haste generalizada** (`SweepCurtain.targetPageIndex`, E03a),
    a mesma regra de A05b com a página de destino do salto atrás, em vez
    de sempre `A + 1`; sem haste quando o salto é na mesma página.
  - **D-TOQUE** — qual passagem `seekToElement` escolhe num elemento
    repetido: **a mesma passagem da posição atual, senão a 1ª** (`pass:`
    explícito sempre ganha), em `ScorePlayer.seekToElement` (E02c).

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
