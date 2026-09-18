# S01 — Fechar a especificação do formato `.vsb`

**Depende de:** F01 · **Decisão necessária:** não (D-NOME resolvida em S01)

## Objetivo

Transformar o rascunho [`docs/formato/especificacao-v1.md`](../formato/especificacao-v1.md)
na versão final que S02-S07 (C++) e R01-R06 (Dart) implementam ao pé da letra,
e produzir um exemplo mínimo validável à mão.

## Decisão registrada (D-NOME)

1. **Nome e extensão do formato:** `.vsb` (**Verovio Score Bridge**).
2. **Flags de CLI:** `-t vsb` para o pacote zip e `-t vsb-json` para o JSON
   único de depuração.
3. **`timemap`:** embutido no pacote quando disponível, conforme confirmado
   pelo usuário. A decisão foi registrada em 2026-09-17 e não há decisão
   pendente neste passo.

## Ler antes (só isto)

- O rascunho inteiro da especificação (é curto e é o objeto deste passo).
- `../verovio_lottie/verovio/src/svgdevicecontext.cpp` `StartPage` L484-L560 —
  a fonte de verdade do `viewBox`, do `color="black"`, do `page-margin` e das
  regras CSS globais que o formato precisa resolver.
- `../verovio_lottie/verovio/src/lottiewriter.cpp` L426-L530 (resolução de
  bold/italic por classe) e L597-L620 (`ComputePageMetrics`).
- `verovio/include/vrv/lottiegeometry.h` — a IR que o formato espelha.

## O que fazer

1. Aplicar a decisão de nome em todo o documento.
2. Conferir, campo a campo, que **todo** dado da IR tem lugar no formato e
   vice-versa. Fazer a tabela de correspondência explícita no documento:
   `LottieShape` → `p`/`r`/`e`, `LottieTextRun` → `t`, `LottieNode` → `g`,
   `LottiePage` → página, e o que S03/S04 acrescentam (`u`, `bbox`).
   Qualquer campo da IR sem destino é um bug do formato — resolva agora.
3. Escrever à mão, no documento, um **exemplo completo mínimo**: uma página com
   um pentagrama, uma clave (uso de glifo), uma nota (grupo com `id`) e um
   título (run de texto). É o *fixture* que R01 usa como primeiro teste de
   parser antes de o exportador existir. Salve-o também em
   `docs/formato/exemplo-minimo.json`.
4. Escrever `docs/formato/schema-v1.json` (JSON Schema draft 2020-12) cobrindo
   o formato. Ele é usado como critério de aceite em S05, S06 e S07.
5. Registrar a decisão e a data no "Histórico de revisões".

## Fora de escopo

- Escrever qualquer código C++ ou Dart.
- Encoding binário (P01a/P01b).

## Critérios de aceite

1. O documento não contém marcadores de conteúdo ou decisão pendentes.
2. `python3 -c "import json,sys;json.load(open('docs/formato/exemplo-minimo.json'))"`
   passa.
3. O exemplo mínimo valida contra o schema:

   ```sh
   pip install check-jsonschema  # se necessário
   check-jsonschema --schemafile docs/formato/schema-v1.json docs/formato/exemplo-minimo.json
   ```

4. A tabela de correspondência IR ↔ formato cobre **todos** os campos de
   `lottiegeometry.h` (confira um a um, o header tem 111 linhas).
5. A decisão D-NOME está registrada na tabela "Decisões pendentes" do
   [`README.md`](README.md) do plano, marcada como resolvida.

## Notas de execução

- 2026-09-17: S01 concluído. Decisão D-NOME registrada: `.vsb`, `-t vsb` e
  `-t vsb-json`; `timemap.json` embutido quando disponível.
- Lidos `CLAUDE.md`, o passo S01, a especificação rascunho, o README do plano,
  `verovio/include/vrv/lottiegeometry.h`, `svgdevicecontext.cpp::StartPage` e
  `lottiewriter.cpp` (CSS por classe e métricas de página) no fork de
  referência; `CLAUDE.md` foi atualizado para registrar D-NOME como resolvida.
- Criados `docs/formato/exemplo-minimo.json` e
  `docs/formato/schema-v1.json` (draft 2020-12).
- Validação executada: `python3 -m json.tool` passou para o exemplo e para o
  schema; `check-jsonschema --schemafile docs/formato/schema-v1.json
  docs/formato/exemplo-minimo.json` passou, assim como as validações isoladas de
  `manifest`, `glyphs`, `scene` e `timemap`.
- A tabela de correspondência cobre os 52 campos declarados em
  `lottiegeometry.h`; nenhum código C++ ou Dart foi escrito.
- 2026-09-17 (correção pós-S04): a auditoria dos passos anteriores, ao revisar
  S04, achou dois desvios entre este documento e a IR que S02-S04 já tinham
  produzido — nenhum deles tinha sido reaberto para atualizar a especificação
  depois que os passos seguintes mudaram a IR, apesar de o cabeçalho do
  documento normativo exigir isso ("uma divergência encontrada durante a
  implementação é resolvida editando este documento primeiro"):
  1. `BridgePage::index` (o índice plano de elementos endereçáveis que S04
     implementou e verificou contra o `timemap`) nunca tinha ganhado uma forma
     em JSON — a linha "S04 | bbox e índice por id" na tabela de §8 era só um
     placeholder de uma linha, nunca expandido. Adicionado `pages[].elements`
     (§5.5 da especificação) + `$defs/indexEntry` no schema + exemplo em
     `exemplo-minimo.json`, validado com `jsonschema` (Draft 2020-12) contra o
     documento único e contra `scene`/`glyphs`/`manifest` isolados.
  2. A tabela de §8 (e três frases soltas em §5) ainda citava os nomes
     `Lottie*` e o caminho `lottiegeometry.h`, que S02 renomeou para `Bridge*`/
     `bridgegeometry.h` — a tabela nunca foi revisitada depois do renome nem
     depois de S03 (uso de glifo, `BridgeChild.glyphUse`/`BridgeGlyphUse`) e S04
     (`BridgeNode.hasBBox`/`bbox`) acrescentarem campos novos à IR, que também
     ficaram sem linha própria. Renomeado em todo o documento e adicionadas as
     linhas que faltavam.
  - Nenhuma mudança de código (C++/Dart) foi feita; é só especificação/schema
    alcançando a IR que S02-S04 já implementaram. Ver a entrada correspondente
    no "Histórico de revisões" da especificação.
