# G09 — Nota para o `zywny`: esconder colunas e desenhar a pausa substituta

**Depende de:** G08c · **Decisão necessária:** não

> O `score_bridge` morou no `zywny` (commit `276bdf6`) e hoje mora no
> `zywny-comum` (leia o aviso de G07: os hospedeiros mudaram). Este passo,
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
   Refazer a `libverovio` de **todas** as plataformas que os apps
   empacotam (`just native` e `just native-android` nos apps, que chamam
   `zywny-comum/tool/build_verovio_*.sh`; `build_android_so.sh` aqui; e o
   que houver de wasm/Windows) — sem isso o `.vsb` gerado no aparelho não traz os
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
   `zywny-comum/score_bridge/test/fixtures/sumico/`, como foi feito com
   `fantasma/`.
3. No `zywny-musicas` (onde os planos moram): atualizar
   `docs/plano/L02-esconder-notas.md` e `L03-pausa-substituta.md` (cujo código
   é no `zywny-comum`) onde as medições daqui mudarem um fato
   citado lá (o passo 6 de "Como executar um passo" vale entre os dois
   repositórios).
4. Linha da fase no `README.md` deste plano.

## Critérios de aceite

1. `docs/nota-para-zywny-sumico.md` escrito, cobrindo os 8 itens.
2. Vetores e fixtures copiados; `cd score_bridge && flutter test` no
   `zywny-comum` continua verde com as fixtures novas presentes (ainda sem
   código novo).
3. L02 e L03 do `zywny` coerentes com a §11 final.
4. O usuário avisado de que o trabalho segue no `zywny-comum` (L02 e L03),
   que serve ao zywny-musicas e ao zywny-aprendizado.

## Notas de execução

Concluído em 2026-11-04. Nenhuma linha de `verovio/`, `compare/` ou da spec mudou;
só documentação neste repositório e, nos outros três, fixtures e planos (sem commit em
nenhum, como manda o plano).

- **Critério 1**: `docs/nota-para-zywny-sumico.md` escrita, nos 8 itens da lista. Segue o
  molde de `nota-para-zywny-fantasma.md`; traz também a tabela do formato de
  `vetores.json` (que a fantasma não precisava descrever) e, na seção 1, a lista de
  plataformas da `libverovio`: **Linux** (`just native`), **Android** arm64-v8a + x86_64
  (`just native-android`) e **Web/wasm** (`zywny-comum/tool/build_verovio_web.sh`). Windows,
  macOS e iOS não têm build de `libverovio` no `zywny-comum` (conferi `tool/`, os `justfile`
  dos dois apps e o `windows/` do `zywny-musicas`): lá o Verovio não existe.
- **Critério 2**: copiados para `/home/mauricio/IdeaProjects/zywny-comum/score_bridge/test/fixtures/sumico/`
  os 4 `.vsb` e o `vetores.json` (de `docs/formato/sumico/`). **Além do que o plano pedia**,
  atualizei os 9 `.vsb` de `test/fixtures/fantasma/`: estavam na versão anterior a G08b
  (sem os glifos reservados e sem `dur`/`dots`; `cmp` dava diferente nos 9) e a nota
  prometia "fixtures regeneradas". O `vetores.json` da fantasma já era idêntico. Com tudo
  no lugar, `cd score_bridge && flutter test` no `zywny-comum`: **301 passam, 7 ignorados,
  0 falham** (a suíte inteira, 2 min 25 s; antes das fixtures da fantasma novas deu o
  mesmo; os 3 arquivos da fantasma/corpus rodados em separado depois: 46 passam). O parser
  de `pitchpos.json` ignora `dur`/`dots` sem mudança.
- **Critério 3**: L02, L03 e L00 (zywny-musicas) e T16 (zywny-aprendizado) coerentes com a
  §11 final. O que mudou nelas:
  - **L02 estava errado num ponto que importa**: dizia que `setColor` no id da `note` leva
    a haste junto. Num **acorde** a haste, o colchete e os pontos são filhos do nó `chord`
    (regra 1 da §11). E os hinos **têm** nós `chord` — hino 010: 95 para 425 notas; hino
    056: 70 para 356 — mesmo sem nenhum `<chord/>` no MusicXML (o importador do Verovio
    junta numa `chord` as notas de uma voz que começam juntas; o alto e o tenor do Ex. 1 da
    §11.1 são o acorde `yy2zfkq`). Corrigi o L02 e a linha "sem `<chord/>`" do L00, que
    sugeria o contrário (a coluna típica "são duas notas em camadas diferentes").
  - L02, regra 3: a **pausa deslocada é dona do traço**; `beamSpan` não é `beam`.
  - L03: os pontos são **círculos** (o glifo `E1E7` fica reservado mas não é desenhado), a
    largura do glifo na conta é **truncada**, `dur ≤ 2` (não `≥ 2`), pauta com `n ≠ 5` →
    `null`, o `x` não tem oráculo.
  - L00: os glifos de pausa e `dur`/`dots` "virão" → "vieram" (G08b).
  - T16 (item 3): a frase "o G09 não foi executado" estava velha; agora diz que o bridge
    está pronto e falta o Dart, e inclui a Web na lista de bibliotecas a refazer.
- **Critério 4**: o usuário avisado (resumo da sessão) de que o trabalho segue no
  `zywny-comum` (L02 e L03), que serve ao `zywny-musicas` e ao `zywny-aprendizado`.
- **Sem commit**: as fixtures e as edições de plano ficaram como mudanças soltas nos
  repositórios `zywny-comum`, `zywny-musicas` e `zywny-aprendizado`, e a nota e o README
  neste. O `zywny-musicas` já tinha mudanças soltas em `linux/` e `windows/` (arquivos
  gerados de plugin, `pubspec.lock`): não são desta sessão e não toquei neles.
- **Direitos**: `h010.vsb` e `h056.vsb` (hinos protegidos) foram para as fixtures do
  `zywny-comum` — a mesma biblioteca de onde vieram; o aviso está na nota (seção 8).
