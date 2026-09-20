# P02b — Binding FFI Dart, dados empacotados e isolate

**Depende de:** P02a (decisão (a) ou (c)) · **Decisão necessária:** não

## Objetivo

Fazer o app abrir um MEI/MusicXML e exibir a partitura sem passar por
servidor: binding FFI, dados do Verovio empacotados como asset, e a geração
rodando fora da thread de UI.

## Ler antes (só isto)

- `../verovio_lottie/docs/plano/E01-bindings-dart-ffi.md`.
- `../verovio_lottie/verovio_viewer/README.md`, seção "Por que um zip, não
  arquivos crus".
- Notas de execução de P02a (símbolos expostos, tamanho da biblioteca).

## Contexto que você precisa (não vá procurar, está aqui)

- **Assets em subdiretório**: o bundler do Flutter não recursa; `verovio/data`
  tem vários níveis. A solução já validada é empacotar um zip único e
  extraí-lo no diretório de documentos do app na primeira execução,
  apontando `--resource-path` para lá.
- **Isolate**: a geração de uma peça grande leva centenas de ms a segundos.
  Rodar na thread de UI congela a animação. Um `Isolate.run` com a chamada FFI
  dentro resolve, mas **ponteiros nativos não atravessam isolates** — o
  isolate precisa abrir a própria instância do `Toolkit` (ou use
  `NativeCallable`/`Isolate.spawn` com carga de dados por caminho de arquivo,
  que é mais simples e suficiente aqui).
- **Byte-identidade CLI × FFI** só é verificável em peça com `xml:id`
  explícito no MEI (ids auto-gerados variam entre processos — nota de S04). Se
  a peça escolhida tiver ids gerados, compare ignorando os ids, e registre a
  limitação.
- Tamanho do app é o número que o usuário vai querer: biblioteca + dados +
  fontes. Meça o APK/bundle com e sem a geração em runtime, para a decisão
  (a) × (b) ficar quantificada mesmo depois de tomada. Números já medidos em
  P02a: `.so` com strip **17,0 MB** (Linux x86_64) e **18,5 MB**
  (Android arm64-v8a).
- **O passo 1 ("pacote Dart de binding") já está feito**: P02a entregou
  `verovio/bindings/dart` funcionando (`VerovioToolkit.renderToBridgeFile` /
  `renderToBridgeJson`, `dart test` 4/4 contra a `.so`). O que resta aqui é o
  empacotamento dos dados, o isolate e o app de demonstração.
- **`verovio/data` é menor do que parece**: 4,0 MB de conteúdo em 2 685
  arquivos (os 14 MB que `du -sh` mostra são bloco de disco, não bytes). Se o
  app não trocar de fonte musical, o obrigatório é Bravura + Leipzig +
  `data/text` = **2,3 MB** em 1 553 arquivos (`Resources::InitFonts`,
  `src/resources.cpp` L61, carrega os três sem opção). O diretório precisa ser
  um caminho de arquivo real: `Resources` só aceita `SetPath`, não há API de
  carregar o diretório de dados de memória — daí a extração na primeira
  execução.
- **Critério 2 (byte-identidade) já foi medido uma vez em P02a**, com Grieg e
  `resetXmlIdSeed(42)` casando o `-x 42` da CLI: `scene.json`, `glyphs.json` e
  `timemap.json` saíram **byte-idênticos**. O `manifest.json` **sempre** vai
  diferir no campo `generator` quando a CLI e a `.so` forem construídas de
  commits diferentes (o hash do commit é compilado no binário) — não conte
  isso como falha do critério; compare os dois binários do mesmo commit ou
  ignore o campo.

## O que fazer

1. Pacote Dart de binding (FFI) sobre os símbolos de P02a, com a mesma
   convenção de vida útil de string documentada lá.
2. Empacotamento de `verovio/data` (zip + extração na primeira execução) e
   configuração do `resourcePath`.
3. Geração em isolate, com `Future` e progresso simples (pelo menos
   "começou/terminou").
4. App de demonstração mínimo (pode ser o `example/` que P03b vai crescer):
   abrir um `.mei` do corpus, gerar, exibir.

## Fora de escopo

- Cache de `.vsb` gerado (decisão do app, não do pacote).
- iOS/Windows/macOS.

## Critérios de aceite

1. `flutter run` num app de exemplo abre um `.mei` do corpus, gera o `.vsb` em
   runtime e exibe a partitura — em Linux desktop **e** Android.
2. O `.vsb` gerado em runtime é **byte-idêntico** ao gerado pela CLI para a
   mesma entrada e as mesmas opções (peça com `xml:id` explícito). Se a peça
   tiver ids gerados, a comparação ignora ids e a limitação está registrada.
   Este critério é o que pega diferença de `resourcePath`, de locale e de
   opções default.
3. A UI não congela durante a geração: uma animação em curso continua fluida
   (teste com um indicador animado; registre o resultado).
4. Tempo de geração por peça registrado, desktop e Android.
5. Tamanho final do app com biblioteca + dados embutidos, registrado, e
   comparado com o tamanho sem eles.
6. `flutter analyze` limpo.

## Notas de execução

(a preencher por quem executar)
