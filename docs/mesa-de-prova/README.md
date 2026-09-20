# Mesa de prova — amostra de evidência visual (R06c)

Recorte curado de `compare/corpus/` (esse diretório **já é** versionado
página a página — SVG de referência, cena do `score_bridge` e diff — e é
onde as 34 páginas do corpus inteiro ficam visíveis direto no GitHub após o
push; ver o cabeçalho de `compare/scripts/compare-corpus.sh`). Este
diretório existe só para reunir, num único lugar, as páginas que o
[relatório de paridade](../relatorio-paridade.md) cita como exemplo de cada
categoria de divergência — não duplica o corpus inteiro.

| Peça / página | Por que foi escolhida |
| --- | --- |
| `Chopin_Etude_Op10_No9` p1 | Pior página do corpus depois de R06b (0,031698%) — exemplo do piso de antialiasing (`TextPainter`/Impeller × `tiny-skia`) em texto comum, categoria sem correção conhecida. |
| `Chopin_Etude_Op10_No9` p2 | Antes da sexta investigação de R06b tinha o número de página "– 2 –" deslocado (bug de agrupamento de âncora multi-run); depois da correção, 0,026952%, dentro do que resta de piso de AA. |
| `Clair_de_Lune__Debussy` p4 | Antes da quinta investigação de R06b tinha a frase "morendo jusqu'à la fin" deslocada 9 px (bug de `letterSpacing` não somado após o último glifo); depois da correção, 0,006991%, dentro do portão de 0,01%. |
| `Grieg_Butterfly_Op43_No1` p3 | Melhor página do corpus (0,000481%) — referência de "quase zero", para comparação. |

Cada página tem três PNGs: `-svg.png` (referência, `resvg`), `-scene.png`
(cena do `score_bridge`/Impeller) e `-diff.png` (mapa de divergência na
tolerância 128/255). O CSV bruto com as 34 páginas está em
`compare/corpus/resultado.csv`.
