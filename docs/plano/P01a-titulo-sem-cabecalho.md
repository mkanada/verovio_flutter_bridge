# P01a — `meta.title` sem depender do cabeçalho desenhado

**Depende de:** — · **Decisão necessária:** **sim — D-META-TITULO** (pare e
pergunte antes de escrever código)

## Objetivo

P01b vai tornar `--header none` o padrão do `.vsb` (D-VSB-PADRAO). Pela regra
atual da spec (§2.3, tabela "Título: o que o cabeçalho renderizado mostra"),
com `--header none` o `meta.title` fica **ausente**. Com isso, o host (`zywny`)
perderia o título que usa para listar a biblioteca. Este passo resolve isso
**antes** de mudar o padrão.

## Decisão necessária — D-META-TITULO

**Com o cabeçalho desligado, de onde vem `meta.title`?**

- **(a) Recomendado: o título que o cabeçalho *mostraria*.** `meta.title` é
  calculado como se `--header` fosse `auto`, sem desenhar nada. Se a peça tem
  cabeçalho codificado (`<pgHead>` do MEI, `<credit>` do MusicXML), usa o
  codificado; senão, gera um `PgHead` temporário com
  `PgHead::GenerateFromMEIHeader(m_doc.m_header)` (o mesmo que
  `Doc::GenerateHeader` faz), passa-o a `BridgeWriter::ExtractMeta` e o
  descarta. O título continua igual ao de hoje com `--header auto` (30/30
  medidos na spec).
- **(b) Ausente**, como a spec diz hoje. O host passa a precisar de outra
  fonte de título.
- **(c) Do `<meiHead>` direto** (`titleStmt/title`), a regra antiga de antes
  de 2026-09-20. Perde as peças MusicXML que só têm `<credit-words>` (4 de 5
  no corpus).

O resto deste arquivo supõe (a). Com (b), o passo se reduz a atualizar a spec
e avisar o `zywny`. Com (c), reescreva "O que fazer".

## Ler antes (só isto)

- `docs/formato/especificacao-v1.md` §2.3 (inteira).
- `verovio/src/toolkit.cpp`: `Toolkit::ReadBridgeMeta` (perto de L2085).
- `verovio/src/bridgewriter.cpp`: `BridgeWriter::ExtractMeta`.
- `verovio/src/doc.cpp`: `Doc::GenerateHeader` (L270) e
  `verovio/src/runningelement.cpp`/`pghead.cpp`: `GenerateFromMEIHeader`.

## Contexto que você precisa (não vá procurar, está aqui)

- Hoje `ReadBridgeMeta` pega `firstPage->GetHeader()`, que devolve `NULL`
  com `--header none`. `ExtractMeta(m_doc.m_header, header)` tira o título do
  `RunningElement` e os autores do `<meiHead>` (os autores **não** dependem
  do cabeçalho).
- `Doc::GenerateHeader` só roda quando o `--header` pede. Com `none`, o
  `scoreDef` não tem `PgHead` gerado. Um `<pgHead>` **codificado** continua
  no `scoreDef` mesmo com `none`, só que não é desenhado.
- Não toque em `View` nem no `SvgDeviceContext`: a mudança fica toda no
  caminho do `meta.json`.

## O que fazer

1. Em `Toolkit::ReadBridgeMeta`: se `firstPage->GetHeader()` não for `NULL`,
   faça como hoje. Senão:
   1. procure no `scoreDef` do primeiro `Score` visível um `PgHead` com
      `func="first"` (codificado) e use-o;
   2. se não houver, crie um `PgHead` local, chame
      `GenerateFromMEIHeader(m_doc.m_header)`, passe-o a `ExtractMeta` e
      destrua-o. Ele nunca é anexado ao documento.
2. Confira que (1.2) não depende de layout: `ExtractMeta` lê a árvore de
   `Rend`/`Text` do cabeçalho, não o desenho. Se depender de algum valor de
   desenho, registre nas notas e pare.
3. Atualize a spec §2.3: o título passa a ser "o que o cabeçalho da página 1
   mostraria com `--header auto`, ou o codificado", **independente de
   `--header`**. Troque a linha `none` da tabela e registre no Histórico de
   revisões.

## Fora de escopo

- Mudar o padrão de `--header` (P01b).
- `creators` (já não depende de `--header`).

## Critérios de aceite

1. Nas 10 peças do corpus, `meta.title` com `--header none` é **igual** ao
   `meta.title` com `--header auto` (tabela nas notas: peça, título `auto`,
   título `none`).
2. Com `--header auto`, `meta.json` é byte-idêntico ao de antes deste passo nas
   10 peças. Com `--header encoded`, idem nas 5 peças MusicXML (já tinham
   `<pgHead>` codificado via `<credit>`); as 5 peças MEI (sem `<pgHead>`
   codificado) ganham `title` — consequência esperada de (a), que calcula o
   título independente do `--header` real (corrigido nas notas: o texto
   original deste critério presumia que nenhuma peça do corpus cairia nesse
   caso).
3. `scene.json`, `glyphs.json` e `-t svg` byte-idênticos nas 10 peças, com
   os três valores de `--header`: o desenho não muda.
4. `score_bridge/test/meta_test.dart` verde (atualize a expectativa do caso
   `none`, se houver) e build do Verovio sem avisos novos.

## Notas de execução

Implementado como descrito: `Toolkit::ReadBridgeMeta` (`verovio/src/toolkit.cpp`)
cai no caminho novo só quando `firstPage->GetHeader()` é `NULL` — procura
`scoreDef->GetPgHead(PGFUNC_first)` codificado e, se não houver, monta um
`PgHead` local com `GenerateFromMEIHeader(m_doc.m_header)`, passa a
`BridgeWriter::ExtractMeta` e descarta (nunca anexado ao `Doc`). `#include
"pghead.h"` adicionado a `toolkit.cpp` (não estava incluído, nem
transitivamente). Build limpo, sem avisos novos.

Medição nas 10 peças do corpus (`--xml-id-seed 42` fixo nas três gerações —
sem seed fixo, `scene.json`/`-t svg` "divergiam" entre builds só por causa dos
`xml:id` sintéticos de `mdiv`/`pageMilestone` sorteados a cada execução, sem
relação com este passo):

| Peça | `title` (auto = none = encoded) |
| --- | --- |
| Chopin Étude Op.10 No.9 (MEI) | Etude in F Minor |
| Chopin Mazurka Op.6 No.1 (MEI) | Mazurka in F-sharp Minor op. 6,1 |
| Grieg Butterfly Op.43 No.1 (MEI) | Butterfly |
| Grieg Little bird Op.43 No.4 (MEI) | Little bird |
| Scarlatti Sonata in C major (MEI) | Suite I |
| Chopin Nocturne Op.9 No.1 (MusicXML) | Trois nocturnes |
| Clair de Lune, Debussy (MusicXML) | Clair de Lune |
| Erik Satie Gymnopédie No.1 (MusicXML) | Gymnopédie No.1 |
| Maple Leaf Rag, Joplin (MusicXML) | Maple Leaf Rag |
| Prelude I BWV 846 (MusicXML) | Prelude I |

Critério 1: 10/10 — confirmado.

Critério 2, com o número real (a tabela acima já mostra por quê): as 5 peças
MEI não têm `<pgHead>` codificado, então **antes** deste passo `--header
encoded` já não desenhava cabeçalho nelas (`Page::GetHeader()` também
`NULL`) e `meta.title` saía ausente. Depois deste passo, o mesmo `NULL` cai no
caminho novo (opção (a) é explícita: "independente de `--header`"), então
`title` passa a existir nessas 5, igual a `auto`. As 5 peças MusicXML batem o
`<credit>` como `<pgHead>` codificado na importação (fora do escopo deste
passo), então já tinham cabeçalho renderizado sob `encoded` e não mudam. O
critério 2 original ("byte-idêntico nas 10 peças" para `auto` e `encoded`) foi
corrigido acima e na spec (§2.3, Histórico de revisões 2026-09-22) para
registrar essa exceção esperada em vez de tratá-la como regressão.

Critério 3: 0 diferenças em `scene.json`, `glyphs.json` e `-t svg` (todas as
páginas) nas 10 peças × 3 valores de `--header`, comparando antes/depois deste
passo — confirma que a mudança fica inteiramente no caminho de `meta.json`.

Critério 4: `flutter test test/meta_test.dart` — 11/11 verdes, sem alterações
(o arquivo não tinha caso `none`; a suíte testa o parser Dart sobre JSON fixo,
não o exportador C++, então nada nela dependia deste comportamento).

`GenerateFromMEIHeader` de fato não toca layout (só monta uma árvore
`Rend`/`Text` a partir do `pugi::xml_document` do cabeçalho) — item 2 do "O
que fazer" confirmado, nada a registrar como bloqueio.
