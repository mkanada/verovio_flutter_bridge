# P02 — Geração em runtime: `libverovio` + FFI Dart

**Depende de:** S07 · **Decisão necessária:** SIM (D-RUNTIME)

## Objetivo

Permitir que o app gere o `.vsb` na hora, a partir de um MEI/MusicXML, em vez
de depender de um arquivo pré-gerado — se for isso que o zywny precisa.

## Decisão necessária

Perguntar ao usuário **antes de começar**: o app vai (a) gerar o `.vsb` em
runtime no dispositivo, (b) consumir `.vsb` pré-gerado (servidor/build), ou
(c) os dois? Isso muda o que precisa ser empacotado (a biblioteca nativa
`libverovio.so` + os dados de fonte do Verovio pesam; um `.vsb` pré-gerado não
pesa nada além de si mesmo).

## Ler antes (só isto)

- `../verovio_lottie/docs/plano/E01-bindings-dart-ffi.md` — os bindings Dart FFI
  já foram feitos uma vez lá (build da `libverovio.so`, wrapper C, pacote Dart);
  **reaproveite o caminho**, trocando as funções de Lottie pelas de `.vsb`.
- `verovio/tools/c_wrapper.cpp` L296-L340 (o padrão de wrapper C).
- `../verovio_lottie/verovio_viewer/README.md`, seção "Por que um zip, não
  arquivos crus" — o problema real de empacotar `verovio/data` como asset no
  Flutter (o bundler não recursa em subdiretórios) e a solução já encontrada.

## O que fazer

1. Expor no wrapper C: `vrvToolkit_renderToBridgeFile(void*, const char*)` e
   `vrvToolkit_renderToBridgeJson(void*)`.
2. Build da `libverovio.so` para as plataformas decididas (Linux desktop e
   Android arm64 no mínimo — o `verovio_lottie` tem os diretórios
   `tools/build-android-*` como precedente de que isso já foi tentado).
3. Pacote Dart de binding (FFI) + empacotamento de `verovio/data` (use a
   estratégia do zip do `verovio_viewer`, já validada).
4. Render fora da thread de UI (`Isolate`), porque uma peça grande demora.

## Fora de escopo

- iOS/Windows/macOS, a menos que o usuário peça na decisão acima.
- Cache de `.vsb` gerado (decisão do app, não do pacote).

## Critérios de aceite

1. `flutter run` num app de exemplo abre um `.mei` do corpus, gera o `.vsb` em
   runtime e exibe a partitura.
2. O `.vsb` gerado em runtime é **byte-idêntico** ao gerado pela CLI para a
   mesma entrada e as mesmas opções (é o teste que pega diferença de
   `resourcePath`, de locale e de opções default).
3. A geração roda em isolate: a UI não congela (teste com uma animação rodando
   durante a geração).
4. Tempo de geração registrado por peça, desktop e Android.
5. Tamanho final do app com a biblioteca + dados embutidos, registrado — é o
   número que o usuário vai querer saber ao decidir (a) vs. (b).

## Notas de execução

(a preencher por quem executar)
