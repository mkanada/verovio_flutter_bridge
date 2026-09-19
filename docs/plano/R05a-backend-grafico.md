# R05a — Decisão: backend gráfico da comparação (Impeller × Skia)

**Depende de:** R03c · **Decisão necessária:** SIM (backend gráfico)

## Objetivo

Escolher, **com números**, qual backend gráfico do Flutter é o oficial da
comparação visual, e registrar a escolha onde ela não se perca. Dois números
medidos com backends diferentes não são comparáveis — é por isso que esta
decisão vem antes da varredura do corpus.

## Decisão necessária

Impeller (padrão atual do Flutter no Linux) ou Skia
(`--no-enable-impeller` / `FLUTTER_ENABLE_IMPELLER=0`). Meça os dois nas
mesmas páginas, leve os dois números ao usuário e **não decida sozinho**.

## Ler antes (só isto)

- `../verovio_lottie/compare/README.md`, seção "Execução: modo batch sob
  xvfb".
- Risco 2 do [README do plano](README.md).
- Notas de execução de R02d (o comando `scene-to-png` e o backend que estava
  ativo quando você gerou a primeira imagem).

## Contexto que você precisa (não vá procurar, está aqui)

- O lado de referência (`resvg` + `tiny-skia`) é **fixo**: não muda com o
  backend do Flutter. O que muda é o lado da cena.
- A diferença esperada entre backends é de **antialiasing de borda**, que a
  tolerância da época (32/255) absorvia em boa parte — mas "em boa parte" não
  é "sempre", e o alvo do projeto era 0,1%, uma margem estreita.
- Como forçar Skia no app `compare` (Linux desktop): variável de ambiente
  `FLUTTER_ENABLE_IMPELLER=0` na execução, ou `flutter build linux
  --no-enable-impeller`. Registre **exatamente** o mecanismo que funcionou na
  sua versão do Flutter (isso muda entre versões; a do projeto é a
  3.47.4 / Dart 3.13.3).
- Rode tudo sob `xvfb-run -a` quando `DISPLAY` estiver vazio.

## O que fazer

1. Escolher 5 páginas de 5 peças diferentes, com perfis distintos (muita
   nota, muito texto, com tracejado, com rotação/arpejo, e uma página de
   pouco conteúdo).
2. Para cada uma, gerar o PNG da cena com Impeller e com Skia e diffar contra
   o mesmo PNG do SVG (tolerância 32 na época; hoje 128).
3. Montar uma tabela: página × backend × % divergente × tempo de execução.
4. Levar a tabela ao usuário com uma pergunta objetiva e registrar a
   resposta, com data, nas notas.
5. Escrever a escolha em `compare/README.md`, com o comando exato que ativa
   aquele backend.

## Fora de escopo

- Ajustar render para "melhorar a %" — se a % estiver ruim nos dois, o
  conserto é no passo da primitiva correspondente.
- Backend do app de produção (P03 mede em dispositivo; aqui é só a
  comparação).

## Critérios de aceite

1. Tabela com 5 páginas × 2 backends, com % e tempo, nas notas de execução.
2. Determinismo dentro de cada backend: rodar duas vezes a mesma página
   produz PNGs **byte-idênticos** (`cmp`). Se não produzir, diga isso ao
   usuário antes de qualquer outra coisa — comparação não determinística
   invalida todos os números seguintes.
3. A pergunta foi feita ao usuário e a resposta está registrada, com data.
4. `compare/README.md` diz qual é o backend oficial e como ativá-lo.
5. A linha "backend gráfico" da tabela de decisões pendentes do
   [README do plano](README.md) e do `CLAUDE.md` está marcada como resolvida,
   com o resultado.

## Notas de execução

Executado em 2026-09-19 (Flutter 3.47.4 / Dart 3.13.3). 5 páginas de 5 peças
distintas, perfis conforme o passo (muita nota, muito texto, tracejado,
rotação/arpejo, pouco conteúdo); tolerância 32 (da época; 6 237 000 px, 2100×2970 em
todas). SVG e `.vsb` gerados do mesmo fonte com flags padrão; `.vsb` sempre
com todas as páginas. Artefatos descartáveis em `/tmp/opencode/r05a/` (os
PNGs de referência da decisão ficam nos logs abaixo, não no repo).

| Página (perfil) | Impeller % (divergentes) | Skia % (divergentes) | Tempo Imp / Skia |
| --- | --- | --- | --- |
| Maple Leaf Rag p1 (muita nota) | 0,3603% (22 475) | 0,6824% (42 561) | 0,92s / 0,89s |
| Clair de Lune p1 (muito texto) | 0,8590% (53 578) | 0,7765% (48 430) | 0,99s / 1,02s |
| Chopin Étude p1 (tracejado octave) | 0,4978% (31 046) | 0,6048% (37 722) | 0,94s / 0,91s |
| Nocturne p1 (arpejo −90°) | 0,6794% (42 373) | 0,8800% (54 883) | 0,95s / 0,95s |
| Satie Gymnopédie p2 (pouco conteúdo) | 0,0552% (3 445) | 0,0394% (2 456) | 0,82s / 0,77s |
| Média | **0,4903%** | **0,5966%** | — |

Determinismo (critério 2): Clair p1 rodada 2× em cada backend dá PNGs
**byte-idênticos** (`cmp`; sha256 iguais), e o rebuild Impeller reproduz o
PNG original — comparação determinística nos dois backends. Impeller ≠ Skia
entre si, como esperado.

Mecanismo que funciona nesta versão do Flutter (o passo citava dois que
**não** funcionam mais: `flutter build linux --no-enable-impeller` não
existe no `flutter build linux --help`, e `FLUTTER_ENABLE_IMPELLER=0` na
execução mantém o Impeller — ambos sondados à mão): o oficial, segundo
<https://docs.flutter.dev/perf/impeller>, é
`fl_dart_project_set_enable_impeller(project, FALSE);` após
`fl_dart_project_new()` em `compare/linux/runner/my_application.cc` +
rebuild (sem a linha = Impeller). Verificado: com a linha, a mensagem
`Using the Impeller rendering backend (OpenGLESSDF)` some do stderr e os
números mudam (tabela acima); sem a linha, ela aparece. O `my_application.cc`
foi revertido ao original após a medição (`git status` limpo) — o build
atual é Impeller.

Decisão (2026-09-19): **Impeller** — confirmada pelo usuário na sessão
— melhor média e 3/5 páginas, padrão do
Flutter 3.47, e o opt-out Skia será removido em versão futura (reverter para
Skia é 1 linha + rebuild + `COMPARE_BACKEND=skia`, documentado em
`compare/README.md` e no cabeçalho do `compare-page.sh`). Registrada em
`compare/README.md`, no README do plano e no `CLAUDE.md`.
