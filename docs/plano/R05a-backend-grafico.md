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
  tolerância 32/255 absorve em boa parte — mas "em boa parte" não é "sempre",
  e o alvo do projeto é 0,1%, uma margem estreita.
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
   o mesmo PNG do SVG (tolerância 32).
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

(a preencher por quem executar)
