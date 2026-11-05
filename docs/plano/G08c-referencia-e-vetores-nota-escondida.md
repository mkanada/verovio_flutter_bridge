# G08c — Referência, varredura do corpus, oráculo e vetores da nota escondida

**Depende de:** G08b · **Decisão necessária:** só se a varredura falhar —
**D-SUM-NATIVO** (ver [`G07`](G07-visao-geral-nota-escondida.md))

## Objetivo

Provar a §11 antes de o `zywny` portá-la: uma implementação de referência
em Python, uma varredura do corpus que confirma (ou derruba) a regra
geométrica das linhas suplementares e a da barra de ligação, um oráculo
Verovio para a posição da pausa, e os vetores de teste que o host vai usar.

## Ler antes (só isto)

- [`G07`](G07-visao-geral-nota-escondida.md) e a §11 da spec.
- [`G04d`](G04d-oraculo-e-vetores.md) e as notas de execução dele: o molde
  de referência + oráculo + vetores, e as armadilhas (sementes de id
  diferentes entre `-t mei` e `-t vsb`).
- `compare/scripts/ghost_ref.py` (leitura do `.vsb`, índice por página,
  geometria da pauta — reaproveite, não copie), `ghost_oracle.py`,
  `g04d-make-vectors.py`.
- `docs/formato/fantasma/vetores.json` (formato dos vetores).
- `verovio/src/staff.cpp` L381-L409 (`LedgerLine::AddDash`) e
  `verovio/src/view_element.cpp` L887-L915 (`View::DrawDots`).

## Contexto que você precisa

- **O corpus não cobre o caso principal.** Os 600 hinos do `zywny` têm duas
  vozes por pauta em camadas separadas, letra, e 586 têm ponto de aumento;
  nenhuma peça de `corpus/` é assim. Traga dois hinos de
  `/home/mauricio/IdeaProjects/Hymn_Grabber/musicxml/` (o `assets/hinos/` saiu do
  app no B08; `zywny-musicas/tool/build_hymn_assets.py` lê dessa pasta) para
  `corpus/sumico/`
  (descompactados; escolha um com linhas suplementares nas duas pautas e
  um com quiáltera) e registre no `corpus/README.md` de onde vieram.
- **Regra das linhas suplementares (regra 3).** A varredura é a prova:
  para todo traço de todo `ledgerLines …` do corpus, calcular as donas
  pela regra e conferir que (i) todo traço tem ao menos uma dona; (ii) as
  donas de um traço são sempre da **mesma coluna** (mesma pauta de
  desenho, mesmo instante no timemap). Se (ii) falhar, existe traço
  fundido entre colunas diferentes — esconder uma delas deixaria o traço
  ou apagaria o da vizinha. O `AddDash` diz que isso não acontece ("os de
  notas vizinhas não fundem"), mas é a varredura que decide. Falhou →
  **pare**, abra D-SUM-NATIVO com o usuário (plano B: gravar no traço os
  ids de `Dash::m_events`), e não invente regra de desempate.
- **Regra da barra (regra 2).** Varredura: todo `beam` tem ao menos uma
  forma filha direta e ao menos uma `note` descendente; registre os casos
  de barra aninhada, barra entre pautas (cross-staff) e `fTrem`/`bTrem`,
  que desenham de outro jeito — entram como limitação ou como regra.
- **Oráculo da pausa (regras 4-6).** Duas provas, a segunda mais forte:
  1. *Sem rodar o Verovio de novo*: para toda pausa de verdade em pauta de
     uma camada só, o `y` e a escala da cena batem com a regra 6 e o glifo
     com a regra 5 (0 exceções esperadas; pausas em pauta de duas camadas
     ficam fora, por causa do ajuste por camada, e são contadas à parte).
  2. *Rodando o Verovio*: numa cópia da peça, trocar a coluna inteira por
     uma pausa de mesma figura (MEI: `<rest dur= dots=>` no lugar das
     notas, uma camada só) e conferir que o Verovio desenha o mesmo glifo,
     no mesmo `y` e com os pontos onde a regra diz. O `x` **não** se
     compara: trocar nota por pausa muda o espaçamento, e a regra 6 usa o
     `x` da cabeça original por definição.
- **Pontos.** A conta de G08a sai de `DrawDots`; a prova 2 é o que a
  valida. Se divergir, corrija a §11 (a spec segue o Verovio).
- Vetores: uma coluna, um conjunto escondido → o que some (ids de nota,
  ids de `beam`, traços por `(pauta, lado, ordem, x1, x2)`) e a pausa
  (`glyph`, `x`, `y`, `sx`, `sy`, pontos). Tolerância de 0,5 unidade de
  viewBox, como em G04d.

## O que fazer

1. `corpus/sumico/`: os dois hinos; `.vsb` em `docs/formato/sumico/`.
2. `compare/scripts/hide_ref.py`: `hidden_shapes(vsb, page, note_ids)` e
   `stand_in(vsb, page, note_ids)` — as regras 1-7 — com `--self-test`.
3. `compare/scripts/g08c-sweep.py`: varreduras da regra 3 e da regra 2
   sobre `corpus/` inteiro (normais e alternativas) + os hinos; números
   por peça.
4. `compare/scripts/hide_oracle.py`: as duas provas da pausa.
5. `compare/scripts/g08c-make-vectors.py` →
   `docs/formato/sumico/vetores.json`, com o `resumo` de cada caso
   conferido à mão. Casos mínimos: coluna de duas vozes com figuras
   diferentes; coluna com linha suplementar ao lado de coluna visível com
   linha suplementar; barra com 1 de 2 e 2 de 2 notas escondidas;
   semibreve; pontuada; quiáltera; nota ligada (cabeça + continuação);
   coluna cross-staff; página alternativa.
6. §11.1 da spec: os dois exemplos trabalhados, com os números do hino.
7. Corrigir a §11 e o `G07` onde a medição contradisser o texto.

## Fora de escopo

- Implementar o plano B de D-SUM-NATIVO (é outro passo, só se necessário).
- Escolher colunas, cores, revelar (host).
- O lado Dart.

## Critérios de aceite

1. Varredura da regra 3: número de traços, de traços sem dona e de traços
   com donas de colunas diferentes, por peça. Aceite: **0 e 0** — ou o
   passo para em D-SUM-NATIVO, com os casos listados (peça, página, x).
2. Varredura da regra 2: número de `beam`, de aninhados, cross-staff e
   tremolos, e o que a regra faz em cada um.
3. Prova 1 da pausa: pausas conferidas, exceções (esperado 0 em pauta de
   uma camada).
4. Prova 2 da pausa: ao menos 500 colunas sorteadas (`--seed` fixo) entre
   corpus e hinos, 0 divergências de glifo, `y` e pontos.
5. `hide_ref.py --self-test` verde; `vetores.json` com os 9 casos mínimos.
6. Um PNG de evidência por caso em `compare/out/g08c/` (a página com a
   coluna escondida e a pausa, desenhada a partir da referência) — para o
   usuário olhar antes de o `zywny` portar.
7. `ghost_ref.py --self-test` continua verde (o que foi reaproveitado não
   quebrou).

## Notas de execução

Concluído em 2026-11-04. Nenhuma linha de `verovio/` mudou (o passo é só referência,
medição e documentação). Scripts em `compare/scripts/`: `hide_ref.py` (a referência, com
`--self-test`), `g08c-sweep.py`, `hide_oracle.py`, `g08c-make-vectors.py`, `scene_svg.py`
(desenha a página só para a evidência). Saídas em `compare/out/g08c/` (`sweep/`,
`oraculo/`, um PNG por caso). Corpus novo: `corpus/sumico/` (`h010`, `h056`,
`s01-pausas-pontuadas.mei`, escrito à mão); vetores e `.vsb` em `docs/formato/sumico/`.

- **Critério 1 (regra 3): 0 e 0**, mas só depois de dois acertos que a varredura impôs
  (D-SUM-NATIVO resolvida: **sem dado novo na cena**). 7 381 traços em 36 peças (páginas
  normais e alternativas), 8 367 donas. Com a regra como a G08a a escreveu houve **4 sem dona**
  (Mazurka, uma pausa de mínima deslocada para 4 linhas abaixo, com traço próprio) e **4
  com donas de colunas diferentes** (Clair de Lune, um arpejo: o `arpeg` espalha os `on` de
  0,02 a 0,04 de semínima, mas as notas são um acorde na cena). Acertos: (1) **a pausa é dona
  do traço** — 108 traços têm uma pausa entre as donas (4 só dela, 104 fundidos com o de uma
  nota da outra camada, em Mazurka/Bach/Satie/Scarlatti; nos hinos, 0): sem isso a regra
  apagaria o traço de que uma pausa visível precisa; (2) coluna de arpejo = o nó `chord`.
- **Critério 2 (regra 2)**: 3 115 `beam`; todos com ≥ 1 forma filha direta e ≥ 1 `note`
  descendente; 0 aninhados; 2 cross-staff (Clair de Lune: a regra vale, some quando as duas
  pautas somem); 1 615 com `chord` dentro; 0 `bTrem`/`fTrem`. **Achado**: `beamSpan` (47 casos
  em Nocturne e Clair de Lune, nenhum nos hinos) é um nó próprio sem nota descendente — a
  regra não o alcança e a barra dele fica (limitação nova, §11).
- **Critério 3 (prova 1, sem Verovio)**: 855 pausas conferidas (pauta de uma camada, fora de
  barra e de cue, sem posição explícita, sem cross-staff vindo de outra pauta), **0 exceções**,
  27 delas com pontos; fora: 200 em pauta de 2 camadas e 6 de 3, 132 com `ploc`/`oloc`
  explícitos (MusicXML `display-step`), 64 em barra, 7 em pauta que recebe cross-staff, 10 sem
  figura (`mRest`/`multiRest`/fora da faixa).
- **Critério 4 (prova 2, no Verovio)**: sorteio estratificado por figura (até 100 colunas
  por semibreve…semifusa, pontuada ou não; `--seed 42`): 860 colunas, 6 inviáveis, **854
  trocadas por uma pausa numa cópia MEI e renderizadas, 0 divergências de glifo, `y`, escala e
  pontos** (840 conferidas + 14 em pauta que recebe cross-staff, que o Verovio desvia por
  colisão, classificadas à parte). Cobre semibreve a semifusa; fusa e semifusa pontuadas só
  existem em `s01` (prova 1). 69 cópias, ~50 s.
- **O que o oráculo corrigiu na §11** (a spec segue o Verovio): (a) a conta dos pontos usa a
  largura do glifo **truncada** (`int`; sem isso o ponto saía 0,7 unidade deslocado em dur 8);
  (b) `dur ≥ 2` na regra 6 era numericamente invertido (o certo é `dur ≤ 2`, "mais longa que
  a semínima"; com `n = 5` não dispara, por isso nada divergiu); (c) pausa só em pauta de
  5 linhas, declarado; (d) o `x` não tem oráculo (a troca muda o espaçamento) — a spec agora
  diz isso e dá as larguras das pausas em relação à cabeça, em vez de prometer uma medição.
- **Armadilhas da prova 2**: trocar nota por pausa deixa para trás ligaduras, dinâmicas e
  pedais que apontam para ids removidos, **em outros compassos também** (`endid` do outro
  lado: o Verovio dá SIGSEGV); a cópia tem de varrer o documento inteiro e remover esses
  controles. A barra tem de ser desfeita em **qualquer** nível (uma pausa numa tercina dentro
  de `beam` é ajustada pela barra e muda de altura). As cópias usam `--xml-id-seed 7` (o
  `-t mei` usa 42), como em G04d.
- **Critério 5**: `hide_ref.py --self-test`: 11 casos, 0 divergências; `vetores.json` com os 9
  casos mínimos + empate de figura + barra 1 de 2 (11 no total), `resumo` escrito à mão por
  caso (a conta está em `conta`) e igual ao da referência na primeira passada.
- **Critério 6**: 11 PNGs em `compare/out/g08c/c01…c11-*.png` (a coluna some, a pausa em
  laranja; a letra, a clave e as outras colunas ficam). Olhados: c01, c04, c06, c09, c10.
- **Critério 7**: `ghost_ref.py --self-test` verde (32 casos, 0 divergências).
- **Direitos**: os dois hinos são protegidos (`<rights>`: © dos autores; arranjo © 2020
  Casa Publicadora Brasileira). Estão em `corpus/sumico/` como material de teste, com a
  ressalva no `corpus/README.md`; para publicar o repositório, trocar por hinos de domínio
  público.
- **Para G09 (nota ao `zywny`)**: as regras novas que o host precisa implementar — a pausa
  deslocada é dona do traço (nunca é escondida), `dur ≤ 2`, largura truncada nos pontos,
  `beamSpan` não some — estão na §11; o host compara com `vetores.json` (tolerância 0,5).
