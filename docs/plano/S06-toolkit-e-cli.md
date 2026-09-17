# S06 — `Toolkit` + CLI (`-t vsb-json`)

**Depende de:** S05 · **Decisão necessária:** depende de D-NOME (resolvida em S01)

## Objetivo

Expor o exportador pela mesma interface que os outros formatos do Verovio, de
modo que `verovio -t vsb-json partitura.mei -o saida.json` produza a cena de
**todas** as páginas.

## Ler antes (só isto)

- `verovio/src/toolkit.cpp` `RenderToDeviceContext` L1674-L1730 (genérico, já
  existe) e, no repositório antigo, `RenderToLottieAnimation`
  (`../verovio_lottie/verovio/src/toolkit.cpp` L1912+) como modelo de laço de
  páginas.
- `verovio/include/vrv/toolkitdef.h` L13-L37 (`FileFormat`).
- `verovio/src/options.cpp` `SetOutputTo` (busque o símbolo; era ~L1987-L2027).
- `verovio/tools/main.cpp` L284-L292 (validação de formato), L312-L315 (a lista
  que força `breaks: none` — **não** inclua o formato novo aí) e L350-L390 (o
  laço de páginas do SVG).

## O que fazer

1. `FileFormat`: acrescentar `VSB_JSON` (e `VSB`, já usado em S07).
2. `Toolkit`:

   ```cpp
   std::string RenderToBridgeJson();                       // todas as páginas
   bool RenderToBridgeJsonFile(const std::string &filename);
   ```

   O laço é: `BridgeDeviceContext dc; dc.SetResources(&m_doc.GetResources());`
   → para cada página `RenderToDeviceContext(p, &dc)` → `BridgeWriter::WriteSingleJson(...)`.
   O dicionário de glifos é **acumulado entre páginas** (uma peça inteira
   compartilha um dicionário só) — confira que o device context não o zera em
   `StartPage`.
3. `SetOutputTo`: aceitar `"vsb-json"`.
4. `tools/main.cpp`: incluir na lista de formatos válidos e na mensagem de erro;
   escrever o arquivo (aceitar `-o -` para stdout, já que é texto).
5. `-a`/`--all-pages` e `-p`/`--page N`: o formato é naturalmente multi-página;
   `-p N` exporta só aquela página (útil para depurar). Espelhe o comportamento
   dos outros formatos, sem inventar semântica nova.

## Fora de escopo

- Pacote zip e timemap (S07).
- Bindings C/FFI (P02).
- Opções de CLI específicas do formato — **não existem**; a animação toda é do
  lado Flutter. Se aparecer vontade de criar uma, pare e pergunte.

## Critérios de aceite

1. `verovio -h` lista `vsb-json` entre os formatos de `--output-to`.
2. Para as 10 peças do corpus:

   ```sh
   ./verovio/tools/verovio -t vsb-json -a --resource-path verovio/data -o compare/out/$n.json $f
   python3 -m json.tool compare/out/$n.json > /dev/null && echo "OK $n"
   ```

   10/10 `OK`, sem crash, sem aviso no stderr.
3. O nº de páginas no JSON bate com `verovio -t svg -a` (conte os `<svg>` de
   página gerados) para todas as peças.
4. `-p 2` produz um JSON com exatamente uma página, cujo conteúdo é igual ao da
   página de índice 1 do export completo (compare os dois sub-objetos).
5. Um dicionário de glifos único para a peça inteira: exportar uma peça de 4+
   páginas e conferir que `glyphs` tem **menos** entradas que a soma dos
   dicionários por página exportados individualmente (prova de compartilhamento).
6. `LC_ALL=tr_TR.UTF-8 verovio -t vsb-json ...` produz saída idêntica (o mesmo
   teste de locale de S05, agora pela CLI).

## Notas de execução

(a preencher por quem executar)
