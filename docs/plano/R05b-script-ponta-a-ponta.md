# R05b — `compare-page.sh` no fluxo `.vsb`, de ponta a ponta

**Depende de:** R05a, R04d · **Decisão necessária:** não

## Objetivo

Um comando só, reproduzível, que sai da partitura e chega na estatística de
divergência: `verovio -t svg` → PNG de referência; `verovio -t vsb` →
`compare scene-to-png` → PNG da cena; `compare diff` → imagem + número. É a
ferramenta que todos os passos seguintes usam para medir.

## Ler antes (só isto)

- `compare/scripts/compare-page.sh` (estado atual: SVG→PNG funciona, o ramo
  Lottie está comentado e deve ser **removido**, não adaptado).
- `compare/lib/main.dart` (comandos `diff` e `scene-to-png`).
- Notas de execução de R05a (backend escolhido).

## Contexto que você precisa (não vá procurar, está aqui)

O script atual já resolve três problemas que você não deve redescobrir:

1. **Display**: o `compare` é app Flutter/Linux e precisa de display mesmo em
   batch — `xvfb-run -a` quando `DISPLAY` está vazio.
2. **Nomes com ponto**: o `-o` do Verovio trunca a partir do último `.`
   (`RemoveExtension`, `tools/main.cpp`); vários `.mxl` do corpus têm ponto no
   nome. O script renderiza num prefixo temporário e move depois.
3. **Lista de fontes**: o `svg_render` recebe as 4 SMuFL (Leipzig, Bravura,
   Leland, Gootville) e as 4 Liberation Serif, mais
   `--pin-serif-family "Liberation Serif"`. Mexer nessa lista muda o PNG de
   referência e invalida comparações com números antigos.

Mais duas coisas específicas deste fluxo:

- **`-p` do Verovio é 1-based; `page.index` no `.vsb` é 0-based.** Gere o
  `.vsb` com todas as páginas e selecione a página no `scene-to-png`, ou gere
  por página — mas escolha um dos dois e documente no cabeçalho do script.
- **`xml:id` auto-gerado não é determinístico entre processos** (achado
  registrado nas notas de S04). Isso não afeta a comparação de pixels, mas
  afeta qualquer comparação que envolva ids entre duas invocações do CLI —
  não escreva o script assumindo ids estáveis entre a chamada do `-t svg` e a
  do `-t vsb`.

## O que fazer

1. Reescrever `compare/scripts/compare-page.sh`:

   ```
   compare-page.sh <arquivo> <página> [tolerância]
     → compare/out/<peça>-p<N>-svg.png
     → compare/out/<peça>-p<N>-scene.png
     → compare/out/<peça>-p<N>-diff.png
     → estatística no stdout (pixels divergentes, total, %)
   ```

   Remova o ramo Lottie comentado. Mantenha as verificações de binário
   ausente com a mensagem que diz **como compilar** (o script atual já faz
   isso — é o que salva quem chega depois).

2. Ativar o backend escolhido em R05a dentro do script (variável de ambiente
   ou flag de build documentada), para que ninguém meça com o backend errado
   por acidente.

3. Fazer o script imprimir, no fim, uma linha única em formato estável
   (`peça;página;largura;altura;divergentes;total;pct`), que R06a vai
   agregar em CSV sem reprocessar texto livre.

## Fora de escopo

- Varredura do corpus (R06a) — este passo é uma página por vez.
- Teste widget-vs-harness (R05c).

## Critérios de aceite

1. `compare-page.sh <peça> 1` roda de ponta a ponta em 3 peças diferentes
   (pelo menos uma `.mxl` com ponto no nome) e escreve os 3 PNGs mais a
   estatística.
2. As dimensões do PNG da cena são **exatamente** as do PNG do SVG nas 3
   peças.
3. Determinismo: rodar o mesmo comando duas vezes produz
   `<peça>-p1-scene.png` byte-idêntico (`cmp` sem diferença).
4. O script falha com mensagem clara (e código de saída != 0) quando falta um
   binário, quando a página não existe na peça e quando o arquivo de entrada
   não existe.
5. A linha final em formato estável sai correta e é a última linha do stdout.
6. `compare/README.md` atualizado com o fluxo novo e o backend oficial.

## Notas de execução

(a preencher por quem executar)
