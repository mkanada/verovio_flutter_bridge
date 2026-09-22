# Nota para o `zywny` — fase E (repetições)

Fechada em 2026-09-22. Não muda nada no `zywny`; é só o que a fase E dá de
novo para o host usar, e o que continua fora.

## O que o host ganha

- **A partitura toca a repetição inteira**, incluindo peças MEI com várias
  `<section>`/`<ending>` (ritornelo, casas) e MusicXML com casa 1 marcada sem
  casa 2 escrita — antes disso, essas peças tocavam sem repetir nenhum
  trecho, sem nenhum aviso.
- **`ScoreController`/`ScoreGeometry`/`ScoreView` aceitam ids expandidos**
  (`abc-rend2`, do timemap) em qualquer método que recebe um `id`: resolvem
  sozinhos ao `xml:id` da cena. O host pode continuar usando os mesmos ids
  do timemap para colorir/animar/rolar até um elemento, mesmo durante uma
  repetição.
- **`MeasureInfo.pass`** (em `ScoreTimeline.measures`/`ScorePlayer.measures`):
  `1` na primeira vez que aquele compasso toca, `2` na segunda, etc. — dá
  para o host mostrar "2ª vez" ou destacar visualmente qual passagem está
  tocando.
- **`ScorePlayer.seekToElement(id, {pass})`**: toca a partir de um compasso,
  nota ou id expandido, mesmo que ele apareça mais de uma vez na peça. Sem
  `pass:`, escolhe a mesma passagem em que a música já está (ou a 1ª, se
  aquele elemento não tocar na passagem atual); com `pass:` explícito, vai
  direto para aquela execução. Uso típico:
  `ScorePageView(onElementTap: (id) => player.seekToElement(id))`.
- **A vista acompanha corretamente durante e depois de qualquer salto de
  repetição** — inclusive voltando para uma página anterior, ou saindo da
  última página. Em `pagedSweep`, o salto tem a mesma haste das viradas
  normais, com a página de destino atrás dela.

## O que continua fora (não implementado)

- **Modo "tocar sem repetições"**: não existe. `--expand-never` (opção do
  Verovio) não serve — ele toca a ordem notada com as duas casas, o que não
  é "sem repetição". Um modo assim precisaria de uma segunda expansão
  (gerar o timemap a partir de uma cópia sem repetir), fora do escopo desta
  fase.
- **D.C./D.S./coda/fine em MEI** (`repeatMark@func`): o corpus não tem
  nenhum caso, e não foi implementado. MusicXML já suporta esses saltos (fase
  anterior ao E, sem mudança aqui).
- **Casas com mais de dois números por grupo** (ex.: `<ending number="1,2">`
  numa casa só) e **repetição aninhada** (uma repetição inteira dentro de
  outra): nenhum caso no corpus; comportamento não verificado.
