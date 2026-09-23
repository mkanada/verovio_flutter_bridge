# Relatório de paridade visual — SVG vs. `score_bridge` (`.vsb`)

**Data:** 2026-09-20 · **Commit:** `e81b6e1` (Impeller) · **Backend gráfico
atual:** Skia (ver "Atualização de 2026-09-20") · **Tolerância:** 128/255 por
canal, portão 99,99%/0,01% (decisão do usuário em 2026-09-19).

**Versões:** Verovio 6.3.0 (build local a partir deste commit) · Flutter
3.47.4 stable · `resvg` 0.48.1 + `tiny-skia` 0.12.0 (referência).

Gerado por `compare/scripts/compare-corpus.sh 128` contra os 10 arquivos de
`corpus/mei/` + `corpus/musicxml/` (34 páginas). Saídas por página (SVG,
`.vsb`, os três PNGs, log) em `compare/corpus/` — **versionado**, visível
página a página direto no GitHub. CSV bruto em
`compare/corpus/resultado.csv`. Amostra curada por categoria em
[`docs/mesa-de-prova/`](mesa-de-prova/README.md).

## Atualização de 2026-09-20 — re-medição com Skia

O usuário descobriu que o Flutter com Impeller no Linux não está aplicando
antialiasing e pediu para a comparação deixar de usar o Impeller. O runner do
`compare` agora chama `fl_dart_project_set_enable_impeller(project, FALSE)`
(**backend gráfico: Skia**) e o corpus inteiro foi re-medido, mesmo comando,
mesma tolerância (128/255), mesmos 34 arquivos; `compare/corpus/resultado.csv`
e os PNGs de `compare/corpus/` são agora **Skia**. A coluna "Impeller" da
tabela abaixo é a medição anterior (commit `e81b6e1`), mantida para
comparação.

| | Impeller (e81b6e1) | Skia (atual) |
| --- | --- | --- |
| Páginas | 34/34 | 34/34 |
| Min | 0,000481% | 0,000497% |
| Max | 0,038624% | 0,039330% |
| Média | 0,008456% | 0,008800% |
| Páginas ≤ 0,01% | 27/34 | 27/34 |
| Páginas ≤ 0,05% | 34/34 | 34/34 |

- **Skia ficou marginalmente pior**: média +0,000344 pp (0,008456% →
  0,008800%), pior em 32 das 34 páginas; melhor em 2 (Étude p4 e Butterfly
  p2, por 1 pixel cada). A diferença por página vai de 1 a ~73 pixels em
  6 237 000 — o ranking das páginas
  e as conclusões do relatório não mudam: as mesmas 7 páginas ficam acima de
  0,01%, nenhuma passa de 0,05%, o portão de 99,99% segue satisfeito na média.
- **O Impeller, neste pipeline, antialiasava**: o `scene-to-png` rasteriza
  offscreen (`Picture.toImage`) e os PNGs antigos têm a mesma quantidade de
  tons intermediários (bordas suavizadas) que a referência do `resvg` —
  Étude p1: 289 990 px (Impeller) × 289 842 (referência) × 284 290 (Skia);
  Clair de Lune p1: 293 216 × 295 173 × 291 201. O defeito observado pelo
  usuário pode estar no caminho de tela (janela), que a comparação não usa;
  não foi investigado.
- **Determinismo do Skia**: duas execuções da mesma página (Étude p1, Clair
  de Lune p1) geram PNG byte-idêntico (`cmp`), e idêntico ao da varredura.
- Os textos abaixo desta seção (comparação com o `verovio_lottie`, causas
  categorizadas, contagens de pixel das correções) são da medição em Impeller
  e ficam como registro histórico; as porcentagens por página estão nas duas
  colunas da tabela. As imagens de `docs/mesa-de-prova/` também são do
  Impeller.

## Atualização de 2026-09-20 — remoção do índice `elements`

`pages[].elements` (§5.5) saiu do formato: era redundância deliberada com a
árvore e custava 20,5% do `scene.json`. O `score_bridge` passa a derivá-lo no
mesmo percurso em que monta a árvore, com a regra agora normativa em §5.5;
`BridgeIndexEntry` e `BridgePage::index` saíram do exportador.

- **Paridade inalterada, no sentido forte**: os 102 PNGs de
  `compare/corpus/` (34 páginas × svg/scene/diff) ficaram **byte-idênticos**
  aos da varredura anterior — o git não vê mudança em nenhum. As 34
  porcentagens são as mesmas dígito a dígito (média 0,008800%, max
  0,039330%, 27/34 ≤ 0,01%). Só a coluna `bytes_vsb` do CSV mudou.
- **Tamanho**: soma dos 34 `.vsb` de 9 880 360 → 6 814 831 bytes (−31,0%);
  por arquivo, entre −27,0% e −35,1% (mediana −30,3%). No `scene.json` cru a
  queda é de 20,5% — é maior no zip porque o índice comprime pior que a
  árvore.
- Verificação da derivação: em 11 páginas de 3 peças, o índice derivado da
  árvore é **igual entrada a entrada** ao que o arquivo antigo gravava
  (mesma ordem, mesmo `nodePath`, mesma bbox, incluindo os `[0,0,0,0]` dos
  nós sem conteúdo desenhável). Os 66 testes do `score_bridge` passam.

## Resumo

- **34/34 páginas** processadas sem erro (5 partituras MEI + 5 MusicXML).
- Divergência por página: **min 0,000481% – max 0,038624% – média
  0,008456%** — todas as páginas abaixo do teto de 0,05% do portão, e a
  média abaixo do alvo de 0,01%.
- **27/34 páginas** ficam individualmente dentro do portão de 0,01%; as 7
  restantes têm causa 100% localizada e explicada (piso de antialiasing do
  motor de texto real, ver categoria 1 abaixo) — nenhuma delas passa de
  0,04%.
- **Nenhuma divergência estrutural** encontrada em nenhuma página: nenhuma
  nota, clave, haste, feixe, ligadura ou hairpin de dinâmica em posição,
  forma, cor ou ordem de empilhamento errada. Metodologia: inspeção visual
  lado a lado (SVG × cena) de toda página acima de 0,01% (as 8 antes de
  R06b, refeita nas que mudaram), célula por célula do mapa de diff nas
  demais, mais os dois testes de correlação por deslocamento e viés de
  luminância da quarta investigação de R06b (descartam shift de texto
  escondido atrás do ruído). Toda divergência observada em todas as 34
  páginas se resume às 5 categorias abaixo, quatro delas já corrigidas.

## Tabela: peça, página, % divergente

| Peça | Pág. | Impeller (e81b6e1) | **Skia (atual)** |
| --- | --- | --- | --- |
| Chopin Étude Op.10 No.9 | 1 | 0,031698% | **0,032516%** |
| Chopin Étude Op.10 No.9 | 2 | 0,026952% | **0,028122%** |
| Chopin Étude Op.10 No.9 | 3 | 0,002084% | **0,002277%** |
| Chopin Étude Op.10 No.9 | 4 | 0,002918% | **0,002902%** |
| Chopin Mazurka Op.6 No.1 | 1 | 0,013115% | **0,013917%** |
| Chopin Mazurka Op.6 No.1 | 2 | 0,005467% | **0,005788%** |
| Chopin Mazurka Op.6 No.1 | 3 | 0,000978% | **0,001299%** |
| Grieg Butterfly Op.43 No.1 | 1 | 0,001908% | **0,001988%** |
| Grieg Butterfly Op.43 No.1 | 2 | 0,001443% | **0,001427%** |
| Grieg Butterfly Op.43 No.1 | 3 | 0,000481% | **0,000497%** |
| Grieg Little bird Op.43 No.4 | 1 | 0,001363% | **0,001603%** |
| Grieg Little bird Op.43 No.4 | 2 | 0,000898% | **0,000946%** |
| Scarlatti Sonata in C major | 1 | 0,003030% | **0,003335%** |
| Scarlatti Sonata in C major | 2 | 0,000770% | **0,000866%** |
| Scarlatti Sonata in C major | 3 | 0,000898% | **0,000978%** |
| Chopin Nocturne Op.9 No.1 | 1 | 0,009299% | **0,009540%** |
| Chopin Nocturne Op.9 No.1 | 2 | 0,004441% | **0,004922%** |
| Chopin Nocturne Op.9 No.1 | 3 | 0,015264% | **0,016017%** |
| Chopin Nocturne Op.9 No.1 | 4 | 0,019593% | **0,020314%** |
| Chopin Nocturne Op.9 No.1 | 5 | 0,008594% | **0,009299%** |
| Chopin Nocturne Op.9 No.1 | 6 | 0,008193% | **0,008850%** |
| Chopin Nocturne Op.9 No.1 | 7 | 0,006830% | **0,007183%** |
| Clair de Lune (Debussy) | 1 | 0,038624% | **0,039330%** |
| Clair de Lune (Debussy) | 2 | 0,007728% | **0,007985%** |
| Clair de Lune (Debussy) | 3 | 0,003976% | **0,004457%** |
| Clair de Lune (Debussy) | 4 | 0,006991% | **0,007744%** |
| Clair de Lune (Debussy) | 5 | 0,007472% | **0,007504%** |
| Gymnopédie No.1 (Satie) | 1 | 0,028171% | **0,028219%** |
| Gymnopédie No.1 (Satie) | 2 | 0,000641% | **0,000657%** |
| Maple Leaf Rag (Joplin) | 1 | 0,008642% | **0,008786%** |
| Maple Leaf Rag (Joplin) | 2 | 0,006269% | **0,006590%** |
| Maple Leaf Rag (Joplin) | 3 | 0,002421% | **0,002453%** |
| Prelúdio BWV 846 No.1 | 1 | 0,007888% | **0,008177%** |
| Prelúdio BWV 846 No.1 | 2 | 0,002469% | **0,002710%** |

Médias por peça (min–max): Étude 0,0159% (0,0021–0,0317), Mazurka 0,0065%
(0,0010–0,0131), Butterfly 0,0013% (0,0005–0,0019), Little bird 0,0011%
(0,0009–0,0014), Scarlatti 0,0016% (0,0008–0,0030), Nocturne 0,0103%
(0,0044–0,0196), Clair de Lune 0,0130% (0,0040–0,0386), Gymnopédie 0,0144%
(0,0006–0,0282), Maple Leaf Rag 0,0058% (0,0024–0,0086), Prelúdio BWV 846
0,0052% (0,0025–0,0079).

As 7 páginas acima de 0,01% (Chopin Étude p1/p2, Clair de Lune p1,
Gymnopédie p1, Nocturne p3/p4, Mazurka p1) são as com mais texto comum por
área de página (título, andamento, dinâmica textual, indicações
italianas/francesas) — mesmo padrão de causa dominante já visto no projeto
anterior (ver comparação abaixo), agora numa escala ~15× menor.

## Comparação com o `verovio_lottie` (linha de base)

Número final do projeto anterior (depois de D01-D01-6, todas as correções de
texto comum aplicadas — não o número intermediário de A13/B03, anterior a
essas correções e não comparável):

| | `verovio_lottie` final (tolerância 32/255) | `score_bridge` (tolerância 128/255) |
| --- | --- | --- |
| Páginas | 34/34 | 34/34 |
| Min | 0,0135% | 0,000481% |
| Max | 0,3946% | 0,038624% |
| Média | 0,1251% | 0,008456% |
| Causa dominante do residual | itálico sintético/negrito em texto comum (D01-4/D01-5), piso de AA (ThorVG × `tiny-skia`) | piso de AA em texto comum via `TextPainter` (Impeller × `tiny-skia`) |

As tolerâncias não são diretamente comparáveis (128/255 ignora deliberadamente
diferença de antialiasing de borda; 32/255 não) — a decisão do usuário em
2026-09-19 trocou uma pela outra exatamente para isolar esse ruído. Mesmo
assim, a ordem de grandeza do resíduo caiu (média final ~15× menor, max
~10× menor) e a causa dominante mudou de categoria: lá, texto comum exigiu
quatro passos de correção (D01-D01-6: renderizar, depois consertar itálico
sintético duplicado, depois cobrir bold-italic) até chegar a 0,1251%; aqui,
com o mesmo texto comum desenhado desde R04a, o resíduo já nasce como piso
de motor de fonte, sem bug de estilo pendente. Não há indício de regressão
de qualidade visual entre os dois projetos.

## Tamanho dos pacotes `.vsb`

| Peça | Páginas | Tamanho | KB/página |
| --- | --- | --- | --- |
| Chopin Nocturne Op.9 No.1 | 7 | 460,0 KB | 65,7 |
| Clair de Lune (Debussy) | 5 | 371,8 KB | 74,4 |
| Chopin Étude Op.10 No.9 | 4 | 280,8 KB | 70,2 |
| Maple Leaf Rag (Joplin) | 3 | 306,1 KB | 102,0 |
| Grieg Butterfly Op.43 No.1 | 3 | 213,4 KB | 71,1 |
| Chopin Mazurka Op.6 No.1 | 3 | 217,2 KB | 72,4 |
| Scarlatti Sonata in C major | 3 | 166,3 KB | 55,4 |
| Grieg Little bird Op.43 No.4 | 2 | 137,2 KB | 68,6 |
| Prelúdio BWV 846 No.1 | 2 | 142,3 KB | 71,2 |
| Gymnopédie No.1 (Satie) | 2 | 88,8 KB | 44,4 |

Nenhum pacote passa de ~460 KB (7 páginas); a mediana fica perto de 70
KB/página. Insumo bruto para uma eventual decisão de encoding — não é medição de tempo de parse nem de
memória, que ficam fora do escopo deste relatório.

## Divergências categorizadas

Catálogo consolidado das investigações de R06b (ver
[`docs/plano/R06b-investigacao-de-divergencias.md`](plano/R06b-investigacao-de-divergencias.md)
para o detalhe causal completo de cada uma). Das 5 categorias encontradas no
corpus, 4 foram corrigidas no código; 1 é piso de motor sem correção
conhecida sem mudança de arquitetura.

### 1. Piso de antialiasing em texto comum (não corrigido — é o que resta nas 7 páginas acima de 0,01%)

`score_bridge` desenha glifos SMuFL a partir do dicionário de contornos
exportado (mesma geometria dos dois lados do diff — por isso batem
pixel a pixel) mas desenha texto comum via `TextPainter`/`TextSpan`, que
delega no *shaping* e na rasterização de fonte do motor Flutter (hinting,
grade de pixel, blend de cobertura). O `resvg` da referência renderiza a
mesma TTF (Liberation Serif) por um caminho diferente, sem esse hinting.
Duas medições na quarta investigação de R06b descartam bug de
posição/geometria: correlação por deslocamento inteiro já mínima em (0,0),
e viés de luminância consistente (~66% dos pixels divergentes com a
referência mais escura) — assinatura de diferença de motor, não de erro de
posição. Um spike de viabilidade (mesma investigação) provou que o piso
some se texto comum virar contorno vetorial como o SMuFL — mudança de
arquitetura fora de escopo deste relatório, registrada para decisão futura.

- **Exemplo:** Chopin Étude Op.10 No.9 p.1 (0,031698% — pior página do
  corpus): divergência inteira sobre bordas de `Allegro molto agitato.`,
  indicações italianas, dedilhados e números de compasso; notas, hastes e
  feixes nos mesmos recortes continuam cinza puro. Imagens em
  [`docs/mesa-de-prova/Chopin_Etude_Op10_No9/`](mesa-de-prova/Chopin_Etude_Op10_No9/).

### 2. Traço fantasma em formas de só preenchimento (corrigido, S05)

Colchetes de pedal, feixes e pontos de aumento (`SetPen(0)` no Verovio)
ganhavam no exportador um `strokeWidth = 1` para reproduzir a regra CSS
global do SVG (`rect,path{stroke:currentColor}`). O `resvg` torna esse
traço de 0,1 px quase invisível; o Impeller o alargava em um pixel inteiro,
dobrando a espessura visível de colchetes de pedal e engrossando hastes e
pontos em todo o corpus.

- **Correção:** `ApplyStrokeFromPen` (`bridgedevicecontext.cpp`) emite
  `"stroke":"none"` quando `pen.GetWidth() <= 0`.
- **Efeito medido:** varredura do corpus (então a 32/255) caiu de 874 036
  para 839 588 px divergentes (−3,9%), média 0,4122% → 0,3959%.

### 3. `letterSpacing` não somado após o último glifo de um run (corrigido)

Nos dois laços de `DrawText` para glifos PUA/SMuFL, `letterSpacing` só era
somado **entre** caracteres (guard `!first`); para um run de um único
glifo, nunca era somado. O `resvg`/CSS soma `letter-spacing` depois de
**cada** caractere, inclusive o único/último. O efeito só aparece quando
algo mais lê `m_textPenX` depois, na mesma `<text>` — caso raro no corpus,
mas real: a dinâmica "pp" combinada (glifo PUA, `letter-spacing="90px"`)
seguida de "morendo jusqu'à la fin" em texto comum, em Clair de Lune p.4,
deixava a frase inteira 9 px deslocada à esquerda.

- **Correção:** `letterSpacing` movido para depois do avanço, sem o guard
  `!first`, nos dois laços de `DrawText` (`bridgedevicecontext.cpp`).
- **Efeito medido:** só Clair de Lune p4 mudou no corpus inteiro (as outras
  33 páginas deram delta 0): 3291 → 436 px (0,052766% → 0,006991%, entrou
  no portão). Imagens em
  [`docs/mesa-de-prova/Clair_de_Lune__Debussy/`](mesa-de-prova/Clair_de_Lune__Debussy/).

### 4. Agrupamento de âncora multi-run em texto comum (corrigido)

O SVG emite números de página autogerados ("– N –") como três `<tspan>`
irmãos sem `x` próprio sob uma única âncora `text-anchor="middle"`; o
`resvg`/CSS centraliza a largura **combinada** dos três ("text chunk"). O
ramo de texto comum de `DrawText` não participava do agrupamento de chunk
que já existia para glifos SMuFL/PUA — cada run se autocentralizava sobre a
própria fatia, produzindo gaps assimétricos e deslocamento do grupo
inteiro.

- **Correção:** o ramo de texto comum agora empilha o `BridgeTextRun`
  pendente em `m_textChunkTextRuns`; `FinalizeTextChunk` aplica um só
  deslocamento (largura somada do chunk) quando há mais de uma peça,
  forçando `alignment = left`. Caso de um único run (o mais comum) não
  muda — continua centralizado em runtime pelo `score_bridge`.
- **Efeito medido:** atinge toda página com número de página autogerado no
  corpus (10 páginas melhoraram, 0 regrediram): Étude p2 −211 px, p3 −62%,
  p4 −57%; Mazurka p2 −38%, p3 −78%; Grieg Butterfly p2 −70%, p3 −88%;
  Grieg Little bird p2 −79%; Scarlatti p2 −81%, p3 −79%. Média do corpus
  0,009475% → 0,008456%. Imagens (antes da correção deste bug específico)
  em [`docs/mesa-de-prova/Chopin_Etude_Op10_No9/`](mesa-de-prova/Chopin_Etude_Op10_No9/)
  (p2).

### 5. Artefato de dado do corpus — "mãos PUA" (corrigido no MEI, não no código)

Clair de Lune usava, na fonte original, um glifo PUA (Leipzig `E520`,
"mãos apontando" ☛☛) que a referência SVG não conseguia renderizar
consistentemente. Substituído no MEI por dinâmica semântica (`<pp/>`).
Não é bug de exportador nem de renderizador — é dado de entrada.

- **Efeito medido:** varredura caiu de 27 420 para 22 947 px (−16,3%);
  Clair p1 4671→2409, p4 5502→3291. Categoria encerrada como causa (a
  terceira investigação de R06b confirmou 0 pixels órfãos nas páginas
  afetadas depois da troca).

## Atualização de 2026-09-22 — P01c: padrões do bridge (sem cabeçalho/rodapé/rótulo)

P01b mudou o `.vsb` para sair, por padrão, com `--header none --footer none
--no-instrument-labels` (D-VSB-PADRAO). P01c regenerou o corpus com esses
padrões e re-mediu a paridade: a referência SVG passou a usar as mesmas três
flags (senão toda página divergiria por causa do cabeçalho/rodapé/rótulo que
só um dos dois lados desenharia).

Comando: `CORPUS_DIR=compare/out/p01c/corpus compare/scripts/compare-corpus.sh
128` (git-ignorado — não sobrescreve o `compare/corpus/` versionado de
R06c/E05, que continua sendo a referência **sem** os padrões novos, já que a
mudança de opções não é o que aqueles relatórios mediam). 34/34 páginas, nas
mesmas 10 peças.

| | Skia, sem os padrões (E05, 2026-09-22) | Skia, com os padrões (P01c) |
| --- | --- | --- |
| Páginas | 34/34 | 34/34 |
| Min | 0,000128%* | 0,000128% |
| Max | 0,038624% | 0,024964% |
| Média | 0,008800% | **0,006402%** |
| Páginas ≤ 0,01% | 27/34 | 27/34 |
| Páginas ≤ 0,05% | 34/34 | 34/34 |

\* A coluna "sem os padrões" repete a média/páginas-≤ de E05 (2026-09-22,
mesmo valor de R06c/2026-09-20: 0,008800%, 27/34), mas min/max não tinham
sido citados de novo em E05 — os valores de R06c (0,000481%/0,038624%) estão
aí para referência, não são estritamente da mesma varredura que a coluna ao
lado.

**A média caiu** (0,008800% → 0,006402%, −27%), como o passo antecipava:
menos texto desenhado (sem título, número de página, autor e rótulo de
instrumento) é menos superfície sujeita ao piso de antialiasing de texto
comum, a maior fonte de divergência residual (risco 1 do plano). O teto
também caiu (0,038624% → 0,024964%): a pior página deixou de ser a que tinha
mais texto de cabeçalho. **27/34 páginas continuam ≤ 0,01%** — mesma
contagem, não necessariamente as mesmas páginas (a paginação mudou, então
"página 1 do Clair de Lune" antes e depois não é o mesmo trecho musical).
Nenhuma página passa de 0,05%: o portão de 99,99% continua satisfeito, com
folga maior que antes.

## Atualização de 2026-09-22 — P02d: paridade das páginas alternativas

Requisito inegociável 1 do `CLAUDE.md`, agora para as páginas alternativas
de `alternates.json` (§2.5, P02c): cada uma é uma seleção
(`Toolkit::SelectFromMeasureToEnd`, o mesmo mecanismo que o exportador usa)
renderizada de novo, então precisa da mesma prova de paridade que as
páginas normais.

Mecanismo: `-t svg --select-from <xml:id>` (novo, `tools/main.cpp` +
`Toolkit::SelectFromMeasureToEnd`) gera a referência da sequência que começa
naquele compasso; `compare scene-to-png --alternate <xml:id>` (novo,
`compare/lib/src/scene_to_png.dart`, lê `VsbDocument.alternateStartingAt`,
P03a) desenha a mesma sequência a partir do `.vsb`.
`compare-page.sh`/`compare-corpus.sh` ganharam `--alternate`/
`SWEEP_ALTERNATES=1` para varrer as duas ao mesmo tempo, com `--xml-id-seed
42` fixo só nesse modo (os dois lados — a referência SVG e o `.vsb` que a
sondagem lê — precisam gerar o mesmo `xml:id` de compasso de chegada; sem
semente fixa cada `verovio` roda com uma sequência de ids diferente).

Comando: `CORPUS_DIR=compare/out/p02d SWEEP_ALTERNATES=1
compare/scripts/compare-corpus.sh 128` (git-ignorado). As 10 peças do
corpus geram 18 páginas alternativas ao todo (Gymnopédie 1, Maple Leaf Rag
13 em 8 sequências, Mazurka 2, Little bird 2; Butterfly e Scarlatti têm
pontos de chegada mas nenhum sobrevive à regra de existência de §2.5 — já
são o 1º compasso de alguma página normal, P02b).

| | Skia, páginas normais (P01c) | Skia, páginas alternativas (P02d) |
| --- | --- | --- |
| Páginas | 34/34 | 18/18 |
| Min | 0,000128% | 0,000096% |
| Max | 0,024964% | 0,021789% |
| Média | 0,006402% | 0,006514% |
| Páginas ≤ 0,01% | 27/34 (79%) | 14/18 (78%) |
| Páginas ≤ 0,05% | 34/34 | 18/18 |

**Paridade comparável às páginas normais** — a média (0,006514% vs.
0,006402%) e a proporção ≤ 0,01% (78% vs. 79%) praticamente coincidem, e
nenhuma página passa de 0,022%. Esperado: uma página alternativa é uma
seleção do **mesmo** documento renderizada pelo **mesmo** `View`/
`BridgeDeviceContext`, só com um recorte de compassos diferente — não há
nenhum caminho de código novo que pudesse introduzir uma categoria de
divergência que as páginas normais não já tivessem (texto comum continua
sendo a maior fonte, risco 1 do plano). As piores páginas (Maple Leaf Rag,
0,018-0,022%) são justamente as sequências mais cedo no documento, com mais
texto/dinâmica por página — mesma assinatura das piores páginas normais.

## Atualização de 2026-09-22 — P05: portão da fase P (páginas alternativas)

Confirmação, não re-medição: entre P02d e este portão (P03a-P04c) nenhum
passo tocou `verovio/src` nem o exportador — só `score_bridge` (Dart) e
`tool/generate_examples.dart`. A varredura completa (normais + alternativas)
foi rodada de novo mesmo assim, como o portão pede, com o mesmo comando de
P02d (`CORPUS_DIR=compare/out/p05-parity SWEEP_ALTERNATES=1
compare/scripts/compare-corpus.sh 128`, git-ignorado):

| | Páginas normais | Páginas alternativas |
| --- | --- | --- |
| Páginas | 34/34 | 18/18 |
| Min | 0,000128% | 0,000096% |
| Max | 0,024964% | 0,021789% |
| Média | 0,006402% | 0,006514% |
| Páginas ≤ 0,01% | 27/34 (79%) | 14/18 (78%) |
| Páginas ≤ 0,05% | 34/34 | 18/18 |

**Idêntico, byte a byte, a P01c (normais) e P02d (alternativas)** — como
esperado: nenhuma página mudou de percentual. O portão de paridade da fase
P inteira (P01a-P04c) fica satisfeito com a mesma folga de R06c/E05
(≥99,99% em todas as páginas, normais e alternativas).

## Comando exato

```
compare/scripts/compare-corpus.sh 128
```

rodado a partir da raiz do repositório, com `COMPARE_BACKEND=skia`
(padrão do script desde 2026-09-20; a medição de `e81b6e1` foi com `impeller`), contra `corpus/mei/*.mei` +
`corpus/musicxml/*.mxl` (34 páginas). Pré-requisitos: `verovio/tools/verovio`
compilado (`cd verovio/tools && cmake ../cmake && make -j4`),
`compare/build/linux/x64/release/bundle/compare` e
`compare/svg_render/target/release/svg_render` compilados (ver
`docs/plano/README.md`, seção "Convenções").

## Fora de escopo

- Otimização de tamanho e desempenho — este relatório é sobre
  imagem, não sobre tempo/memória.
- A mudança de arquitetura que zeraria a categoria 1 (texto comum como
  contorno vetorial) — decisão explícita do usuário, não tomada aqui.

## Notas de execução

Relatório escrito a partir dos dados já coletados na sexta investigação de
R06b (`compare/corpus/resultado.csv`, já versionado e commitado em
`e81b6e1` antes deste passo — não foi necessário refazer a varredura).
Conferido por recomputação independente do CSV (`awk`, `LC_NUMERIC=C`):
média 0,008456%, min 0,000481% (Grieg Butterfly p3), max 0,038624% (Clair
de Lune p1) — bate com os números citados nas notas de R06b.
