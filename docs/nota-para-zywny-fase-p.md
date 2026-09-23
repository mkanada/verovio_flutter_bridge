# Nota para o `zywny` — fase P (páginas alternativas)

Fechada em 2026-09-22. Não muda nada no `zywny`; é só o que a fase P dá de
novo para o host usar, e o que continua fora.

## O que o host ganha

- **Num salto de repetição que muda de página, a vista não volta mais para
  a página normal de destino** (onde o compasso de chegada podia estar no
  meio) — mostra uma página **alternativa**, redesenhada a partir dele, com
  o compasso de chegada sempre no topo. Automático: acontece sozinho
  enquanto o `ScorePlayer` estiver tocando, sem nenhuma chamada nova do
  host.
- **`ScoreViewController.displayedPage`** (`PageRef`) é a página realmente
  na tela agora — normal ou alternativa. **`currentPage`/`goToPage`
  continuam falando só de páginas normais**, como sempre (o usuário nunca
  vê "página 3 de uma sequência" — só "página 3"). Se o host mostra o
  número da página em algum lugar da UI, continue usando `currentPage`;
  `displayedPage` só importa se o host quiser saber se a tela está numa
  alternativa agora (por exemplo, para não deixar o usuário "virar
  manualmente" para longe dela sem querer).
- **`ScoreViewController.showPage(PageRef)`**: API do player (não é para o
  host chamar diretamente, salvo um uso avançado) para mostrar uma
  alternativa; `goToPage`/`nextPage`/`previousPage` do usuário sempre
  voltam para as páginas normais.
- **`ScorePlayer({..., useAlternates: true})`** (padrão): liga a rota nova.
  `useAlternates: false` desliga por completo — a vista volta a se
  comportar exatamente como antes desta fase (E03b), sempre em páginas
  normais. Não há necessidade de mudar nada além de passar esse parâmetro
  se o host quiser desligar.
- **Importante para gerar o `.vsb` em runtime (D-RUNTIME):** chame
  `toolkit.setOutputTo('vsb')` **antes** de `loadData`. Os padrões de
  D-VSB-PADRAO (`--header none --footer none --no-instrument-labels`, e a
  geração de `alternates.json`) só se aplicam quando o Toolkit já sabe que
  vai gerar `.vsb` — chamar `loadData` primeiro e mudar o formato de saída
  depois não ativa esses padrões.

## Custo (medido, não decidido)

Gerar as páginas alternativas custa **zero** em peças sem repetição de
verdade (a maioria: 6 das 10 peças do corpus). Nas que têm, o custo escala
com o número de sequências, não com o tamanho da peça: de +15% a +85% de
tamanho/tempo de geração no caso comum (1 sequência), até **+330%/+280%**
no pior caso medido (Maple Leaf Rag, 8 sequências) — números completos,
por peça, em `docs/relatorio-paginas-alternativas.md`. O parse no Dart
(`VsbDocument.alternates`) é preguiçoso: só custa alguma coisa se o host
efetivamente consultar `alternates`/`ScoreTimeline` com `useAlternates:
true` (o padrão) numa peça que tenha sequências.

**Se o custo for alto demais para uma peça específica** (o pior caso é uma
peça com muita repetição), `useAlternates: false` no `ScorePlayer` evita
consultar `alternates` de todo — a decisão de gerar `.vsb` **sem**
alternativas (`--no-vsb-alternates`, se algum dia exposto no host) ainda
não foi pedida por nenhum passo do plano.

## O que continua fora (não implementado)

- **Encoding binário (D-BIN)**: continua decisão do usuário, agora com
  números reais de tamanho/tempo no relatório citado acima, para julgar se
  vale a pena.
- **`seekToElement`/toque num elemento de uma sequência**: a rota de P04a
  decide a página a exibir por **posição no tempo** (`ScorePlayer.seek`);
  tocar diretamente num elemento (`onElementTap`) continua resolvendo pela
  regra de D-TOQUE (fase E) sem levar em conta se o resultado cai numa
  página alternativa — funciona (a rota se aplica de qualquer jeito depois
  do `seek`), só não foi um caso testado à parte neste passo.
- **Cortar sequências alternativas não usadas por nenhum salto real**
  (D-ALT-EXTENSAO manda gerar até o fim da peça sempre) — rever isso é
  decisão do usuário, à luz dos números de custo acima.
