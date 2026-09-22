# P02a — Especificação: `alternates.json`

**Depende de:** — (pode rodar em paralelo a P01*) · **Decisão necessária:**
não

## Objetivo

Fechar, **só em documentação**, o contrato de como as páginas alternativas
entram no `.vsb`, antes de escrever C++ (P02c) ou Dart (P03a). É o mesmo
papel que S01 teve para o formato inteiro.

## Ler antes (só isto)

- `docs/plano/P00-visao-geral-paginas-alternativas.md` (inteiro).
- `docs/formato/especificacao-v1.md`: §2, §2.1, §2.2, §5 (cabeçalho), §5.5 e
  §9.
- `docs/formato/schema-v1.json` e `docs/formato/exemplo-minimo.json`.

## Contexto que você precisa (não vá procurar, está aqui)

- A mudança tem que ser **aditiva**, como `meta.json` foi em 2026-09-20:
  `version` continua `1`, e um leitor antigo que ignore o arquivo extra
  continua funcionando só com as páginas normais.
- Um arquivo **separado** (e não uma chave nova em `scene.json`) permite que
  o leitor adie o parse das alternativas até o player precisar delas. Com
  D-ALT-EXTENSAO (cada sequência vai até o fim da peça), as alternativas
  podem pesar tanto quanto as páginas normais ou mais.
- Uma página alternativa é **igual em forma** a uma página de `scene.json`
  (§5): mesmos campos, mesma árvore, mesmos glifos do **mesmo**
  `glyphs.json`. Os `xml:id` de notas, acordes, compassos etc. são os mesmos
  das páginas normais. Ids de `system` e do `score`/`scoreDef` sintetizados
  pela seleção são novos.
- Dentro de **uma** sequência, cada id aparece uma vez (é uma paginação
  completa de um trecho). Entre sequências, e entre uma sequência e as
  normais, os ids se repetem **por construção**. O índice de elementos
  (§5.5) é **por sequência**.

## O que fazer

1. Nova seção **§2.5 `alternates.json`** na spec:

   ```json
   {
     "sequences": [
       {
         "start": "d1e3853",
         "pages": [ { "index": 0, "...": "igual a scene.pages[i] (§5)" } ]
       }
     ]
   }
   ```

   - `start`: `xml:id` (notado, sem `-rendN`) do compasso de chegada, que é
     o **primeiro compasso** da página 0 da sequência.
   - `pages`: a paginação do trecho `start` → fim da peça (D-ALT-EXTENSAO).
     `index` é 0-based **dentro da sequência**.
   - Sequências em ordem de documento de `start`, sem `start` repetido.
   - Regra de existência (normativa): só existe sequência para um compasso
     que é destino de um salto na execução (spec §2.4: ordem dos `measureOn`)
     **e** não é o primeiro compasso de nenhuma página normal. Uma peça sem
     sequência nenhuma **omite** o arquivo e a entrada do manifest (mesma
     regra de omissão do timemap e do `meta.json`).
2. §2.1: `files.alternates` (opcional), descrito como os outros.
3. §2.2: propriedade opcional `alternates` no JSON único.
4. §5.5: diga que o índice derivado é por sequência (normais e cada
   alternativa, cada uma com o seu).
5. §9: um leitor que não conhece `alternates` o ignora. Um leitor que
   conhece e não encontra o arquivo trata a peça como "sem alternativas".
6. `schema-v1.json`: `$defs/page` reusado pelo `alternates`, e um schema do
   documento `alternates.json`. O `exemplo-minimo.json` **não** muda (não tem
   repetição).
7. Histórico de revisões: linha datada citando D-ALT/D-ALT-EXTENSAO.
8. Crie `docs/formato/exemplo-alternates.json`, **escrito à mão**, com uma
   sequência de uma página pequena (copie a estrutura de uma página do
   `exemplo-minimo.json`, com um compasso). Ele valida contra o schema e
   serve de fixture para P03a antes de o C++ existir.

## Fora de escopo

- Qualquer código.
- Informação de rota (que página exibir quando): é o **leitor** que decide,
  pela regra de P00. O arquivo só oferece as páginas.

## Critérios de aceite

1. Spec com §2.5, §2.1, §2.2, §5.5 e §9 atualizados, e histórico registrado.
2. `exemplo-alternates.json` valida contra o schema novo (use o mesmo
   validador que S01 usou; registre o comando nas notas).
3. `exemplo-minimo.json` continua validando.

## Notas de execução

_(preencher)_
