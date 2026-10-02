# Nota do `zywny` — ligadura que troca de camada some do `tied`

Escrita em 2026-10-01, a partir de uma investigação feita no `zywny`. É um
pedido de correção **neste repositório** (C++, gravador de G01). Nada precisa
mudar no formato nem no lado Dart.

## 1. Sintoma

No hino 10 do `zywny`, compasso `3i` (3º da introdução), clave de fá: o sol
grave (G2) da última colcheia está ligado ao sol do compasso `4i`. A linha da
ligadura é desenhada, mas no destaque a nota de continuação não acende junto
com a cabeça. O som está certo (a cabeça soa até o fim da cadeia).

## 2. Causa

O `midi.json` sai sem `tied` na cabeça quando a continuação está em **outra
camada** (`<layer>`) da mesma pauta.

- `GenerateMIDIFunctor::VisitNote` (`verovio/src/midifunctor.cpp:838-841`)
  pula a nota secundária e chama `LogTiedContinuation(pitch, id)`.
- `LogTiedContinuation` (`midifunctor.cpp:1238`) procura a cabeça em
  `m_openTieHeadEvent` (`include/vrv/midifunctor.h:551-554`), um mapa
  `pitch → índice do evento` que é **membro da instância do functor**.
- `Doc::ExportMIDI` cria uma instância por par pauta+camada
  (`verovio/src/doc.cpp:616-625`) e cada uma percorre a peça inteira sozinha.

Então a continuação na camada 2 nunca enxerga a cabeça aberta na camada 1, e
o id é descartado. A duração não é afetada porque vem de
`InitTimemapTiesFunctor::VisitTie` (`midifunctor.cpp:313`), que segue
`Tie::GetStart/GetEnd` e não depende de camada.

Isso é a limitação já registrada nas notas de execução de G01 ("chave só por
pitch, já que uma instância do functor processa uma pauta+camada fixas"). O
corpus de lá não tinha ligadura entre camadas; os hinos têm muitas.

## 3. Reprodução

Entrada: `/home/mauricio/IdeaProjects/zywny/assets/hinos/010.musicxml.gz`
(descompactar com `zcat`). Com `--xml-id-seed 1`:

```sh
cd verovio
zcat /home/mauricio/IdeaProjects/zywny/assets/hinos/010.musicxml.gz > /tmp/010.musicxml
./tools/verovio -r data -x 1 -t mei --all-pages -o /tmp/010.mei /tmp/010.musicxml
./tools/verovio -r data -x 1 -t vsb -o /tmp/010.vsb /tmp/010.musicxml
unzip -o /tmp/010.vsb midi.json -d /tmp/010
```

As cinco ligaduras da barra `3i` → `4i` (os `<tie>` estão no fim do compasso
`3i` do MEI):

| Nota | Pauta | Camada (início → fim) | Id da continuação | No `tied` da cabeça? |
| --- | --- | --- | --- | --- |
| B3 | 1 | 1 → 2 | `cg7y08o` | não |
| D4 | 1 | 1 → 2 | `efwg9mm` | não |
| G4 | 1 | 1 → 1 | `au36i87` | sim |
| G2 | 2 | 1 → 2 | `yvc8ap1` | não |
| D3 | 2 | 1 → 1 | `q1c11nce` | sim |

No hino 10 inteiro: 47 `<tie>` no MEI, 19 trocam de camada. Nenhuma das 19
aparece em `tied`.

## 4. Alcance

Contagem aproximada direto nos MusicXML dos 600 hinos (comparando `<voice>` da
nota que abre com a da nota que fecha): cerca de 956 ligaduras de 8 390 trocam
de voz, em 169 hinos. É o padrão comum de hinário: a voz que segura a nota
muda de camada na barra de compasso enquanto a outra se move.

## 5. O que o `zywny` espera

O contrato de §2.7 de `docs/formato/especificacao-v1.md` não muda: `tied`
lista os ids de **todas** as continuações da cadeia, na ordem, seja qual for a
camada (ou pauta) em que estejam. O evento continua pertencendo à cabeça, com
`s`/`l` da cabeça.

Do lado Dart nada precisa mudar: `mergeTiedEntries` (`score_player.dart`) e o
treino (`PracticeController._chainOf`) só leem `MidiNote.tied`.

## 6. Sugestão de correção

Montar a cadeia pelo próprio elemento de ligadura, que é a alternativa 1 do
documento de G01 ("percorrer `Tie::GetStart/GetEnd` a partir da nota"), em vez
da busca por pitch dentro da camada.

Só trocar o mapa por um compartilhado entre instâncias **não** resolve: cada
camada percorre a peça inteira antes da próxima começar, então "cabeça aberta
agora" não tem sentido entre camadas. Duas formas que funcionam:

1. Um passo antes do export (ou dentro de `InitTimemapTiesFunctor::VisitTie`,
   que já visita todo `<tie>`) grava `id da nota inicial → id da nota final`;
   ao gravar o evento da cabeça, seguir esse mapa até o fim da cadeia.
2. Pós-processar o `MIDIEventLog`: gravar as continuações puladas e ligá-las às
   cabeças pelo mapa de (1), depois de todas as camadas terem rodado.

## 7. Casos para não quebrar

- **Cadeia de 3+ notas** (Gymnopédie, `e11eog5` → 3 continuações): continua
  saindo inteira e em ordem, inclusive se um elo do meio trocar de camada.
- **Repetição expandida** (ids `-rend<N>`): as continuações de uma cabeça
  `-rendN` têm de sair com o id da mesma passagem.
- **Casas de repetição** — comportamento atual que achei no mesmo hino e que
  vale decidir de propósito. Compasso 23 → casa 1 (compasso 24) e casa 2
  (compasso 25). No MEI os `<tie>` do compasso 23 apontam só para o compasso
  24. Na 2ª passagem, o Verovio avisa
  `Time spanning element 'tie' with @xml:id 'gxnlfkm-rend2' could not be set as running`,
  e hoje a busca por pitch acaba ligando a cabeça ao compasso 25:

  | Cabeça (compasso 23) | 1ª passagem | 2ª passagem (`-rend2`) |
  | --- | --- | --- |
  | D3 `f6qyds7`, pauta 2 | `tied: [smbmxxz]` (c. 24) | `tied: [rhrwvig]` (c. 25) |
  | G2 `cp4eor`, pauta 2 | sem `tied` (troca de camada) | `tied: [p1sbx3el]` (c. 25) |
  | B3 `o1rv1vjs`, pauta 1 | sem `tied` (troca de camada) | `tied: [mfso6zn]` (c. 25) |

  Musicalmente o resultado da 2ª passagem parece o desejado (a nota entra
  ligada na casa 2), mas ele sai por coincidência de pitch, não pelo `<tie>`.
  Uma correção baseada só em `Tie::GetStart/GetEnd` perderia esses três. Não
  investiguei se o `off` da cabeça nessa passagem está certo.
- **Ornamento expandido**: segue sem `tied` (§2.7).
- **Entrada velha no mapa**: `m_openTieHeadEvent` nunca é limpo, então uma
  continuação sem cabeça pode grudar numa cabeça antiga de mesmo pitch. Se o
  mapa por pitch sobreviver como reserva (para o caso das casas), vale fechar
  a entrada quando a cadeia termina.

## 8. Critérios de aceite sugeridos

1. Hino 10, seed 1: as cinco cabeças da tabela da seção 3 saem com `tied`
   contendo o id da continuação.
2. Hino 10 inteiro: toda nota final de um `<tie>` do MEI aparece em `tied` da
   cabeça da cadeia, em todas as passagens.
3. Corpus atual: `midi.json` idêntico ao de antes nas peças sem ligadura entre
   camadas; `compare/scripts/verify-midi-json.py` continua passando.
4. `scene.json`, `glyphs.json`, `timemap.json` e o `.mid` não mudam.
5. O caso das casas de repetição (seção 7) fica com comportamento decidido e
   anotado.

Vale incluir o hino 10 (ou um recorte dos compassos `3i`-`4i` e 23-25) no
`corpus/` como fixture de ligadura entre camadas.

## 9. Depois da correção

Avisar o `zywny` para recompilar a `libverovio.so`
(`tool/build_verovio_linux.sh` e o equivalente Android) e regenerar as
fixtures `.vsb` de teste. Os hinos são renderizados em runtime a partir do
MusicXML, então não há asset pré-gerado para refazer.

## 10. Resolução (2026-10-01)

Corrigido neste repositório, pela forma 2 da seção 6: `VisitNote` grava as
continuações puladas e `MIDIEventLog::ResolveTies` (`midifunctor.cpp`),
chamado por `Doc::ExportMIDI` depois de todas as camadas, monta as cadeias a
partir dos `<tie>`. O mapa por pitch (`m_openTieHeadEvent`) saiu de vez.
Detalhes e medições em `docs/plano/G01-gravador-de-notas-midi.md` ("Revisão de
2026-10-01"); o texto de `tied` em §2.7 da spec ganhou as duas garantias novas.

Critérios da seção 8:

1. Atendido: as cinco cabeças da tabela da seção 3 saem com a continuação.
2. Atendido: as notas finais dos 47 `<tie>` aparecem em `tied`, nas duas
   passagens (66 cabeças com `tied`, antes 44).
3. `midi.json` idêntico em 8 das 10 peças do corpus e nas 13 de
   `corpus/repeticoes`. Mazurka (+9 cabeças) e Clair de Lune (+4) mudam porque
   **têm** ligadura entre camadas; no Clair de Lune sai também um caso de
   "entrada velha no mapa" (`trajyh1` deixou a cabeça do compasso 17 e foi
   para a do compasso 55). `verify-midi-json.py` dá o mesmo veredito de antes
   em todas, com menos divergências de relógio (as que vinham de `tied`
   faltando somem: hino 10 de 25 para 3, Mazurka de 9 para 0, Clair de Lune
   de 4 para 0).
4. Atendido: `scene.json`, `glyphs.json`, `timemap.json` e o `.mid` não mudam.
5. **Casas de repetição — decidido assim:** na última passagem a cabeça do
   compasso 23 lista a nota ligada da casa 2, agora por regra e não por
   coincidência de pitch: o `<tie>` clonado aponta para a casa 1, que não é
   tocada em seguida, então a cabeça fica aberta e recebe a continuação órfã
   de mesma pauta e pitch tocada logo depois. Vale também quando essa nota
   troca de camada.

   | Cabeça (compasso 23) | 1ª passagem | 2ª passagem (`-rend2`) |
   | --- | --- | --- |
   | D3 `f6qyds7` | `[smbmxxz]` | `[rhrwvig]` |
   | G2 `cp4eor` | `[c1p8ut94]` | `[p1sbx3el]` |
   | B3 `o1rv1vjs` | `[s1yjngzk]` | `[mfso6zn]` |
   | D4 `unhgns7` | `[u1lyqnqu]` | `[o12g1foe]` |
   | G4 `wo0766` | `[p16n97vn]` | `[p921wzv]` |

Fixture: `corpus/ligaduras/l01-entre-camadas-e-casas.musicxml` (recorte
sintético dos dois casos, não o hino), conferida por
`compare/scripts/verify-tied-chains.py`.

**Fica em aberto** o `off` nas casas, que a seção 7 não tinha investigado: ele
está errado e não foi mexido, porque vem do cálculo de duração do Verovio
(`InitTimemapTiesFunctor::VisitTie`) e corrigir muda o `.mid`. No hino 10, 2ª
passagem, a cabeça soma a duração da nota da casa 1 em vez da da casa 2 (D3
`f6qyds7-rend2` termina em 144 583 ms, a casa 2 vai até 146 667 ms), e as três
notas da casa 1 que abrem ligadura para a casa 2 (`y12st8y`, `vggswj3`,
`x1f8teoh`) soam 3 333 ms além do fim da casa 1, por cima da repetição.

Só vale para ligadura que o MusicXML escreve dos dois lados: se a casa 2 tem
`<tie type="stop">` sem um `start` correspondente na casa 1, o importador do
Verovio descarta a ligadura e a nota da casa 2 é tocada de novo, com evento
próprio.
