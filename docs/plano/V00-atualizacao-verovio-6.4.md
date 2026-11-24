# V00 — Atualização do Verovio 6.3.0 → 6.4.1

Coordenação: Claude (Opus) monitora e revisa; o trabalho pesado fica em
subagentes Haiku. Avisos de andamento por notificação push. Sem commit/push sem
o usuário pedir.

Alvo: tag upstream `version-6.4.1` (`fbe8f46`), o patch mais recente da 6.4.
Base atual: `verovio/` vendorizado = `version-6.3.0` (`425dd7b`) + patches do
bridge.

## Passos

| Passo | O quê | Quem | Aceite |
|---|---|---|---|
| V1a | Clonar upstream em `compare/out/upstream`, diff `verovio/` × `version-6.3.0`: confirmar a base e listar os arquivos do bridge (novos/alterados) | Haiku | lista de patches; nenhuma diferença inexplicada |
| V1b | Linha de base do `zywny-aprendizado`: `flutter analyze` + `flutter test` com a lib atual | Haiku | contagem de falhas pré-existentes registrada |
| V2 | Merge de três vias (6.3.0 → nosso tree × 6.4.1) num repo temporário; resolver conflitos | Haiku (+ revisão) | merge sem marcadores; conflitos explicados |
| V3 | Trocar `verovio/` pelo resultado, build do CLI e das libs (`build_linux_so.sh`), testes do binding Dart | Haiku | build limpo; testes verdes |
| V4 | Paridade do corpus (`compare-corpus.sh`) e checagens de regressão do `.vsb` (scripts G/M/E) | Haiku | ≥99,99% em todas as páginas; diferenças explicadas |
| V5 | `zywny-aprendizado`: rebuild da `libverovio.so` + `verovio_data.zip`, `analyze` + `test` | Haiku | nenhuma falha nova em relação ao V1b |
| V6 | Atualizar docs (README, CLAUDE.md, relatório) para 6.4.1 e relatório final | Haiku + revisão | — |

Regras para os subagentes: saídas temporárias só em `compare/out/`; não alterar
`SvgDeviceContext`/`BBoxDeviceContext`/`View` além do que vier do upstream;
nada de commit.

## Resultado (2026-11-24)

- **Base confirmada**: `verovio/` vinha de `version-6.3.0` (`425dd7b`). Conferido na V1a: 31 ADDED, 28 M, 35 D.
- **Conflitos do merge** (`compare/out/v2-merge.md`), uma linha cada:
  - `ci_build.yml`, `python-ci-wheel.yml`, `bindings/iOS/all.h`, `pom.xml` e `.pypi-version`: o 6.4.1 alterou, nós apagamos; ficam apagados.
  - `expansionmap.h`/`.cpp`: `ScoreOrPartElement` do upstream; corpo do E04a mantido, com `score->` trocado por `scoreOrPart->`.
  - `doc.h`: `ScoreOrPartElement` e `MIDIEventLog` (G01); `GetSourceFormat`/`SetSourceFormat` e `MarkAsCastOff()`, os dois.
  - `midifunctor.h`: assinatura `CustomTuning *` do upstream, com `SetEventLog` (G01) mantido.
  - `doc.cpp`: `SetCustomTuning(scoreDef->GetCustomTuning())` do upstream, com `SetEventLog` (G01).
  - `options.h`/`.cpp`: `m_debugAlternateStarts` (P02b) e `m_convertAttributes` (novo), os dois.
  - `iomusxml.cpp`: HarmData próprio (D-MUSICA-CIFRA) e as linhas `rootStep`/`harmText` do upstream.
- **Uma adaptação de API**: `src/toolkit.cpp` (título de `meta`, D-META-TITULO): `GetVisibleScores()` virou `GetVisibleScoresOrParts()`.
- **Paridade** (34 páginas, `compare/out/v4-report.md`): média 0,006390% (linha de base 0,008800%); máximo 0,024964% (Clair de Lune p1, linha de base 0,039330%). Nenhuma página passa de 0,025%.
- **Nosso `.vsb` = SVG do 6.4.1 puro** nas 97 páginas.
- **Clair de Lune, compassos 66–69**: a troca de clave da pauta 2 era bug do 6.3.0, corrigido no 6.4.1. A suspeita da V4 sobre as 4 notas em F4 do compasso 69 foi descartada na V4b: o MusicXML mantém F4 até a troca para G2 em t=720 desse compasso, e essas notas vêm antes dela. O 6.4.1 puro desenha igual ao nosso, e o `pitchpos.json` bate com a clave desenhada em todas as notas dos compassos 64–70. Achado à parte, que já existia no 6.3.0: duas trocas de clave com uma nota só entre elas desenham essa nota em F4.
- **Maple Leaf Rag**: o 6.4.1 puro deixa de repetir a segunda passagem dos compassos 1–15, uma regressão do upstream (timemap: 905 entradas no puro, 1013 no nosso; o nosso dá o mesmo plano de repetições do 6.3.0). As 50 entradas a mais do `expansionmap` são 25 `accid` invisíveis criados pelo importador MusicXML do 6.4.1. O patch E04b do bridge (`iomusxml.cpp`) mantém o resultado correto: manter o E04b; candidato a issue no upstream. Evidência em `compare/out/v6-maple/`.
- **Classe nova `placeholder`** em `section`, `sb`, `pb` e `scoreDef` (grupos de sistema vazios, que o `BridgeDeviceContext` não desenha). Código de host não pode comparar essas strings de classe exatamente; o código atual do app e do zywny-comum está seguro.
- **Libs Android** reconstruídas (`arm64-v8a` e `x86_64`) e copiadas para o `jniLibs` do `zywny-aprendizado`; sha256 igual ao build do bridge.
- **Testes do `zywny-aprendizado`**: `flutter analyze` sem issues (linha de base: 0). `flutter test`, rodada com o build Android em paralelo: 4053 passou, 1 falhou (`aluno_virtual_calibrar_test.dart:64`), 2 pulados. Rodada completa repetida: 4054 passou, 0 falhou, 2 pulados, igual à linha de base; o teste de calibração passou. A falha não reapareceu, e a causa não foi identificada.
- **Docs**: README, `docs/formato/especificacao-v1.md` e `docs/formato/exemplo-minimo.json` para 6.4.1. Em `docs/nota-para-zywny-musica.md` a menção a `6.3.0-<hash>` fica, porque descreve a medição do M00.
- **Pendências**:
  - `compare/pubspec.yaml` aponta `score_bridge` para `/home/mauricio/IdeaProjects/zywny/score_bridge`, que foi para o `zywny-comum`. Anterior a esta atualização; não corrigido.
  - `zywny-comum/score_bridge/test/exemplo_minimo_test.dart` fixa `verovio 6.3.0` no fixture; o gerador escreve `6.4.1`.
  - Não testado em aparelho.
