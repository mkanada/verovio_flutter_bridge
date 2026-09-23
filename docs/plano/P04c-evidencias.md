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

Implementado como planejado: `tool/generate_examples.dart` ganhou
`_repeticaoAlternativaExample`, chamada uma vez por peça
(`MapleLeafRag`/`Mazurka`), que monta duas instâncias (`useAlternates:
true` e `false`) do trio `ScoreView`/`ScoreViewController`/`ScorePlayer`
sobre a mesma peça e captura 7 quadros (os 6 do "O que fazer" + o de
comparação do item 3).

**Fixture nova:** `test/fixtures/mazurka.vsb`, gerada com
`verovio corpus/mei/Chopin_Mazurka_Op6_No1.mei -t vsb --xml-id-seed 42`
(os padrões do bridge, D-VSB-PADRAO, já saem sozinhos de `-t vsb`) — a
mesma peça MEI de referência da fase E, agora com `alternates.json` (1
sequência, a única desta peça com salto entre páginas — "42 → 18", página
1 → 0, já medido em P01c).

Cada peça tem exatamente **um** salto que cruza página (P01c): a busca do
salto é `tl.measures.indexWhere((m) => m.view.isAlternate)` — a 1ª
ocorrência alternativa da execução já é o destino dele, porque uma
sequência alternativa, uma vez alcançada, dura até o fim da peça
(D-ALT-EXTENSAO), então não há um "2º primeiro salto alternativo" a
confundir com o 1º.

1. Quadros e `roteiro.md` gravados em `docs/exemplos/repeticao-alternativa/
   MapleLeafRag/` e `.../Mazurka/`.
2. **Verificado por asserção, não só pela imagem:** cada `roteiro.md` inclui
   um `expect` (no próprio gerador) de que
   `alternates[sequence].pages[view.index].firstMeasureId == <compasso de
   chegada>` — e visualmente (ver quadro 3 de cada peça): o compasso de
   chegada aparece à esquerda da haste, no topo da página alternativa. O
   quadro de comparação (`useAlternates: false`) mostra a mesma haste
   revelando a página normal, com o compasso de chegada no **meio** dela —
   a diferença que a fase P inteira existe para eliminar.
   - **Achado durante a implementação:** o quadro 6 ("nota da 2ª passagem
     acesa") não pode usar o instante do próprio salto (`next.startMs`):
     `displayedPage` só muda de página na **conclusão** da haste
     (`next.startMs + d`), não no instante do salto em si — um `seek` para
     `next.startMs` ainda mostra a página antiga (a haste ainda estaria no
     meio da conclusão). Corrigido para `seek(next.startMs + d + 50)`, com
     um `expect(vc.displayedPage, next.view)` no próprio gerador para não
     repetir o erro se a peça de exemplo mudar.
3. **Nenhum PNG de outro passo sobrevive no diff final** — `git checkout`
   descartou os PNGs/roteiro.md regenerados de `destaque-notas/`,
   `virada-pagina/` e `repeticao/` (diferenças de ambiente, 0,2-3%, como o
   próprio passo avisa). `docs/exemplos/repeticao-alternativa/` é a única
   pasta nova.

**Achado fora do escopo deste passo, registrado e não corrigido (Fora de
escopo: "mudanças de comportamento… registre e pare"):** ao regenerar,
`docs/exemplos/repeticao/MapleLeafRag/roteiro.md` (do E03b/D-SALTO) mudou
de conteúdo, não só de pixels — os dois saltos que ele documenta (`39900
ms` e `97500 ms`) **não são mais saltos entre páginas** na paginação atual
(P01c mudou a paginação; a única travessia de página desta peça sobrevivente
é a de `153900 ms`, a mesma que este passo usa). A regeneração mostra
"haste ausente" nos 4 primeiros quadros dos dois saltos, onde antes havia
haste — ou seja, **o exemplo de E03b está descrevendo saltos que não
existem mais como travessias de página**, silenciosamente, desde P01c. Os
PNGs/roteiro.md committados desse exemplo foram mantidos como estavam
(`git checkout`), porque corrigi-los é uma mudança de escopo (decidir
*quais* saltos ilustrar, já que a peça só tem 1 travessia de página agora,
não 2) que este passo não pediu. Fica registrado para o usuário decidir se
vale um passo à parte para atualizar/consolidar
`docs/exemplos/repeticao/MapleLeafRag/`.

`flutter analyze`: nenhum problema. `flutter test tool/generate_examples.dart`
(5 casos, os 3 de antes + os 2 novos): todos passam. Suíte inteira
(`flutter test`) não afetada — este passo não tocou nenhum arquivo de
`lib/`.
