#!/usr/bin/env python3
"""G08c: gera docs/formato/sumico/vetores.json (+ os .vsb pequenos que ele usa) e um PNG de evidência
por caso em compare/out/g08c/.

Cada caso traz um `resumo` ESCRITO À MÃO (pela teoria musical e pela leitura da cena; a conta está
em `conta`) e, gerado pela referência depois de conferir o resumo, o bloco numérico completo
`esperado` (o que o host compara, com tolerância de 0,5 unidade de viewBox). Se um resumo escrito à
mão divergir da referência o script para: ou a referência, ou a conta, está errada.

`coluna` é C (as notas da coluna que ganha a pausa); `escondidas` é H (todas as notas escondidas no
momento; ausente = só a coluna).

Uso: g08c-make-vectors.py   (roda de qualquer diretório)
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import hide_ref as hr
import scene_svg

OUT = os.path.join(ROOT, "docs", "formato", "sumico")
PNG = os.path.join(ROOT, "compare", "out", "g08c")
VEROVIO = os.path.join(ROOT, "verovio", "tools", "verovio")
RES = os.path.join(ROOT, "verovio", "data")

SOURCES = {
    "h010.vsb": "corpus/sumico/h010.musicxml",
    "h056.vsb": "corpus/sumico/h056.musicxml",
    "f04-cross-staff.vsb": "corpus/fantasma/f04-cross-staff.mei",
    "r04-casas.vsb": "corpus/repeticoes/r04-casas.mei",
}
os.makedirs(OUT, exist_ok=True)
os.makedirs(PNG, exist_ok=True)
for name, src in SOURCES.items():
    subprocess.run([VEROVIO, "-t", "vsb", "--xml-id-seed", "42", "--resource-path", RES, "-o", os.path.join(OUT, name),
                    os.path.join(ROOT, src)], check=True, capture_output=True)


def R(notes, chords, beams, ledgers, rest, loc, dots=0):
    return dict(notes=notes, chords=chords, beams=beams, ledgers=ledgers, rest=rest, restLoc=loc, dots=dots)


# (slug, nome, vsb, página, C, H|None, resumo, conta)
CASES = [
 ("c01-duas-vozes", "coluna de duas vozes com figuras diferentes: vale a mais curta", "h010.vsb", 0,
  ["r10709ff", "x1848jna", "z1oagi0k"], None, R(3, 1, 0, 1, "E4E5", 4),
  "soprano semínima (dur 4) e alto/tenor em acorde de mínimas (dur 2): a mais curta é a semínima -> E4E5; n=5 -> loc 4 "
  "(linha do meio), y = 1106 + (8-4)*90 = 1466; x = 3446 (menor x de cabeça); alto e tenor são o acorde yy2zfkq, "
  "escondido inteiro; o tenor está em loc -2 -> 1 traço abaixo, só desta coluna (x 3398-3720)"),
 ("c02-suplementar-ao-lado-de-visivel", "linha suplementar da coluna some, a das colunas vizinhas fica", "h010.vsb", 0,
  ["qyrisol", "t1hslndl"], None, R(2, 0, 0, 1, "E4E6", 4),
  "colcheia (soprano) e semínima (baixo-tenor): a mais curta é a colcheia -> E4E6; o tenor em loc -3 pede 1 linha "
  "abaixo (loc <= -2); o traço (x 16717-17039 = cabeça 16765-16991 +- 48 de extensão) só pertence a esta coluna: as "
  "colunas dos instantes 16 e 18, vizinhas, têm o traço delas e ele NÃO entra em `ledgers`; a colcheia está na barra "
  "p1thud05 com u1m1ofen, que continua visível -> a barra fica"),
 ("c03-barra-1-de-2", "barra com 1 de 2 notas escondidas: a barra fica", "h010.vsb", 0,
  ["m1ujlm1s", "u1knnyxl", "w1x5tsbc"], None, R(3, 1, 0, 1, "E4E6", 4),
  "a colcheia m1ujlm1s é uma das duas da barra l1z05zi4 (a outra é nc27kmr, visível) -> beams 0; a mínima do alto/tenor "
  "é o acorde vhtnoag; mais curta = colcheia -> E4E6"),
 ("c04-barra-2-de-2", "barra com 2 de 2 notas escondidas: a barra some", "h010.vsb", 0,
  ["nc27kmr"], ["m1ujlm1s", "u1knnyxl", "w1x5tsbc", "nc27kmr"], R(4, 1, 1, 1, "E4E6", 4),
  "a coluna do instante 0 já estava escondida e agora o instante 0,5 (nc27kmr, colcheia): as duas notas da barra "
  "l1z05zi4 estão em H -> a barra some (1 forma filha direta); a pausa é só da coluna nova (x 2116)"),
 ("c05-semibreve", "semibreve: a pausa pende uma linha acima do meio", "h010.vsb", 0,
  ["s15b1q47", "uatlm6o"], None, R(2, 1, 0, 0, "E4E3", 6),
  "duas vozes em semibreve (acorde tm2wsd9, locs 0 e 5): dur 1 -> E4E3; loc = 4 + 2 = 6 (a semibreve pende da 4ª linha "
  "contada de baixo); y = 7801 + (8-6)*90 = 7981"),
 ("c06-pontuada", "figura pontuada: a pausa leva o ponto", "h010.vsb", 0,
  ["g1qqc06o", "y4ih5in"], None, R(2, 0, 0, 0, "E4E5", 4, 1),
  "mínima e semínima pontuada: a mais curta é a semínima pontuada (dur 4, 1 ponto) -> E4E5 + 1 ponto; o ponto cai no "
  "espaço acima da linha do meio: loc 4 par -> 5, y = 3519 + (8-5)*90 = 3789; x = 12798 + 219 (largura do glifo, "
  "truncada) + 90 (unit) = 13107; raio 2*90/5 = 36"),
 ("c07-empate-de-figura", "mesma figura, uma pontuada: a sem ponto é a mais curta", "h010.vsb", 0,
  ["u1rdh9nl", "yuf88p8"], None, R(2, 0, 0, 1, "E4E5", 4),
  "duas semínimas, uma pontuada (dur 4 nas duas): vale a sem ponto -> E4E5 sem ponto; traço abaixo (loc -3)"),
 ("c08-quialtera", "colcheia de quiáltera: vale a figura escrita", "h056.vsb", 0,
  ["w1ewv8n7"], None, R(1, 0, 0, 0, "E4E6", 4),
  "tercina de colcheias (dur escrito 8, duração sonora 1/3 de semínima): a pausa é de colcheia -> E4E6, não de "
  "semicolcheia; as outras duas notas da tercina seguem na barra u17t1jzh -> a barra fica"),
 ("c09-nota-ligada", "nota ligada: cabeça e continuação escondidas pelo id", "h010.vsb", 0,
  ["k15ihioq", "n1nkt294", "p1n03y7u"], ["k15ihioq", "n1nkt294", "p1n03y7u", "kf0fkqg", "m1j3dlmg"], R(5, 2, 0, 2, "E4E6", 4),
  "acorde de colcheias no fim de um sistema, ligado a um acorde de semínima pontuada no começo do seguinte (o host "
  "esconde as continuações pelo id, midi.json -> tied): os dois acordes saem inteiros (l1wbisrw e ld7kz8f) e o traço "
  "abaixo de cada sistema (loc -3 nas duas); a pausa é só da cabeça (colcheia -> E4E6) e não leva ponto, porque a "
  "continuação não entra em C"),
 ("c10-cross-staff", "coluna cross-staff: pausa na pauta de desenho", "f04-cross-staff.vsb", 0,
  ["f04-c", "f04-f"], None, R(2, 0, 0, 3, "E4E5", 4),
  "f04-c é uma nota da mão direita desenhada na pauta de baixo (loc 14: 3 linhas suplementares acima, pelo `staff` do "
  "nó) e f04-f é a nota do baixo (mínima); a mais curta é a semínima -> E4E5 na pauta de desenho j196sd00 (topo 2340): "
  "y = 2340 + (8-4)*90 = 2700"),
 ("c11-pagina-alternativa", "página alternativa: mesma regra, coordenadas da página", "r04-casas.vsb", "alt0.0",
  ["m5n3"], None, R(1, 0, 0, 1, "E4E5", 4),
  "a mesma nota existe na página normal e na alternativa (sequência a partir do compasso m5); em loc -2 pede 1 traço "
  "abaixo; topo da pauta 566 -> y = 566 + (8-4)*90 = 926"),
]


def crop_of(doc, ref, col, hidden_ids):
    """Região de evidência no referencial de conteúdo: o compasso (todas as pautas) em volta da coluna."""
    root = doc.page_root(ref)
    ix = hr.PageIx(root)
    st = ix.notes[col[0]][1]
    best = None

    def rec(n, meas):
        nonlocal best
        if hr.classes(n)[:1] == ["measure"]:
            meas = n
        if n is st:
            best = meas
        for c in n.get("children", []):
            if c.get("t") == "g":
                rec(c, meas)
    rec(root, None)
    xs = [head[0] for i in col for head in [hr.head_extent(doc, ix.notes[i][0])]]
    x = min(xs)
    y0, y1 = best["bbox"][1], best["bbox"][3]
    return (x - 700, y0 - 150, x + 1500, y1 + 150)


vectors = []
bad = 0
docs = {}
for slug, nome, vsb, page, col, hid, want, conta in CASES:
    doc = docs.setdefault(vsb, hr.Doc(os.path.join(OUT, vsb)))
    res = json.loads(json.dumps(hr.run(doc, page, col, hid)))
    got = hr.summary(res)
    if got != want:
        print("RESUMO à mão diverge da referência:", slug, "\n  à mão:   ", want, "\n  obtido:  ", got)
        bad += 1
    case = dict(nome=nome, vsb=vsb, pagina=page, coluna=col)
    if hid:
        case["escondidas"] = hid
    case.update(resumo=want, esperado=res, conta=conta)
    vectors.append(case)
    scene_svg.render_png(doc, page, res, crop_of(doc, page, col, hid or col), os.path.join(PNG, slug + ".png"))
if bad:
    sys.exit(1)
json.dump(dict(descricao="Vetores da nota escondida e da pausa substituta (especificacao-v1.md §11, G08c). Cada caso: "
                         "`coluna` = C, `escondidas` = H (ausente = só C), `resumo` escrito à mão, `esperado` = saída de "
                         "compare/scripts/hide_ref.py (tolerância de 0,5 unidade de viewBox nos números).",
               tolerancia=0.5, casos=vectors), open(os.path.join(OUT, "vetores.json"), "w"), ensure_ascii=False, indent=1)
print("%d casos gravados; PNGs em %s" % (len(vectors), PNG))
