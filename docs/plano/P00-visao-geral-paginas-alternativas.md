# P00 — Visão geral da fase P: páginas alternativas do player

**Não é um passo executável.** É o documento de referência da fase P: leia
este arquivo inteiro antes de executar **qualquer** passo `P*`. Cada passo
repete o que precisa, mas as regras abaixo são o contrato comum.

## O problema

Numa repetição cujo salto muda de página, a vista de hoje (E03a/E03b,
D-SALTO = haste generalizada) volta para a **página original** de destino. O
compasso de chegada pode estar no meio dela, e o leitor precisa procurá-lo.

O que o usuário quer: a música é apresentada normalmente até o salto. No
salto, a vista **não** volta para a página original. Ela vai para uma página
**nova, redesenhada**, que começa exatamente no compasso de chegada. Isso só
vale quando o compasso de chegada não está visível na página exibida no
momento.

## Decisões do usuário (2026-09-22) — não reabrir

| Id | Decisão |
| --- | --- |
| **D-ALT** | O `.vsb` carrega as páginas **normais** (como hoje) **e** as páginas **alternativas**, usadas só pelo player quando há repetição. |
| **D-ALT-INDICE** | A indexação vista pelo usuário não muda: `goToPage`, `currentPage`, `onPageChanged` e `pageCount` continuam falando das páginas normais. A indexação alternativa só existe no modo player. |
| **D-ALT-EXTENSAO** | Cada sequência alternativa começa no compasso de chegada e vai **até o fim da peça** (sem cortar páginas que não forem usadas). |
| **D-VSB-PADRAO** | O `.vsb` é gerado **por padrão** com `--header none`, `--footer none` e `--no-instrument-labels`. Sem título/número de página desenhados e sem rótulo de instrumento, sobra mais espaço para a música, e as páginas alternativas (que o Verovio desenha sem cabeçalho) ficam iguais às normais. |
| **D-ALT-MECANISMO** | As páginas alternativas saem do **`Toolkit::Select()` do próprio Verovio** sobre o `Doc` já carregado, seguido de uma renderização normal pelo mesmo `View` → `BridgeDeviceContext`. Não se escreve nem se relê MEI, e não há fatiador próprio. |

## Decisão ainda aberta (o passo que depende dela para e pergunta)

| Id | Pergunta | Passo |
| --- | --- | --- |
| **D-META-TITULO** | Com `--header none` por padrão, a regra atual (§2.3 da spec) deixa `meta.title` **ausente**. O que fazer? | P01a |

## O que já foi provado (sessão de 2026-09-22, programa avulso, não versionado)

Um programa C++ ligado à `libverovio.so`, usando só a API pública do
`Toolkit`, carregou `Chopin_Mazurka_Op6_No1.mei` (3 páginas), chamou
`Select({"measureRange":"18-end"})` + `RedoLayout()` e renderizou SVG:

- A seleção saiu com **2 páginas**, já **paginadas pela altura** (a página 1
  vai do compasso 18 ao 44, e a 2 continua do 45). Não foi preciso escrever
  código de layout.
- O início da página 1 da seleção trouxe clave, armadura (3♯, igual ao
  `key.sig="3s"` do `scoreDef`), fórmula 3/4, chave de grupo, número de
  compasso "18" e a barra `rptstart`. O contexto vem de
  `Doc::ReactivateSelection` (`doc.cpp`), que copia o
  `system->GetDrawingScoreDef()` para um `Score` novo com rótulo
  `[selectionScore]`.
- As páginas da seleção **não têm `pgHead` nem `pgFoot`** (0 ocorrências no
  SVG). É por isso que D-VSB-PADRAO tira os dois das normais: assim os dois
  tipos de página ficam iguais.
- Os **`xml:id` das notas são preservados**: 304 notas na página 1 da seleção,
  todas presentes no desenho normal. Os ids de `system` (e do `score`/
  `scoreDef` sintetizados) são **novos**.
- O rótulo "piano" continua aparecendo na seleção. A opção
  `--no-instrument-labels` (commit `4663537`, `View::DrawSystem`) remove o
  rótulo e o espaço reservado para ele (a pauta começava em x = 1262 de
  21 000 e passou a começar em x = 0).
- `Select` aceita `{"start": id, "end": id}` ou `{"measureRange": "18-end"}`
  (`docselection.cpp`). O `measureRange` usa o **número** do compasso, que
  pode faltar ou se repetir. **Use sempre `start`/`end` por `xml:id`.**
- A seleção fica pendente até `RedoLayout()` (`toolkit.cpp`:
  `if (m_docSelection.m_isPending) m_doc.InitSelectionDoc(...)`). Um
  `Select("{}")` (sem `start`/`end`/`measureRange`) pede o reset.

## Regras que a fase P implementa

### Exportador (C++): quais sequências alternativas existem

1. Ordem de execução dos compassos: a sequência de `measureOn` do timemap que
   o próprio `RenderToBridgeFile` já gera (`includeMeasures: true`). Cada id
   é resolvido ao compasso notado pela **regra do sufixo** (spec §2.4:
   `^(.*)-rend([0-9]+)$`, com a base existindo no documento).
2. **Salto** = uma ocorrência cujo compasso não é o seguinte, **na ordem de
   documento**, do compasso da ocorrência anterior. É a mesma definição de
   `ScoreTimeline._build` (`isJump`).
3. **Pontos de chegada** = compassos de destino de algum salto, sem
   repetição, **excluindo** os que já são o primeiro compasso de alguma
   página normal (ali a página normal já serve).
4. Para cada ponto de chegada `T`: `Select({"start": T, "end": <último
   compasso do documento>})` + relayout, renderização de **todas** as páginas
   resultantes no mesmo `BridgeDeviceContext` (o dicionário de glifos é
   compartilhado) e reset da seleção. As páginas normais não podem mudar
   (critério byte-idêntico em P02c).

### Player (Dart): que página exibir em cada ocorrência

Uma página exibida é um **`PageRef`**: `(sequência, índice)`, em que a
sequência `null` é a normal e `k` é a k-ésima alternativa. Percorrendo as
ocorrências de compasso na ordem de execução, com a página exibida
`atual = (s, p)`:

1. 1ª ocorrência: a página normal do compasso.
2. Sem salto: a página do compasso **na sequência `s`**. Toda sequência vai
   até o fim da peça (D-ALT-EXTENSAO), então o compasso está sempre lá.
3. Salto para `T`, testando nesta ordem:
   1. `T` está na página exibida (`page_s(T) == p`) → **fica**. É o caso de
      salto na mesma página; sem haste.
   2. `T` é o 1º compasso de alguma página da sequência `s` → essa página.
   3. `T` é o 1º compasso de alguma página normal → essa página normal.
   4. Existe a sequência alternativa que começa em `T` → a página 0 dela.
   5. Caso contrário (`.vsb` antigo, sem alternativas) → `page_s(T)`, que é
      o comportamento de hoje (E03).

A haste (regra de A05b/E03b) continua a mesma. A única diferença é que a
página de trás passa a ser um `PageRef`.

## Mapa da fase

```
P01a (meta.title) → P01b (padrões do .vsb) → P01c (re-medição do corpus)
                                                   │
P02a (spec) → P02b (pontos de chegada) → P02c (render das alternativas)
                                                   │
                     P03a (modelo/parser) ─────────┴→ P02d (paridade das alternativas)
                                                        → P03b (vista com PageRef)
                        → P04a (rota na timeline) → P04b (player) → P04c (evidências) → P05 (portão)
```

P01* e P02a podem ser feitos em paralelo. P02b depende de P01c porque a
paginação muda com os padrões novos. P03a pode começar sobre o
`exemplo-alternates.json` de P02a, mas os critérios dele usam fixtures reais
de P02c. P02d vem depois de P03a porque o `compare` lê o `.vsb` pelo
`score_bridge`.
