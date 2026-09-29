# G04a — Especificação: `pitchpos.json`, pauta na cena e fórmula da fantasma

**Depende de:** — · **Decisão necessária:** não (todas as decisões estão em
[`G03`](G03-visao-geral-nota-fantasma.md), tomadas em 2026-09-29)

## Objetivo

Escrever, em `docs/formato/especificacao-v1.md`, o contrato que G04b/G04c
implementam e que o `zywny` lê: o arquivo novo `pitchpos.json`, os campos
novos do nó `staff` da cena, os glifos reservados e a **fórmula normativa**
da nota fantasma (tecla MIDI → posição, acidente, linhas suplementares,
marcador de oitava). Atualizar `schema-v1.json` e os exemplos.

## Ler antes (só isto)

- [`G03`](G03-visao-geral-nota-fantasma.md) inteiro (decisões e regras).
- `docs/formato/especificacao-v1.md`: §2 e §2.1 (manifest, regra de
  omissão), §2.4 (timemap, regra do sufixo `-rend<N>`), §2.7 (`midi.json`, o
  modelo de seção mais recente), §4 (glifos), §5.1 (nó), §9
  (compatibilidade) e o "Histórico de revisões".
- `docs/formato/schema-v1.json`.

## Contexto que você precisa

- **Por que um arquivo novo e não campos no `midi.json`:** `midi.json` é "o
  que soa" (ids expandidos, uma entrada por evento MIDI); o contexto de
  notação é "como está escrito" (ids notados, inclui pausas, que não soam).
- **Por que a geometria vai no nó `staff` da cena e não no `pitchpos.json`:**
  ela depende do layout. As páginas alternativas (§2.5) são outro layout do
  mesmo `Doc`, e o nó `staff` de cada página já sai do mesmo
  `BridgeDeviceContext` — a fantasma funciona nas duas sem dado duplicado.
- **Fatos medidos** (`erik-satie.vsb`, 1ª pauta da página 1): as 5 linhas
  são os 5 primeiros filhos `p` do nó `staff` (y = 808, 988, 1168, 1348,
  1528; espessura 13), sem id nem classe — hoje não há como o leitor saber
  que são linhas de pauta sem heurística. Linha suplementar: grupo
  `ledgerLines below`, espessura 22, de x = 2581 a 2903 para uma cabeça de
  x = 2629 a 2855 (extensão ≈ 48 de cada lado). Cabeça preta `E0A4` com
  `sx = sy = 0.72`. O dicionário do Satie **não** tem `E260` (bemol): hoje
  a fantasma não conseguiria desenhar ♭ nessa peça.
- Unidade vertical e fórmula de `loc`: ver G03, § Regras.

## O que fazer

1. **§2.8 `pitchpos.json`** (novo, opcional, aditivo; omitido junto com a
   entrada do manifest quando não há nenhum evento). Proposta de forma —
   ajuste nomes de chave se precisar, mas mantenha a semântica:

   ```json
   {
     "events": {
       "orw55dt": { "t": "n", "co": 2, "sh": 0, "key": {"f": 1, "c": 1},
                    "acc": {"g4": 1}, "pn": "d", "o": 4, "alt": 0, "loc": -3 },
       "j97m9qh": { "t": "r", "co": 2, "sh": 0, "key": {"f": 1, "c": 1} }
     }
   }
   ```

   - chave = `xml:id` **notado** de nota ou pausa (inclui `mRest`); o leitor
     chega de um id expandido pelo `sceneIdOf` (§2.4).
   - `t`: `"n"` (nota) ou `"r"` (pausa).
   - `co`: `clefLocOffset` da clave vigente **na pauta onde o elemento é
     desenhado** (cross-staff incluído).
   - `sh` (opcional, padrão 0): semitons som − escrita (transposição +
     8va/8vb vigentes), o mesmo que `GetMIDIPitch` soma.
   - `key` (opcional, padrão `{}`): alteração da armadura vigente por nome
     de nota (−2…+2), inclusive armaduras não padronizadas (`keyAccid`).
   - `acc` (opcional, padrão `{}`): alteração em vigor por `pname`+`oct`
     vinda de acidentes **escritos antes** deste elemento no mesmo compasso
     e pauta (0 = bequadro escrito).
   - Só nota: `pn`/`o` (altura escrita), `alt` (alteração efetiva: `accid`,
     senão `accid.ges`, senão a em vigor), `loc` (o `loc` que o Verovio
     usou para desenhar — cobre notas com `@loc` explícito).
2. **§5.1, campos novos em nós** (aditivos):
   - nó `staff`: `lines: [topY, unit, n]` (y da linha de cima no referencial
     de conteúdo, meio-espaço, número de linhas); `ledger: [espessura,
     extensão]` (para o tamanho normal e, se diferente, `ledgerCue`);
     `gs`: escala `sx` de um glifo de tamanho normal nessa pauta.
   - nó de nota/acorde/pausa **cross-staff**: `staff: "<id do nó staff>"`
     onde é desenhado (ausente = pauta ancestral).
3. **§4, glifos reservados**: o dicionário traz sempre, da fonte da peça,
   `E0A4` (cabeça preta), `E260`/`E261`/`E262` (♭/♮/♯), `E511`/`E512`
   (8va/8vb) e `E515`/`E516` (15ma/15mb), mesmo sem instância `u`.
4. **§2.4, timemap:** documentar `restsOn`/`restsOff` (D-FANT-PAUSA-TEMPO),
   com a mesma regra de ids expandidos de `on`/`off`.
5. **§10 (novo) "Nota fantasma" — normativo**: os 8 passos de G03 § Regras,
   escritos como algoritmo, com: fórmula de `loc` e de y; grafia (tecla
   branca/preta, armadura, sentido do erro sem armadura, desempate de
   proximidade: a de cima); alcance (> 4 linhas suplementares → ∓7 por
   oitava, marcadores); acidente (alteração em vigor = `acc`, senão `key`;
   desenha se diferente); x e deslocamento de colisão (≤ 1 `loc` de uma
   cabeça real **do mesmo instante e pauta** ou de outra fantasma → +
   largura da cabeça); posição do acidente (à esquerda da cabeça, folga a
   medir em G04d — deixe um valor provisório marcado como tal); linhas
   suplementares (x de `cabeça − extensão` a `cabeça + largura +
   extensão`); marcador de oitava (centralizado na cabeça, acima para 8va,
   abaixo para 8vb, livre das linhas suplementares). Inclua 3 exemplos
   trabalhados com números do Satie.
6. `schema-v1.json`, `exemplo-minimo.json` (se couber) e o histórico de
   revisões.

## Fora de escopo

- Implementar qualquer coisa (G04b/G04c). Lado Dart (G05/`zywny`).
- Parâmetros visuais do host (cor, fade, tempo mínimo na tela).

## Critérios de aceite

1. A especificação descreve `pitchpos.json`, os campos de nó, os glifos
   reservados, `restsOn`/`restsOff` e a §10 normativa; o histórico ganha a
   linha de 2026-09-xx.
2. Um `docs/formato/exemplo-pitchpos.json` novo (o exemplo da §2.8) valida
   contra o schema, com o mesmo validador de S01/P02a:
   `check-jsonschema --schemafile docs/formato/schema-v1.json
   docs/formato/exemplo-pitchpos.json`; `exemplo-minimo.json` continua
   validando.
3. Os 3 exemplos trabalhados da §10 batem, conta a conta, com a cena real
   do Satie (registre de onde saiu cada número).

## Notas de execução

_(vazio)_
