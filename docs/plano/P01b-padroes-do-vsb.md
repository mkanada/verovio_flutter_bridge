# P01b — Padrões do `.vsb`: sem cabeçalho, sem rodapé, sem rótulo de instrumento

**Depende de:** P01a · **Decisão necessária:** não (D-VSB-PADRAO, decidida
pelo usuário em 2026-09-22)

## Objetivo

Todo `.vsb` passa a sair, **por padrão**, com `--header none`, `--footer none`
e `--no-instrument-labels`, tanto pela CLI (`-t vsb`, `-t vsb-json`) quanto
pelo FFI que o `zywny` usa (`verovio/bindings/dart`). Quem precisar pode
continuar escolhendo outro valor explicitamente.

## Ler antes (só isto)

- `verovio/src/toolkit.cpp`: `Toolkit::LoadData` (o trecho perto de L830-L860,
  onde `footerOption`/`GenerateFooter` e o cabeçalho são decididos) e
  `Toolkit::SetOutputTo` (L170).
- `verovio/tools/main.cpp`: o `case` de `-t` (L209) e os ramos `vsb`/
  `vsb-json` (L552-L580).
- `verovio/include/vrv/options.h`: `m_header`, `m_footer`,
  `m_noInstrumentLabels`, `m_outputTo`.
- `verovio/bindings/dart/lib/src/verovio_toolkit.dart` (`setOutputTo`,
  `setOptions`, `loadData`) e `verovio/bindings/dart/README.md`.

## Contexto que você precisa (não vá procurar, está aqui)

- As três opções mexem no **layout**, não só no desenho: o cabeçalho e o
  rodapé ocupam altura da página, e o rótulo ocupa largura do sistema. Por
  isso precisam valer **antes** do cast-off, ou seja, antes de `LoadData`.
  Aplicar dentro de `RenderToBridgeFile` exigiria um `RedoLayout` inteiro:
  não faça assim.
- A CLI chama `toolkit.SetOutputTo(optarg)` ao ler `-t`, antes de carregar o
  arquivo. O FFI expõe `setOutputTo` (`vrvToolkit_setOutputTo`,
  `c_wrapper.cpp` L418).
- `Option::IsSet()` é `m_value != m_defaultValue` (`options.cpp` L226). Não
  distingue "não passado" de "passado com o valor padrão". Consequência: com
  a regra abaixo, `--header auto` explícito num `.vsb` **não** religa o
  cabeçalho (use `--header encoded`). Registre isso na ajuda da CLI e no
  README do binding. Se achar um jeito limpo de saber se a opção foi passada
  (sem mexer em `Option` além do mínimo), prefira-o e registre nas notas.
- Página de rodapé hoje: o `pgFoot` gerado é o logo "MEI engraved with
  Verovio" (`data/footer.svg`, `RunningElement::LoadFooter`). O número de
  página "– 2 –" das páginas 2+ vem do `pgHead2` gerado
  (`Doc::GenerateHeader`, `AddPageNum`). Os dois somem com `none`/`none`.

## O que fazer

1. **Um lugar só, no `Toolkit`:** no começo de `Toolkit::LoadData` (antes de
   qualquer decisão de cabeçalho/rodapé/layout), se `m_outputTo` for `VSB` ou
   `VSB_JSON` (`toolkitdef.h` L35-L36), aplique os padrões do bridge a cada
   opção que **não** estiver `IsSet()`:
   - `m_header` = `HEADER_none`;
   - `m_footer` = `FOOTER_none`;
   - `m_noInstrumentLabels` = `true`.

   Escreva isso num método privado pequeno (`ApplyBridgeDefaults()`), com
   comentário citando D-VSB-PADRAO.
2. Confira que `SetOutputTo` com `vsb`/`vsb-json` é aceito por
   `Options::SetOutputTo` (se não for, é a mesma lista que o `main.cpp` usa:
   corrija ali).
3. **CLI:** nada além do `-t` que já existe. Documente os padrões na ajuda
   de `-t vsb`/`vsb-json`.
4. **Binding Dart:** documente no `README.md` do binding e no doc-comment de
   `renderToBridgeFile` que o host precisa chamar `setOutputTo('vsb')`
   **antes** de `loadData`. Acrescente um teste em
   `verovio/bindings/dart/test/` que carrega uma peça com
   `setOutputTo('vsb')` e verifica, no `renderToBridgeJson()`, que não há nó
   de classe `pgHead`, `pgFoot` nem `label`.
5. `-t svg` **não** muda de padrão: continua com cabeçalho, rodapé e rótulo.

## Fora de escopo

- Regenerar o corpus, as fixtures e re-medir a paridade (P01c).
- Páginas alternativas (P02*).

## Critérios de aceite

1. `verovio -t vsb` numa peça do corpus: nenhum nó `pgHead`, `pgFoot` ou
   `label` no `scene.json`. Mostre a contagem antes/depois nas 10 peças
   (`pgFoot` hoje: 8, 6, 14, 0, 4, 6, 4, 6, 4, 6).
2. `verovio -t vsb --header encoded` numa peça com cabeçalho codificado
   desenha o cabeçalho (o padrão pode ser sobrescrito).
3. `verovio -t svg` sem flags: SVG byte-idêntico ao de antes deste passo nas
   10 peças.
4. `meta.json` com o novo padrão é igual ao de `--header auto` antes do passo
   (P01a garante isso; aqui só confirme).
5. Teste do binding verde; build do Verovio sem avisos novos.

## Notas de execução

_(preencher)_
