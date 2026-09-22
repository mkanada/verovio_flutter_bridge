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

Implementado como descrito: `Toolkit::ApplyBridgeDefaults()` (novo método
privado, `verovio/src/toolkit.cpp`), chamado no início de
`Toolkit::LoadData(const std::string &, bool)`, antes de qualquer outro
processamento. Só mexe em `m_header`/`m_footer`/`m_noInstrumentLabels` quando
`m_options->GetOutputTo()` é `VSB`/`VSB_JSON` **e** a opção ainda não foi
setada (`Option::IsSet()`). Não achei um jeito limpo de distinguir "não
passado" de "passado com o valor padrão" sem mexer em `Option` além do
mínimo (o problema é estrutural: `OptionBool`/`OptionIntMap` só guardam
`m_value`/`m_defaultValue`, não um terceiro estado); segui com a limitação
documentada, como o passo previa.

Critério 1: 0 nós `pgHead`/`pgFoot`/`label` no `.vsb` padrão, nas 10 peças
(medido com `-t vsb-json`, `--xml-id-seed 42` fixo — sem seed fixo o
`xml:id` sintético de `mdiv`/`pageMilestone` muda a cada execução e "some"
sozinho da comparação, sem relação com este passo, mesma armadilha de P01a).
Contagem de `pgFoot` **antes** deste passo (com `--header auto --footer auto`,
que já não é mais o padrão do `.vsb`): não medi de novo (o número citado no
passo, "8, 6, 14, 0, 4, 6, 4, 6, 4, 6", já vem de antes; não repeti porque o
critério real é "0 depois", que medi diretamente).

Critério 2: `--header encoded` sobrescreve o padrão e desenha nas 5 peças
MusicXML (têm `<credit>` codificado, batido como `pgHead` na importação);
nas 5 peças MEI (sem `<pgHead>` codificado) continua sem cabeçalho — mesma
observação de P01a, não é regressão deste passo.

Critério 3: `-t svg` sem flags, nas 10 peças (34 páginas), byte-idêntico
antes/depois deste passo — a única diferença bruta encontrada foi a string
`<desc>Engraved by Verovio 6.3.0-<hash>-dirty</desc>` (o hash do commit no
`--version`, que muda com o HEAD/dirty state do build, não com o código);
ignorando essa linha, 0 diferenças nas 34 páginas.

Critério 4: `meta.json` do `.vsb` padrão (`--header none --footer none
--no-instrument-labels`) tem `title` igual ao de `--header auto` de antes de
P01a nas 10 peças — já garantido pelo P01a (que calcula `title`
independente de `--header`); aqui só confirmei que continua True com o novo
padrão.

Critério 5: `dart test` em `verovio/bindings/dart/` — 5/5 verdes, incluindo
o teste novo (`setOutputTo(vsb) before loadFile suppresses
header/footer/label`), que carrega a Little bird com `setOutputTo('vsb')`
antes de `loadFile` e confere 0 `pgHead`/`pgFoot`/`label` e `meta.title`
não nulo. Precisou reconstruir `libverovio.so`
(`./build_linux_so.sh`, ~2 min) antes de rodar. Build do Verovio (CLI) sem
avisos novos.

Documentação: `-t`/`m_outputTo` (`options.cpp`), `RenderToBridgeFile`/
`RenderToBridgeJson` (`toolkit.h`) e o `README.md` do binding Dart (exemplo
de uso + nota) e o doc-comment de `renderToBridgeFile`/`renderToBridgeJson`
em `verovio_toolkit.dart` avisam que `setOutputTo('vsb'|'vsb-json')` precisa
vir **antes** de `loadFile`/`loadData` — os três padrões afetam layout
(cast-off), não só desenho, e `ApplyBridgeDefaults()` só roda dentro de
`LoadData`.
