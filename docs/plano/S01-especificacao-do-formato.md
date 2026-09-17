# S01 — Fechar a especificação do formato `.vsb`

**Depende de:** F01 · **Decisão necessária:** SIM (D-NOME)

## Objetivo

Transformar o rascunho [`docs/formato/especificacao-v1.md`](../formato/especificacao-v1.md)
na versão final que S02-S07 (C++) e R01-R06 (Dart) implementam ao pé da letra,
e produzir um exemplo mínimo validável à mão.

## Decisão necessária (pergunte ao usuário antes de escrever código)

1. **Nome e extensão do formato.** Em uso no plano: `.vsb`
   ("Verovio Score Bridge"), flags `-t vsb` (pacote zip) e `-t vsb-json`
   (JSON único, depuração). Confirme ou troque — depois disso, o nome aparece
   em CLI, `FileFormat`, nomes de classe e no pacote Dart, e trocar fica caro.
2. **`timemap` embutido no pacote?** Recomendação: sim (o host lê um arquivo
   só). Confirmar, porque muda o `manifest.json`.

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
- Encoding binário (P01).

## Critérios de aceite

1. O documento não tem nenhum "(a preencher)" nem "(a decidir)" restante.
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

(a preencher por quem executar)
