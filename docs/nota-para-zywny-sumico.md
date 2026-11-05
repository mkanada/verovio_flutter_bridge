# Nota para o `zywny` — nota escondida e pausa substituta (fase G, G07-G09)

Fechada em 2026-11-04 no lado deste repositório (formato, exportador,
referência e vetores). **Acréscimo G11 (2026-11-05): esconder um compasso inteiro
com a pausa de compasso; ver a seção 9, que pede refazer a `libverovio` de novo.** **Toda a execução Dart é no `zywny-comum`**
(`score_bridge/`), nos passos **L02** (esconder) e **L03** (pausa
substituta) do plano do `zywny-musicas`; o mesmo `score_bridge` serve ao
decorar do `zywny-musicas` e ao treino "Notas escondidas" (T16) do
`zywny-aprendizado`. Nada específico de um app entra nele.

As decisões estão em
[`docs/plano/G07-visao-geral-nota-escondida.md`](plano/G07-visao-geral-nota-escondida.md)
(D-SUM-*); o contrato normativo é a **§11** de
[`docs/formato/especificacao-v1.md`](formato/especificacao-v1.md) (com a §2.8,
`pitchpos.json`, e a §4, glifos reservados). Esta nota diz o que mudou, o que
conferir, como portar e o que **não** é do formato.

## 1. O que mudou no `.vsb`

Tudo aditivo (`version` continua `1`; um leitor antigo ignora):

| O quê | Onde | Para quê |
| --- | --- | --- |
| `dur` e `dots` em `pitchpos.json` | §2.8 | a **figura escrita** de cada nota e pausa (`dur` 1, 2, 4, … 1024; `dots` só se > 0). Ausente em `mRest`/`multiRest`, em nota sem `@dur` na fonte (2 apojaturas do Scarlatti, no corpus) e fora de 1..1024 (breve, longa, máxima) |
| 8 glifos reservados novos | §4 | `E4E3`…`E4E9` (pausas de semibreve a semifusa) e `E1E7` (ponto de aumento) sempre no `glyphs.json`, mesmo sem uso — 16 reservados no total, chave `"<fonte>:<codepoint>"` (`Leipzig:E4E5`) |
| §11 (nova) | especificação | a regra normativa: esconder a nota, a barra, as linhas suplementares; a pausa substituta (figura, glifo, posição, pontos) |

Nada muda no desenho: `scene.json`, `alternates.json`, `timemap.json`,
`midi.json` e `meta.json` são byte-idênticos aos de antes de G08b nas 36 peças
medidas; o `.mid` e o timemap avulsos também. D-SUM-NATIVO foi resolvida em
G08c com **sem dado novo na cena** — o plano B (gravar no traço os ids de
`Dash::m_events`) não foi preciso e **não existe** campo de traço no formato.

**Regenerar as fixtures** (`.vsb` do corpus e de teste) com o binário novo.
Custo medido nas 36 peças (JSON não comprimido): `glyphs.json` +2,5 a +4,8 KB
por peça (+127 849 bytes no total; cada um dos 8 pesa de 252 B, o ponto, a
1 364 B, a pausa de semifusa); `pitchpos.json` +10% (~9 bytes por evento,
+102 720 bytes no total); tempo de geração inalterado (6,41 s → 6,31 s, ruído).
Os dois hinos: `h010.vsb` 116 KB (`pitchpos.json` 35 KB, `glyphs.json` 25 KB),
`h056.vsb` 119 KB (30 KB e 26 KB), já com `alternates.json`.

**Refazer a `libverovio` de TODAS as plataformas que os apps empacotam.** O
`.vsb` é gerado no aparelho; sem a lib nova ele sai sem os glifos de pausa e
sem `dur`/`dots`, e a coluna some **sem pausa** (é o comportamento
previsto, mas não é o que se quer entregar). Os scripts moram no
`zywny-comum/tool/`, nenhum precisa de mudança:

| Plataforma | Comando (de dentro de um app) | Script |
| --- | --- | --- |
| Linux | `just native` | `tool/build_verovio_linux.sh` → `build_linux_so.sh` (aqui, `verovio/bindings/dart/`) |
| Android (arm64-v8a + x86_64) | `just native-android` | `tool/build_verovio_android.sh` → `build_android_so.sh` |
| Web (wasm) | `tool/build_verovio_web.sh` (Emscripten; a 1ª compilação leva ~10 min) | `verovio/bindings/js/build_wasm.sh` |

Windows, macOS e iOS não têm script de `libverovio` no `zywny-comum` (e o
`zywny-musicas/windows` não a empacota): lá o Verovio não existe, então não há
`.vsb` gerado no aparelho. Se um dia houver, a lib vem de `verovio/` deste
repositório e tem de ser de depois de `6aa532d` (G08b).

## 2. Conferir no que já existe

Feito neste passo, no `zywny-comum` (ainda sem código novo):

- O parser de `pitchpos.json` (`score_bridge/lib/src/parser.dart`,
  `_parsePitchEvent`) lê só os campos que conhece e **ignora** `dur`/`dots`: as
  fixtures novas passam sem mudança.
- `cd score_bridge && flutter test`, com `test/fixtures/sumico/` presente e as
  fixtures de `test/fixtures/fantasma/` **atualizadas** (os 9 `.vsb` de lá
  também mudaram em G08b — ganharam os glifos e `dur`/`dots`; o
  `vetores.json` da fantasma é idêntico): verde (ver "Notas de execução" em
  G09 para os números).
- A nota fantasma (§10) é inalterada: 32 casos e 2 400 alvos de G04d/G06
  continuam com 0 divergências na referência Python
  (`ghost_ref.py --self-test`, `ghost_oracle.py`).

## 3. Modelo e parser (sugestão)

- `PitchEvent.dur` (`int?`) e `PitchEvent.dots` (`int`, 0 se ausente), nos
  dois tipos de evento (`n` e `r`). Ausente → `null`/0, nunca erro: um `.vsb`
  de antes de G08b não tem o campo.
- O resto do que a §11 pede já existe: `StaffGeometry` (`lines`, `gs`),
  `staffRef`, o índice por página de `ghost.dart` (como achar o `staff`, o
  `notehead` e os `u` de uma nota — reaproveite) e `VsbDocument.sceneIdOf`
  (id expandido `-rend<N>` → id da cena).
- O contorno do glifo vem de `glyphs.json` (chave `"<fonte>:<codepoint>"`); a
  largura de cabeça usada nas regras 3 e 6 é o intervalo horizontal dos
  vértices (`v`) do contorno × `sx` da instância, a mesma medida da §10 passo 7.
  A largura **do glifo da pausa** nos pontos usa `bbox[2] / 10 × sx` (§4),
  **truncada** (`⌊·⌋`): o Verovio calcula em inteiros.

## 4. Esconder (§11, regras 1-3) — L02

API sugerida (no `ScoreController` ou num controlador irmão; uma notificação
por chamada, como o resto): `setHidden(Set<String> noteIds)`, `reveal(id)`,
`clearHidden()`, `isHidden(id)`. **O chamador passa só notas**: as formas da
barra e os traços a apagar são derivados do conjunto `H` (todas as notas
escondidas) pela regra — nunca recebidos de fora.

Resumo do que a referência
([`compare/scripts/hide_ref.py`](../compare/scripts/hide_ref.py), `hidden_shapes`;
335 linhas, leia-a junto com a §11) calcula:

1. **Notas**: cada nota de `H` vira transparente (cor herdada, §6): cabeça,
   haste própria, colchete, acidente, articulação e pontos vão junto. A
   `verse` (letra) fica — `kOverrideExemptClasses`.
   - **Acorde.** A haste, o colchete e os pontos de um acorde são filhos do
     nó `chord`, **não** de cada `note`: o nó `chord` some quando **toda**
     `note` descendente dele está em `H`. **Isto corrige o L02**, que dizia
     que trocar a cor da `note` bastava. E vale para os hinos: no
     `h010.vsb` há **95 nós `chord` para 425 notas** (70 e 356 no `h056`),
     embora o MusicXML não tenha um único `<chord/>` — o importador do
     Verovio junta numa `chord` as notas de uma mesma voz que começam
     juntas (o alto e o tenor do exemplo 1 da §11.1 são o acorde `yy2zfkq`).
     A coluna típica do hino **não** é só "duas notas em camadas diferentes".
   - Continuação de nota ligada é outra `note` na cena: esconde-se pelo id
     (`midi.json` → `tied`).
2. **Barra de ligação**: as formas **filhas diretas** de um `beam` somem
   quando toda `note` descendente do `beam` está em `H`. Nunca troque a cor do
   nó `beam` (pintaria as notas visíveis dele junto).
3. **Linhas suplementares**: um traço (forma `p` dentro de `ledgerLines …`,
   filho de `staff`, sem `id`) tem a **ordem** `k` (1ª, 2ª… linha a partir da
   pauta) e pertence às notas da mesma pauta de desenho cuja cabeça (contorno
   do glifo) ele cobre em x, com 1 unidade de folga, e cujo `loc` alcança a
   linha (acima `loc ≥ 2·(n−1) + 2k`; abaixo `loc ≤ −2k`). Some quando toda
   dona é nota e todas estão em `H`.
   - **A pausa deslocada é dona do traço** (e nunca é escondida): o Verovio
     desenha traço para uma pausa em posição explícita ou deslocada por
     camada, e o dele funde com o de uma nota da outra camada. Sem contar a
     pausa, a regra apagaria um traço de que ela precisa.
   - Um traço sem nenhuma dona fica visível. Não deve existir; a varredura não
     achou nenhum.

Validação obrigatória:
[`docs/formato/sumico/vetores.json`](formato/sumico/vetores.json), 11 casos —
ver a seção 5, porque o mesmo arquivo valida a pausa.

**Custo de recompilar `Picture`.** A barra e os traços estão em segmentos
**estáticos** (compilados uma vez em `ui.Picture`): apagá-los recompila a
página, ou exige promovê-los a dinâmicos. Não medi do lado de cá (é medição do
Flutter, `pictureBuilds`); o número que importa é o custo **por revelação**
(o decorar esconde no começo da etapa e revela uma coluna por erro). O critério
6 do L02 já pede a medição.

## 5. Pausa substituta (§11, regras 4-7) — L03

`standInFor(List<String> noteIds)` → `StandInRest {page, staffId, glyph, x,
y, sx, sy, dots}` (ou `null` se não der para calcular). Referência:
`hide_ref.py`, `stand_in`. Os passos, em unidades de viewBox, no referencial de
conteúdo (§5.1):

```text
figura  = nota de C com maior dur; empate: menor dots   // a "mais curta"
glifo   = "<fonte>:" + {1:E4E3 2:E4E4 4:E4E5 8:E4E6 16:E4E7 32:E4E8 64:E4E9}[dur]
x       = menor x de cabeça (u dentro de notehead) entre as notas de C
loc     = n − 1                       // linha do meio; n = nº de linhas da pauta
se dur ≤ 2 e loc ímpar:   loc −= 1    // com n = 5 nunca dispara
se dur == 1 e n > 1:      loc += 2    // a semibreve pende uma linha acima
y       = topY + (2·(n − 1) − loc)·unit
sx, sy  = gs  (do nó staff)
```

Sem pausa substituta (a coluna some do mesmo jeito, só não se desenha nada):
alguma nota de `C` sem `dur`; `dur` ≥ 128; glifo ausente do dicionário (`.vsb`
anterior a G08b); pauta com `n ≠ 5`; tablatura, percussão, mensural.

**Pontos de aumento** (`dots > 0`). Cada ponto é um **círculo** (não o glifo
`E1E7`, que existe no dicionário só por reserva), de raio
`r = max(2·unit/5, 2)`:

```text
locDot = loc;  se locDot é par: locDot += 1
se dur == 32 ou 64: locDot += 2               // a pausa de fusa/semifusa é mais alta
xRel   = (dur > 2) ? ⌊largura do glifo da pausa⌋ : ⌊2,5·unit⌋
x0     = x + xRel + unit
yDot   = topY + (2·(n − 1) − locDot)·unit
ponto j (0 … dots−1): elipse { cx = x0 + j·1,5·unit, cy = yDot, rx = ry = r }
```

**Uma pausa por (pauta de desenho, instante)** (regra 7): colunas de duas
pautas no mesmo instante dão duas pausas, cada uma na pauta de desenho (o
`staff` do nó, §5.1 — numa coluna cross-staff é a de desenho, não a de
origem).

Camada de overlay no molde da fantasma (`ghost_layer.dart`): `CustomPaint`
**por cima** da página, nunca um widget por forma; glifos pelo `GlyphCache`;
repinta só quando o conjunto de colunas ou um piscar muda; recortada na virada
por haste e acompanhando zoom e pan. Cor de repouso por parâmetro
(`kMemoRestColor`, nasce no L03) e "piscar" por coluna.

### Os vetores

`docs/formato/sumico/vetores.json`: `tolerancia` 0,5 (unidade de viewBox,
sobre todos os números; o `resumo` tem de bater **exatamente**) e `casos`:

| Campo | O que é |
| --- | --- |
| `vsb`, `pagina` | o `.vsb` na mesma pasta; `pagina` é o índice (0-based) ou `"altN.M"` (sequência alternativa N, página M — o `PageRef` das alternativas, §2.5) |
| `coluna` | `C`, os ids notados da coluna (todos na mesma pauta de desenho) |
| `escondidas` | `H`, todas as notas escondidas; **ausente = só `C`** |
| `resumo` | escrito à mão: nº de notas/acordes/barras/traços que somem, glifo, `loc` e nº de pontos da pausa |
| `esperado.hidden` | `notes` (ids), `chords` (ids dos nós `chord`), `beams` (`{id, shapes}`: o `beam` e quantas formas filhas diretas dele somem), `ledgers` (`[pauta, "above"/"below", k, x1, x2]` — o traço identificado pela pauta, lado, ordem e o intervalo em x) |
| `esperado.standIn` | `glyph`, `dur`, `x`, `y`, `sx`, `sy`, `loc`, `dots` (`[{cx, cy, rx, ry}]`) |
| `conta` | a aritmética à mão do caso |

Os 11 casos: duas vozes com figuras diferentes (vale a mais curta); traço da
coluna some e o das vizinhas fica; barra com 1 de 2 notas escondidas (fica) e
2 de 2 (some); semibreve (`loc` 6); figura pontuada (um círculo); empate de
figura (a sem ponto vence); colcheia de tercina (vale a escrita); nota ligada
(cabeça e continuação); coluna cross-staff; página alternativa. Dois deles
estão trabalhados à mão na §11.1 (hino 010).

`python3 compare/scripts/hide_ref.py --self-test` roda a referência contra os
mesmos 11 casos (0 divergências); `hide_ref.py <vsb> <página> <id,id…>` calcula
um caso qualquer. Um PNG de evidência por caso, desenhado a partir da
referência, sai de `compare/scripts/g08c-make-vectors.py` em
`compare/out/g08c/c01…c11-*.png` (git-ignorado).

### O que foi provado contra o Verovio

- **Pausa** (G08c, `hide_oracle.py`): (1) 855 pausas **de verdade** do corpus
  em pauta de uma camada, fora de barra, sem posição explícita: glifo, `y`,
  escala e pontos batem com a regra, 0 exceções (27 com pontos); (2) 854 de
  860 colunas sorteadas (`--seed 42`, estratificadas por figura de semibreve a
  semifusa, com e sem ponto) **trocadas por uma pausa de mesma figura numa
  cópia MEI e renderizadas pelo próprio Verovio**: 0 divergências de glifo,
  `y`, escala e pontos (840 conferidas; 14 em pauta que recebe cross-staff, que
  o Verovio desvia por colisão, classificadas à parte; 6 inviáveis).
  **O `x` não tem oráculo** (a troca muda o espaçamento); a regra usa o `x` da
  cabeça por definição.
- **Linhas suplementares**: 7 381 traços em 36 peças (normais e alternativas),
  8 367 donas: 0 sem dona e 0 com donas de colunas diferentes — **mas só
  depois** de dois acertos que a varredura impôs (a pausa deslocada é dona; as
  notas de um arpejo, de `on` ligeiramente diferentes no timemap, são uma
  coluna só: o nó `chord`). 108 traços têm uma pausa entre as donas.
- **Barras**: 3 115 `beam`, todos com ≥ 1 forma filha direta e ≥ 1 `note`
  descendente; 0 aninhados; 2 cross-staff (Clair de Lune: a regra vale como
  está); 1 615 com `chord` dentro; 0 `bTrem`/`fTrem`.

## 6. O que é do host e não do formato

- **Quais colunas somem** e quando (o sorteio, L01; as etapas, L05; no T16,
  só colunas de melodia de uma voz — a coluna com nota longa de outra voz
  não entra).
- **A cor da pausa** (`kMemoRestColor`), o **piscar** e o veredito, a
  **revelação ao errar** (D-SUM-ERRO) e a **prova às cegas**.
- Reproduzir a pausa no lugar certo da cronologia (a coluna é um instante do
  timemap; um id expandido `-rend<N>` vira o id da cena por `sceneIdOf`).
- Nota escondida **não tem halo e não responde a toque**: cor transparente não
  é "ausente" — o halo e o `onElementTap` ainda enxergam o nó. O `highlight`
  num id escondido não pinta a nota (o L05 pisca a pausa).

## 7. Números úteis

| O quê | Valor |
| --- | --- |
| Hino 010 (`h010.vsb`) | 2 páginas, 425 notas, 95 `chord`, 74 `beam`; pauta `topY` 1106, `unit` 90, `n` 5, `gs` 0,72 |
| Hino 056 (`h056.vsb`) | 2 páginas, 356 notas, 70 `chord`, 59 `beam`, 6 `rest`; tercinas |
| Traços de linha suplementar, corpus + hinos | 7 381, 0 sem dona, 0 de colunas diferentes |
| `beam` | 3 115; aninhados 0; cross-staff 2; com `chord` 1 615; `bTrem`/`fTrem` 0 |
| `beamSpan` | 47 casos (Nocturne e Clair de Lune; 0 nos hinos): **não** é `beam`, a barra fica |
| Pausas de verdade | 855 conferidas sem exceção; fora do oráculo: 200 em pauta de 2 camadas, 6 de 3, 132 com `ploc`/`oloc` explícito, 64 em barra, 7 em pauta com cross-staff, 10 sem figura |
| Largura da pausa × cabeça (226 u com `gs` 0,72) | semínima 219, colcheia 198, semicolcheia 233, semibreve e mínima 216; só fusa (286) e semifusa (344) passam da cabeça, para a direita |
| Figuras sem `dur` no corpus | 2 apojaturas (Scarlatti) |

## 8. Limitações aceitas da v1

- A pausa substituta pode ficar **apertada contra uma nota visível vizinha**:
  o espaçamento foi calculado para a nota, não para a pausa. Nas pautas que
  recebem cross-staff, em pauta de 2 camadas, com `@loc`/`@ploc` explícito e
  dentro de barra o Verovio mudaria a altura; a pausa substituta fica na
  posição padrão da pauta, que pode encostar numa nota visível.
- Ligadura de prolongamento ou de expressão que começa ou termina numa nota
  escondida continua desenhada; dedilhado (`fing`) também; apojaturas e
  ornamentos não somem.
- **`beamSpan` não some** (a barra que atravessa compasso ou quebra de
  sistema): a regra 2 não o alcança.
- Acorde cross-staff dividido entre duas pautas pode ficar com a haste (o nó
  `chord` só some quando toda `note` dele está escondida).
- O traço fundido com o de uma pausa deslocada fica **inteiro**, mais largo do
  que a pausa precisa.
- Pauta que não tem 5 linhas, tablatura, percussão e notação mensural: sem
  pausa substituta (a coluna some do mesmo jeito).
- **Direitos**: `h010.vsb` e `h056.vsb` vêm de hinos protegidos (© dos autores;
  arranjo © Casa Publicadora Brasileira) da própria biblioteca do `zywny`.
  Estão nas fixtures só como material de teste; para publicar o repositório,
  trocar por hinos de domínio público.

## 9. Esconder um compasso inteiro: a pausa de compasso (G11, regra 8)

Pedido do T17 do `zywny-aprendizado`: esconder **todo o compasso, nas duas
pautas**, e ver no lugar **uma pausa de compasso por pauta** (a semibreve
centrada), não uma fileira de pausas pequenas. Compassos escondidos vizinhos têm
cada um a sua. O contrato é a **§11.2** da especificação (regra 8); o `.vsb` e a
referência abaixo trazem tudo o que o host precisa. O código Dart é do
`zywny-comum` (planos L02/L03 e T17, item 0).

### 9.1 O que mudou no `.vsb` — e o que refazer

Um campo novo, aditivo (`version` continua `1`): **`inner: [x0, x1]` em todo nó
`measure`** (§5.1) — a faixa em que o Verovio centra a pausa de compasso. A conta
do host é `cx = x0 + ⌊(x1 − x0) / 2⌋` (divisão inteira). Foi a decisão
D-SUM-COMPASSO: o centro **não** sai do que o `.vsb` já tinha (depende de uma margem
de 87 a 90 unidades, e 125 quando só há clave, que o Verovio reserva depois do
cabeçalho e que a cena não grava): sem o campo, um compasso com cabeçalho (o
primeiro de cada linha) errava o centro em até 1,4 unidade e, usando a borda de
cada pauta, em até 18; com ele, **0 divergências em 5 170 pausas desenhadas pelo
Verovio**.

**É preciso refazer a `libverovio` de todas as plataformas, outra vez** (a
anterior é de G08b e não grava `inner`): **Linux** (`just native`), **Android**
arm64-v8a + x86_64 (`just native-android`) e **Web/wasm**
(`zywny-comum/tool/build_verovio_web.sh`). Os scripts não mudam. Um `.vsb` gerado
com a biblioteca antiga ainda funciona, mas as notas somem **sem** pausa de compasso
(sem `inner` a regra devolve nada), que é o comportamento previsto, não um erro.
**Regenerar as fixtures** do `zywny-comum` com a biblioteca nova: as de
`test/fixtures/sumico/` já vêm regeneradas (item 9.4); as de `fantasma/` e as do
corpus do host ganham `inner` e precisam ser refeitas para a suíte exercer o campo
(o parser ignora o campo se faltar).

### 9.2 O que o host faz (a regra, em resumo)

Para o conjunto `M` de compassos escondidos (ids de nó `measure`, os mesmos do
`measureOn` do timemap; `sceneIdOf` para `-rend<N>`). Referência:
[`compare/scripts/hide_ref.py`](../compare/scripts/hide_ref.py), `hidden_measures`
e `measure_stand_in`; a conta toda está na §11.2.

1. **Notas do compasso** = os nós `note` descendentes do nó `measure` (da própria
   cena, sem o `pitchpos.json`). Todas entram em `H`; as regras 1 a 3 (nota,
   acorde, barra, traço) valem como estão (L02).
2. **Pausas de verdade** (nós `rest`, não `mRest`) de uma pauta de desenho que
   **tem nota** no compasso **também somem** (e contam como donas escondidas do
   traço de linha suplementar). Pauta **sem nenhuma nota** (só pausa ou só
   `mRest`): o host **não faz nada** nela. É o caso das mãos intercaladas
   (1a a 3d): a mão que não toca fica com a pausa que já tem.
3. **Tercina** (`tuplet`): some o nó inteiro quando toda `note` e `rest` dentro
   dele some; leva o colchete e o número.
4. **Controles ancorados** (`tie`, `slur`, `phrase`, `arpeg`, `beamSpan`): somem
   quando **todos** os compassos que tocam estão em `M` (cálculo pela caixa do
   controle e pelo primeiro traço de linha de cada compasso: §11.2); ficam se
   cruzam para um compasso visível. **Alguns não têm `id`** (as metades de
   ligadura que cruzam a quebra de sistema são filhas do `system`, ids ausentes):
   identifique-os pelo nó, não pelo `id`; a referência os chama de
   `classe@x0,y0,x1,y1`.
5. **Pausa de compasso por pauta de desenho que tem nota:** `g = "<fonte>:E4E3"`;
   `cx` como acima; `x = cx − ⌊largura de E4E3 × sx⌋ / 2` (a mesma largura
   truncada da regra 6; o `/ 2` é inteiro); `y` e escala da semibreve da regra 6
   (`loc` 6 com `n = 5`, `y = topY + 2·unit`), sem pontos. Cor de repouso e
   piscar são do host, como na coluna. A **pausa de compasso substituta fica de
   fora** em: `.vsb` sem `inner`, compasso de **2 semibreves ou mais** (4/2, 8/4:
   o Verovio desenha a pausa de breve, `E4E2`, que não é glifo reservado; a
   duração vem de `measureOn` consecutivos no timemap), pauta com `n ≠ 5`.
6. O que **fica**: dinâmica, andamento, cifra, texto, pedal, ottava, trinado,
   fermata, dedilhado, número do compasso, letra, clave, armadura, fórmula, barras.
   A tabela com as ocorrências e a regra de cada uma está na §11.2.

### 9.3 Os vetores novos

Em `docs/formato/sumico/vetores.json`, chave **`casosCompasso`** (a chave `casos`,
que os testes atuais do host leem, **não mudou**: cada caso novo é uma entrada à
parte, para a suíte continuar verde sem código novo). Campos: `vsb`, `pagina`
(índice ou `"altN.M"`), `compassos` (os ids escondidos), `resumo` (contagens;
notas e pausas conferidas contra o MEI da fonte), `esperado.hidden` (`notes`,
`chords`, `beams`, `ledgers`, e os novos `rests`, `tuplets`, `controls`),
`esperado.measureStandIn` (`[{measure, staff, g, x, y, sx, sy}]`) e `conta`
(a aritmética de alguns). Tolerância 0,5 sobre todos os números; `resumo` exato.
`hide_ref.py --self-test` roda os 11 casos de coluna e os 15 de compasso (0
divergências).

| # | Caso | `.vsb` |
| --- | --- | --- |
| m01 | primeiro compasso do sistema (depois de clave, armadura e fórmula) | `h010.vsb` |
| m02, m03 | compasso comum; último da linha | `h010.vsb` |
| m04 | primeiro do sistema com cabeçalho **e** barra de repetição à esquerda | `h010.vsb`, `alt0.0` |
| m05 | armadura trocada no meio da linha | `f06-mudanca-armadura.vsb` |
| m06 | mão intercalada (2c): a pauta só com pausa fica como está | `g11-mao-intercalada.vsb` |
| m07 | pautas com notas e pausas misturadas: as pausas de verdade somem | idem |
| m08 | melodia na esquerda (4b) | `g11-melodia-esquerda.vsb` |
| m09 | tercina | `g11-tercina.vsb` |
| m10 | 6/8 (o glifo é a semibreve mesmo assim) | `g11-6-8.vsb` |
| m11 | uma pauta com notas e pausas, a outra já com `mRest` (fica) | `g11-especiais.vsb` |
| m12 | tercina e ligadura de expressão dentro do compasso somem; a ligadura de prolongamento para o seguinte fica | idem |
| m13 | dois compassos vizinhos: cada um com a sua pausa; a ligadura de prolongamento entre eles some | idem |
| m14 | 4/2: sem pausa de compasso substituta | idem |
| m15 | anacruse (1 semínima): mesma semibreve | idem |

Um PNG por caso (as notas somem e a pausa de compasso aparece em laranja) sai de
`compare/scripts/g11-make-vectors.py` em `compare/out/g11/vec/m01…m15-*.png`
(git-ignorado).

### 9.4 O que foi provado

- **A pausa** (`hide_oracle.py --measures`): (1) as 11 `mRest` de verdade do
  corpus (pauta de uma camada) batem com a regra em glifo, `x`, `y` e escala; (2)
  numa cópia MEI de cada peça de **todo o corpus (70 partituras, 35 do
  aprendizado)**, o conteúdo de **todos** os compassos de cada pauta (e de um em
  cada 3) vira `<mRest/>` e o próprio Verovio desenha **5 170 pausas**: **0
  divergências** de `x`, `y`, glifo e escala (|dx| máximo 0,00 em todas as
  categorias: 612 primeiro do sistema, 3 699 comum, 742 último, 42 primeiro com
  barra de repetição à esquerda, 54 só barra de repetição, 21 cabeçalho no meio).
  Os 2 compassos de 4/2 saem em `E4E2`, e a regra, coerente, não dá pausa. Uma
  anacruse de 1 semínima sai na mesma semibreve.
- **O que vaza** (`g11-sweep.py`): escondendo **todos** os compassos de cada
  uma das 124 páginas (1 517 compassos), **0 vazamentos**: não sobra nota, haste,
  barra, tercina nem ligadura; só ficam pauta, clave, armadura, fórmula, barras,
  letra, dinâmica, andamento, cifra, pedal e as pausas de pautas sem nota.
  Pautas por compasso: 2 140 só notas, 732 notas e pausas (as pausas somem), 35
  só pausas (ficam), 11 só `mRest` (ficam).
- **Achados que mudaram a regra** (a spec segue o Verovio): ligaduras que cruzam
  a quebra de sistema são filhas do `system`, sem `id` (116 `tie`, 25 `slur`, 4
  `phrase` no corpus): sem contá-las, escondendo uma página inteira sobravam essas
  ligaduras no ar; o `beamSpan` e o arpejo passam a ter dono (o compasso) e deixam
  de ser limitação.

### 9.5 Limitações da regra 8

- Ligadura que cruza para um compasso **visível** continua desenhada (dá a
  entender que o som continua); a nota ligada que está no compasso visível
  continua visível lá.
- Pausa de compasso de **várias vozes em camadas** (a posição vertical muda no
  Verovio) e multi-compasso (`multiRest`) ficam fora; ottava, trinado, fermata e
  dedilhado ficam.
- Compasso de 2 semibreves ou mais e pauta com `n ≠ 5`: as notas somem sem
  pausa de compasso. Anacruse: mesma semibreve (o aprendizado não gera; esconder
  uma anacruse é decisão do host).
- A pausa de compasso substitui **a pauta toda do compasso**: vale o compasso
  completo, não o ritmo, de propósito (é o que o T17 quer).
