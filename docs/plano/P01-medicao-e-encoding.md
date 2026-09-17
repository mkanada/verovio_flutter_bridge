# P01 — Medição (tamanho, parse, frame) e gate de encoding binário

**Depende de:** R06, A02 · **Decisão necessária:** SIM (D-BIN) — e **em duas
etapas**: primeiro levar os números ao usuário, e só depois, se ele disser que
vale, decidir a técnica

## Objetivo

Medir o custo real do formato JSON com o pipeline completo funcionando e
decidir, **com números na mão**, se vale trocar por um encoding binário. O
projeto anterior tem um precedente: o passo de tamanho (D06) ficou bloqueado
por meses justamente porque a decisão foi tentada sem medição.

## Ler antes (só isto)

- Notas de execução de S07 (tamanhos por peça), R01 (tempo de parse) e A01/A02
  (tempo de compilação e de repaint).
- `../verovio_lottie/docs/plano/D06-tamanho-do-arquivo.md`, seção "Passo 0" — o
  método de decidir com o usuário, que continua valendo. (O **conteúdo**
  técnico de lá não vale mais: o conflito precomp × slot de cor não existe
  aqui.)

## O que fazer

1. Medir, para as 10 peças do corpus, e montar uma tabela única:
   - tamanho do `.vsb`, do `scene.json` cru e do `glyphs.json` cru;
   - proporção glifos/cena/timemap dentro do pacote;
   - tempo de parse no Dart (mediana de 5, em desktop **e** num dispositivo
     Android, se houver um disponível — senão registre que faltou);
   - tempo de compilação dos `Picture`s por página;
   - memória residente do documento carregado (`ProcessInfo.currentRss` antes e
     depois).
2. Medir também **uma peça grande** fora do corpus (20+ páginas — sinfonia ou
   sonata completa em MEI de domínio público). O corpus tem 5-16 compassos por
   peça e não representa o pior caso.
3. Levar a tabela ao usuário com uma pergunta objetiva: *o tempo de abertura e
   o tamanho são um problema para o zywny?* — e registrar a resposta.
4. Se a resposta for "está bom": o passo **termina aqui**, com os números
   documentados em `docs/medicoes.md`. Não implemente nada.
5. Se for "reduzir": só então discutir a técnica, nesta ordem de custo/benefício
   (proponha, não escolha sozinho):
   a. comprimir melhor o que já existe (o zip já deflaciona; medir `-9`);
   b. reduzir precisão numérica (menos dígitos significativos) — medir impacto
      na paridade antes;
   c. CBOR/MessagePack (troca o parser, mantém o modelo);
   d. FlatBuffers (schema compartilhado, parse zero-copy).

## Fora de escopo

- Implementar qualquer encoding novo sem a decisão registrada.
- Otimizar render (P03).

## Critérios de aceite

1. `docs/medicoes.md` com a tabela completa (as 10 peças + a peça grande) e o
   comando que gerou cada número.
2. A pergunta foi feita ao usuário e a resposta está registrada no documento,
   com data.
3. A decisão D-BIN está marcada como resolvida na tabela do
   [README do plano](README.md).
4. Se a decisão for implementar algo: o critério de aceite passa a incluir
   **paridade inalterada** — rodar R06 de novo e obter as mesmas médias
   (margem desprezível), porque mexer em precisão numérica é a forma mais fácil
   de quebrar a paridade sem perceber.

## Notas de execução

(a preencher por quem executar)
