# G09 — Nota para o `zywny`: esconder colunas e desenhar a pausa substituta

**Depende de:** G08c · **Decisão necessária:** não

> O `score_bridge` mora no `zywny` desde o commit `276bdf6`. Este passo,
> **neste repositório**, só escreve `docs/nota-para-zywny-sumico.md` (no
> molde de `nota-para-zywny-fantasma.md`) e copia vetores e fixtures; a
> execução é no plano do host (L02 e L03 de lá).

## Objetivo

Entregar ao `zywny` tudo o que ele precisa para implementar o lado Dart da
trilha do decorar sem reabrir decisões nem refazer medições.

## Ler antes (só isto)

- [`G07`](G07-visao-geral-nota-escondida.md) inteiro e as notas de
  execução de G08a-G08c.
- `docs/nota-para-zywny-fantasma.md` (molde).
- `docs/formato/especificacao-v1.md` §2.8, §4, §11.
- No `zywny`: `docs/plano/L00-trilha-do-decorar.md`,
  `L02-esconder-notas.md`, `L03-pausa-substituta.md` (o que o host espera
  receber).

## O que a nota deve cobrir

1. **O que mudou no `.vsb`** (tudo aditivo, `version` 1): 8 glifos
   reservados novos; `dur`/`dots` em `pitchpos.json`. Regenerar fixtures.
   Refazer a `libverovio` de **todas** as plataformas que o `zywny`
   empacota (`just native` no Linux, `build_android_so.sh`, e o que houver
   de wasm/Windows) — sem isso o `.vsb` gerado no aparelho não traz os
   glifos e a coluna some sem pausa.
2. **Conferir no que existe**: o parser de `pitchpos.json` ignora ou lê os
   campos novos sem quebrar; testes existentes verdes com as fixtures
   novas; a nota fantasma (§10) inalterada.
3. **Modelo/parser** (sugestão): `PitchPosEvent.dur`/`dots` (`int?`,
   `int`).
4. **Esconder** (§11, regras 1-3): API sugerida — `setHidden(Set<String>
   noteIds)`, `reveal(id)`, `clearHidden()`; o conjunto de formas de barra
   e de traços a apagar é **derivado** do conjunto de notas, pela regra,
   nunca passado pelo chamador. Validado contra
   `docs/formato/sumico/vetores.json`. Custo de recompilar `Picture`
   (as formas da barra e dos traços estão em segmentos estáticos): medir.
5. **Pausa substituta** (§11, regras 4-7): `standInFor(noteIds)` → glifo,
   posição, escala, pontos; camada de overlay no molde da fantasma, com
   cor de repouso e "piscar" por coluna. Mesmos vetores, tolerância 0,5.
6. **O que é do host e não do formato**: quais colunas somem (o sorteio),
   a cor, o piscar, revelar no erro, a prova às cegas.
7. **Números úteis**: os medidos em G08b/G08c (tamanho, contagens das
   varreduras, casos de barra aninhada/cross-staff/tremolo e o que a regra
   faz com eles).
8. Limitações aceitas da v1 (G07) e, se o plano B de D-SUM-NATIVO entrou,
   o campo novo do traço e como usá-lo.

## O que fazer

1. Escrever `docs/nota-para-zywny-sumico.md`.
2. Copiar `docs/formato/sumico/` (vetores e `.vsb`) para
   `zywny/score_bridge/test/fixtures/sumico/`, como foi feito com
   `fantasma/`.
3. No `zywny`: atualizar `docs/plano/L02-esconder-notas.md` e
   `L03-pausa-substituta.md` onde as medições daqui mudarem um fato
   citado lá (o passo 6 de "Como executar um passo" vale entre os dois
   repositórios).
4. Linha da fase no `README.md` deste plano.

## Critérios de aceite

1. `docs/nota-para-zywny-sumico.md` escrito, cobrindo os 8 itens.
2. Vetores e fixtures copiados; `cd score_bridge && flutter test` no
   `zywny` continua verde com as fixtures novas presentes (ainda sem
   código novo).
3. L02 e L03 do `zywny` coerentes com a §11 final.
4. O usuário avisado de que o trabalho segue no `zywny`.

## Notas de execução

_(preencher ao executar)_
