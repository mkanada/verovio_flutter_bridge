# P02c — C++: renderizar as sequências alternativas e gravar `alternates.json`

**Depende de:** P02b · **Decisão necessária:** não

## Objetivo

Para cada ponto de chegada de P02b, gerar a sequência alternativa com o
`Select()` do Verovio (D-ALT-MECANISMO) e gravá-la em `alternates.json`
(spec §2.5). As páginas normais, o timemap e o `meta.json` não podem mudar
nem um byte.

## Ler antes (só isto)

- `docs/plano/P00-visao-geral-paginas-alternativas.md`, seções "O que já foi
  provado" e "Exportador (C++)".
- `verovio/src/toolkit.cpp`: `RenderPagesToBridge`, `RenderToBridgeJson`,
  `RenderToBridgeFile`, `Toolkit::Select` (L165) e `Toolkit::RedoLayout`
  (perto de L1640).
- `verovio/src/doc.cpp`: `InitSelectionDoc`, `ResetSelectionDoc`,
  `ReactivateSelection` (L1241-L1370).
- `verovio/src/bridgewriter.cpp`: `WriteScene`, `WriteManifest`,
  `WriteSingleJson`.
- `docs/formato/especificacao-v1.md` §2.5.

## Contexto que você precisa (não vá procurar, está aqui)

- `Select(json)` só marca a seleção como pendente. Ela é aplicada no próximo
  `RedoLayout()`. `Select("{}")` + `RedoLayout()` pede o reset
  (`docselection.cpp`: sem `start`/`end`/`measureRange` = reset). **Confira**
  que depois do reset `GetPageCount()` e o SVG da página 1 voltam
  byte-idênticos: é o critério 3.
- O `BridgeDeviceContext` acumula as páginas em `GetPages()` e o dicionário
  de glifos em `GetGlyphs()`, e o dicionário nunca é zerado entre páginas
  (achado de S06). Renderize as alternativas **no mesmo** DC, **depois** das
  normais, e separe as páginas pelo índice (`pages[0..N)` = normais, o resto
  = alternativas, por sequência). Um glifo que só aparece numa alternativa
  (clave de cortesia, por exemplo) entra no `glyphs.json` compartilhado.
- O timemap (`RenderToTimemap`) usa o `m_midiDoc` expandido, que é
  independente da paginação. Gere-o **antes** das seleções, como hoje.
- O `meta.json` lê `firstPage->GetHeader()`. Leia-o **antes** das seleções,
  para que ele saia do documento normal.
- Custo: cada sequência = um relayout do trecho + o reset (relayout do
  documento inteiro). D-RUNTIME (o `.vsb` é gerado no aparelho) torna esse
  custo relevante. **Meça.**
- `RenderToBridgeJson(from, to)` (o `-t vsb-json` com `-p`) exporta um
  intervalo de páginas. Alternativas só entram quando o intervalo é o
  documento inteiro (`-a`). Registre essa regra na spec, se precisar.

## O que fazer

1. Opção nova `--no-vsb-alternates` (bool, `options.h`/`options.cpp`, grupo
   geral, igual a `noInstrumentLabels` do commit `4663537`) que desliga a
   geração. Serve para os critérios e para depuração. O padrão é gerar.
2. Em `RenderToBridgeFile` (e em `RenderToBridgeJson` quando for o documento
   inteiro), depois das páginas normais, do timemap e do meta:
   1. `starts = pontos de chegada` (P02b);
   2. para cada `T`: `Select({"start": T, "end": <id do último compasso do
      documento>})`, `RedoLayout()`, renderize **todas** as páginas da
      seleção no mesmo `BridgeDeviceContext` e anote o intervalo de páginas
      da sequência `T`;
   3. `Select("{}")` + `RedoLayout()` para devolver o `Doc` ao estado
      normal (o `Toolkit` do FFI pode ser reaproveitado pelo host).
3. `BridgeWriter::WriteAlternates(...)` → `alternates.json` (§2.5), com as
   páginas serializadas exatamente como `WriteScene` faz (reuse o código;
   não duplique a serialização de página). `index` 0-based dentro da
   sequência.
4. Manifest com `files.alternates` quando houver sequências. JSON único com a
   propriedade `alternates`. Omitido quando não houver sequência.
5. Se a sequência de `T` sair com a página 0 **não** começando em `T` (a
   seleção falhou, `LogWarning("Selection could not be made")`), **não**
   grave a sequência e registre um aviso no log. Não aborte o arquivo.

## Fora de escopo

- Referência SVG e paridade das alternativas (P02d).
- Qualquer coisa no Dart.

## Critérios de aceite

1. Para cada peça com repetição: o número de sequências é igual ao de pontos
   de chegada de P02b, e a página 0 de cada sequência tem `start` como
   **primeiro** nó de classe `measure` (verificado por script sobre o
   `alternates.json`).
2. Todo `xml:id` de nota/acorde/pausa/compasso numa página alternativa existe
   nas páginas normais. Dentro de uma sequência, nenhum id se repete.
3. `scene.json`, `timemap.json`, `meta.json` e `manifest` (menos
   `files.alternates`) **byte-idênticos** com e sem `--no-vsb-alternates`
   nas 10 peças. `glyphs.json` com alternativas é um **superconjunto** do sem
   alternativas.
4. Depois do `RenderToBridgeFile`, o mesmo `Toolkit` renderizando `-t svg` da
   página 1 dá SVG byte-idêntico a um `Toolkit` novo: o estado foi
   restaurado (teste com um programa avulso contra a `libverovio.so`, como o
   da sessão de 2026-09-22, ou pelo binding Dart).
5. Tabela nas notas, por peça: páginas normais, sequências, páginas
   alternativas, tamanho do `.vsb` com e sem alternativas, e tempo de
   `RenderToBridgeFile` com e sem (média de 5 execuções, `--release`).
6. Peças sem repetição: nenhum `alternates.json`, `.vsb` byte-idêntico ao de
   P01c.
7. Build sem avisos novos.

## Notas de execução

_(preencher)_
