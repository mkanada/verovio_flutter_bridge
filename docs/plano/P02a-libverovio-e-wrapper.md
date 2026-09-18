# P02a — Decisão D-RUNTIME, `libverovio` e wrapper C

**Depende de:** S07 · **Decisão necessária:** SIM (D-RUNTIME)

## Objetivo

Decidir se o app precisa gerar `.vsb` no aparelho e, se precisar, produzir a
biblioteca nativa com as funções do bridge expostas em C. O binding Dart e o
empacotamento ficam em P02b.

## Decisão necessária

Perguntar **antes de começar**: o app vai (a) gerar o `.vsb` em runtime no
dispositivo, (b) consumir `.vsb` pré-gerado (servidor/build), ou (c) os dois?
Isso muda o que precisa ser empacotado — a `libverovio.so` mais os dados de
fonte do Verovio pesam; um `.vsb` pré-gerado não pesa nada além de si mesmo.
Se a resposta for (b), **este passo e o P02b não são executados** — registre
a decisão e siga.

## Ler antes (só isto)

- `../verovio_lottie/docs/plano/E01-bindings-dart-ffi.md` — o caminho já foi
  percorrido uma vez (build da `.so`, wrapper C, pacote Dart). Reaproveite,
  trocando as funções Lottie pelas de `.vsb`.
- `verovio/tools/c_wrapper.cpp` L296-L340 (o padrão de wrapper C do projeto).
- `verovio/src/toolkit.cpp`, as funções de saída `.vsb` (S06/S07).

## Contexto que você precisa (não vá procurar, está aqui)

- O `Toolkit` já expõe a geração de `.vsb` (S06/S07); o wrapper C é uma casca
  fina sobre ela, no mesmo estilo das funções já existentes.
- `verovio/data` é obrigatório em runtime (`--resource-path`): são as fontes
  SMuFL e as métricas de texto. Empacotar isso num app Flutter tem uma
  armadilha conhecida — o bundler **não recursa** em subdiretórios de assets;
  o `verovio_lottie` resolveu com um zip único (ver
  `../verovio_lottie/verovio_viewer/README.md`, "Por que um zip, não arquivos
  crus"). Isso é P02b, mas decida o formato aqui, porque muda o wrapper.
- O `verovio_lottie` tem `tools/build-android-*` como precedente de build
  Android — confira antes de inventar.
- **`xml:id` auto-gerado não é determinístico entre processos** (nota de
  S04). Isso afeta diretamente o critério de "byte-idêntico ao da CLI": só
  vale para peças cujos elementos têm `xml:id` explícito no MEI, ou
  comparando o **mesmo processo**. Escolha o caso de teste com isso em mente e
  registre.

## O que fazer

1. Fazer a pergunta ao usuário e registrar a resposta com data (README do
   plano + `CLAUDE.md`).
2. Expor no wrapper C:

   ```c
   bool vrvToolkit_renderToBridgeFile(void *tk, const char *path);
   const char *vrvToolkit_renderToBridgeJson(void *tk);
   ```

   Seguindo exatamente o padrão de vida útil de string do wrapper existente
   (buffer interno reutilizado — documente).
3. Build da `libverovio.so` para as plataformas decididas (Linux desktop e
   Android arm64 no mínimo), com o comando registrado nas notas.
4. Teste de fumaça nativo: gerar um `.vsb` pela biblioteca, fora do Flutter,
   e abri-lo com o parser Dart (ou com Python) para confirmar que é válido.

## Fora de escopo

- Binding Dart, isolate e empacotamento de dados (P02b).
- iOS/Windows/macOS, a menos que o usuário peça na decisão.

## Critérios de aceite

1. A decisão D-RUNTIME está registrada, com data, no README do plano e no
   `CLAUDE.md`. Se for (b), o passo termina aqui.
2. `libverovio.so` compila para Linux desktop e Android arm64; comandos nas
   notas.
3. As duas funções novas aparecem nos símbolos exportados
   (`nm -D libverovio.so | grep Bridge`).
4. Teste de fumaça: `.vsb` gerado pela biblioteca abre no parser sem erro e
   tem o mesmo número de páginas que o gerado pela CLI.
5. Tamanho da biblioteca por plataforma registrado — é insumo da conta de
   tamanho do app em P02b.

## Notas de execução

(a preencher por quem executar)
