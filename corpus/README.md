# corpus

Partituras de piano solo, completas, usadas como material de teste para o
exportador dotLottie deste projeto (ver `docs/descricao-do-projeto.md`). Toda
obra musical aqui é de domínio público (compositores falecidos há mais de um
século); o que muda de arquivo para arquivo é a licença da *codificação*
digital (MEI/MusicXML), documentada abaixo.

## `mei/` — fonte: [music-encoding/sample-encodings](https://github.com/music-encoding/sample-encodings)

Licença do repositório: **ECL-2.0** (Educational Community License, baseada na
Apache 2.0 — permite redistribuição). Arquivos em
`MEI_4.0/Music/Complete_examples/`:

| Arquivo | Peça |
| --- | --- |
| `Chopin_Etude_Op10_No9.mei` | Chopin — Étude Op. 10 No. 9 |
| `Chopin_Mazurka_Op6_No1.mei` | Chopin — Mazurka Op. 6 No. 1 |
| `Grieg_Butterfly_Op43_No1.mei` | Grieg — "Butterfly", Lyric Pieces Op. 43 No. 1 |
| `Grieg_Little_bird_Op43_No4.mei` | Grieg — "Little Bird", Lyric Pieces Op. 43 No. 4 |
| `Scarlatti_Sonata_in_C-major.mei` | D. Scarlatti — Sonata em Dó maior |

## `musicxml/` — fonte: [musetrainer/library](https://github.com/musetrainer/library)

Biblioteca de arquivos MusicXML de domínio público mantida pelo projeto
MuseTrainer (curadoria de partituras originalmente publicadas no
MuseScore.com). O repositório não traz um arquivo de licença formal; as obras
em si são de domínio público e as transcrições selecionadas aqui são
mecânicas (sem arranjo/adaptação autoral). Arquivos em `scores/` (formato
`.mxl`, MusicXML comprimido):

| Arquivo | Peça |
| --- | --- |
| `Clair_de_Lune__Debussy.mxl` | Debussy — Clair de Lune (Suite bergamasque) |
| `Erik_Satie_-_Gymnopedie_No.1.mxl` | Satie — Gymnopédie No. 1 |
| `Maple_Leaf_Rag_Scott_Joplin.mxl` | Joplin — Maple Leaf Rag |
| `Prelude_I_in_C_major_BWV_846_-_Well_Tempered_Clavier_First_Book.mxl` | J.S. Bach — Prelúdio I em Dó maior, BWV 846 (O Cravo Bem Temperado, Livro I) |
| `Chopin_-_Nocturne_Op._9_No._1.mxl` | Chopin — Nocturne Op. 9 No. 1 |

## Uso

Exemplo de renderização de um arquivo MEI com o Verovio já compilado neste
repositório:

```sh
verovio/tools/verovio -f mei -t svg corpus/mei/Chopin_Etude_Op10_No9.mei \
  -o /tmp/saida.svg --resource-path verovio/data
```

Para MusicXML, use `-f musicxml` (ou deixe o Verovio detectar automaticamente
pela extensão).

## `fantasma/` — partituras mínimas da nota fantasma (G04c)

Oito partituras MEI escritas à mão para este projeto (sem restrição de licença),
cada uma exercitando um caso que o corpus real não cobre, para `pitchpos.json`
(§2.8) e para a nota fantasma (§10). `esperado.json` traz, por id, os campos de
`pitchpos.json` que o teste confere — valores escritos pela teoria musical, não
copiados da saída do exportador (`compare/scripts/g04c-fantasma-check.py`).

| Arquivo | Caso |
| --- | --- |
| `f01-clave-no-meio.mei` | clave de Sol → clave de Fá no meio do compasso |
| `f02-oitavas.mei` | 8va e 8vb (`<octave>`) |
| `f03-transpositor.mei` | clarinete em Si♭ (`trans.semi="-2"`), armadura de ré maior escrita |
| `f04-cross-staff.mei` | notas da mão esquerda escritas na pauta de cima e vice-versa (`@staff`) |
| `f05-armadura-nao-padrao.mei` | `<keySig>` com `<keyAccid>` (só fá♯ e si♭) |
| `f06-mudanca-armadura.mei` | dó → 3♯ (compasso 3) → 3♭ (compasso 5) no meio do sistema |
| `f07-acidentes.mei` | ♯, ♮ e ♯♯ escritos numa camada e lidos noutra da mesma pauta; acidente em vigor no compasso seguinte |
| `f08-pausas.mei` | `rest` e `mRest` em duas pautas |

Nas fixtures que dependem da armadura no som, as notas alteradas trazem
`accid.ges` (o Verovio não aplica a armadura ao MIDI; os importadores fazem isso
gravando `accid.ges`).

## `ligaduras/` — cadeias de ligadura do `midi.json`

Partituras mínimas escritas à mão para este projeto (sem restrição de
licença), para o campo `tied` de `midi.json` (§2.7). O `.esperado.json` ao lado
traz, por id da cabeça, a cadeia esperada; confere-se com
`compare/scripts/verify-tied-chains.py <peça.vsb> <esperado.json>`.

| Arquivo | Caso |
| --- | --- |
| `l01-entre-camadas-e-casas.musicxml` | ligadura que troca de camada na barra de compasso; ligadura para dentro da casa 1 e da casa 2 (na 2ª passagem a cadeia vai para a casa 2, uma delas trocando de camada) |
