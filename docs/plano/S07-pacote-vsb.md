# S07 — Pacote `.vsb` (zip) com timemap embutido

**Depende de:** S06 · **Decisão necessária:** não (resolvida em S01)

## Objetivo

Empacotar `manifest.json` + `scene.json` + `glyphs.json` + `timemap.json` num
único arquivo `.vsb`, que é o formato que o app consome.

## Ler antes (só isto)

- `verovio/include/vrv/filereader.h` / `verovio/src/filereader.cpp` —
  `ZipFileWriter` (escrito em A11 do projeto anterior) e a nota do risco 5 do
  [README do plano](README.md) sobre `zip_file.hpp` ser header-only.
- `verovio/src/toolkit.cpp` `RenderToTimemap` (busque o símbolo) e
  `include/vrv/timemap.h`.
- Seção 2 da [especificação](../formato/especificacao-v1.md).

## O que fazer

1. `Toolkit::RenderToBridgeFile(const std::string &filename)`:
   - renderiza todas as páginas com o `BridgeDeviceContext`;
   - grava `manifest.json`, `scene.json`, `glyphs.json`;
   - grava `timemap.json` chamando o caminho de timemap já existente. Se a peça
     não produzir timemap (sem informação rítmica utilizável), **omita o arquivo
     e o campo no manifest** — não grave um timemap vazio.
2. `FileFormat::VSB`, `SetOutputTo("vsb")`, entrada em `tools/main.cpp`.
   Pacote binário: recusar `-o -` com mensagem clara (mesmo padrão que o
   `dotlottie` usava).
3. Compressão: use o padrão do `zip_file.hpp` (deflate). Registre nas notas o
   tamanho antes/depois do zip por peça.

## Fora de escopo

- Ler o `.vsb` no Dart (R01 já lê; aqui só se produz).
- Assinatura, versionamento incremental, delta entre versões.

## Critérios de aceite

1. `verovio -t vsb -a --resource-path verovio/data -o saida.vsb peca.mei` gera
   o arquivo para as 10 peças do corpus.
2. `unzip -t saida.vsb` passa em 10/10.
3. `unzip -p saida.vsb scene.json | python3 -m json.tool > /dev/null` e o mesmo
   para `glyphs.json`, `manifest.json`, `timemap.json` — todos válidos.
4. `manifest.json` bate com o conteúdo: `pageCount` igual ao nº de páginas de
   `scene.json`, e `files` lista exatamente os arquivos presentes no zip.
5. Os ids do `timemap.json` embutido são **os mesmos** do `verovio -t timemap`
   rodado separadamente na mesma peça (compare os dois JSONs; devem ser iguais
   módulo formatação).
6. Tabela de tamanhos (por peça: nº de páginas, `scene.json` cru, `glyphs.json`
   cru, `.vsb` final, KB/página) registrada nas notas de execução — é o insumo
   do gate de P01.

## Notas de execução

(a preencher por quem executar)
