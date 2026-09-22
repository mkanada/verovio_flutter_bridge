# P04c — Evidências visuais das páginas alternativas

**Depende de:** P04b · **Decisão necessária:** não

## Objetivo

Registrar a prova visual do comportamento novo, no mesmo formato de
`docs/exemplos/repeticao/` (E03b), para o usuário julgar pelo olho antes do
portão.

## Ler antes (só isto)

- `score_bridge/tool/generate_examples.dart`.
- `docs/exemplos/repeticao/MapleLeafRag/roteiro.md`.
- E03b, "Notas de execução" (`restNear` e o achado de que o
  `generate_examples` regera também os PNGs de A02c/A05b).

## Contexto que você precisa (não vá procurar, está aqui)

- `flutter test tool/generate_examples.dart` roda **todos** os testes do
  arquivo e regera PNGs de outros passos com diferenças de ambiente
  (0,2-3%). Descarte com `git checkout` o que não for deste passo.
- Saltos encadeados de perto fazem um "repouso" ingênuo cair dentro de outra
  haste. Use `restNear`.

## O que fazer

1. Estenda `tool/generate_examples.dart` para gerar
   `docs/exemplos/repeticao-alternativa/MapleLeafRag/` e
   `.../Mazurka/` (uma peça MusicXML e uma MEI). Para o 1º salto entre
   páginas de cada uma, 6 quadros:
   1. repouso antes do salto;
   2. meio da entrada da haste;
   3. haste estacionada: a **alternativa** atrás, com o compasso de chegada
      no canto superior esquerdo;
   4. meio da conclusão;
   5. repouso na alternativa;
   6. uma nota da 2ª passagem acesa **na alternativa**.
2. `roteiro.md` em cada pasta: instante de cada quadro, `displayedPage`, e o
   que se vê.
3. Um quadro "antes" equivalente com `useAlternates: false` (o
   comportamento de E03b), para comparação lado a lado.

## Fora de escopo

- Mudanças de comportamento. Se a evidência mostrar um problema, registre e
  pare.

## Critérios de aceite

1. Os quadros e os `roteiro.md` estão em
   `docs/exemplos/repeticao-alternativa/`.
2. No quadro 3, o compasso de chegada é o primeiro da página de trás (confira
   por imagem e pela bbox de `geometryOf(k)`).
3. Nenhum PNG de outro passo foi alterado no diff final.

## Notas de execução

_(preencher)_
