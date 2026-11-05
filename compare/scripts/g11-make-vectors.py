#!/usr/bin/env python3
"""G11: gera os casos de compasso de docs/formato/sumico/vetores.json (chave `casosCompasso`), copia os
`.vsb` novos para docs/formato/sumico/ e desenha um PNG de evidência por caso em compare/out/g11/vec/.

Os `.vsb` de entrada saem do binário atual (`-t vsb --xml-id-seed 42`, como no G08c) para
compare/out/g11/vec/ (feito à mão, um por vez: ver as linhas FONTES). A contagem de notas e de pausas de
cada caso é conferida contra uma contagem independente feita no MEI da fonte (`-t mei --xml-id-seed 42`),
não contra a cena: nota = elemento <note>; pausa que some = <rest> de pauta que tem nota.
"""
import json, os, shutil, subprocess, sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import hide_ref as hr
import scene_svg as ss

VEC = os.path.join(ROOT, "compare/out/g11/vec")
DST = os.path.join(ROOT, "docs/formato/sumico")
VEROVIO = os.path.join(ROOT, "verovio/tools/verovio")
RES = os.path.join(ROOT, "verovio/data")
NS = "{http://www.music-encoding.org/ns/mei}"
XID = "{http://www.w3.org/XML/1998/namespace}id"

FONTES = {   # .vsb -> fonte (os seis de g11-*/f06 vêm de compare/out/g11/vec; h010 e r04-casas já estão em docs/formato/sumico)
    "g11-mao-intercalada.vsb": "corpus/sumico/aprendizado/2c-0.musicxml",
    "g11-melodia-esquerda.vsb": "corpus/sumico/aprendizado/4b-0.musicxml",
    "g11-tercina.vsb": "corpus/sumico/aprendizado/33d-0.musicxml",
    "g11-6-8.vsb": "corpus/sumico/aprendizado/28d-0.musicxml",
    "g11-especiais.vsb": "corpus/sumico/g11-compassos-especiais.mei",
    "f06-mudanca-armadura.vsb": "corpus/fantasma/f06-mudanca-armadura.mei",
    "h010.vsb": "corpus/sumico/h010.musicxml",
    "r04-casas.vsb": "corpus/repeticoes/r04-casas.mei",
}

# (slug, nome, vsb, página, compassos, conta)
CASES = [
 ("m01-primeiro-do-sistema", "primeiro compasso do sistema: a pausa fica depois de clave, armadura e fórmula",
  "h010.vsb", 0, ["t179lj11"], "inner [1487, 4792]: cx = 1487 + (4792 − 1487)//2 = 3139; x = 3139 − 216//2 = 3031"),
 ("m02-compasso-comum", "compasso comum no meio do sistema",
  "h010.vsb", 0, ["axzadr3"], "inner [4819, 8124]: cx = 4819 + 3305//2 = 6471; x = 6471 − 108 = 6363"),
 ("m03-ultimo-do-sistema", "último compasso do sistema (barra no fim da linha)",
  "h010.vsb", 0, ["r16x677f"], "inner [15362, 19977]: cx = 15362 + 4615//2 = 17669; x = 17669 − 108 = 17561"),
 ("m04-barra-de-repeticao", "primeiro do sistema, com cabeçalho e barra de repetição à esquerda (página alternativa)",
  "h010.vsb", "alt0.0", ["p126lw7d"], "inner [1870, 7503]: cx = 1870 + 5633//2 = 4686; x = 4686 − 108 = 4578"),
 ("m05-cabecalho-no-meio", "compasso com armadura trocada no meio da linha",
  "f06-mudanca-armadura.vsb", 0, ["f-m3"], "o inner começa depois da armadura nova; ver `inner` do compasso"),
 ("m06-mao-intercalada", "mão intercalada (2c): a pauta que só tem pausa fica como está, a outra ganha a pausa de compasso",
  "g11-mao-intercalada.vsb", 0, ["g1cokkdt"], "uma pauta com 4 notas e outra só com uma pausa: 1 pausa de compasso, a pausa de verdade fica"),
 ("m07-notas-e-pausas", "pautas com notas e pausas misturadas: as pausas de verdade somem e entra a pausa de compasso",
  "g11-mao-intercalada.vsb", 0, ["dgv5qh9"], "duas pautas, cada uma com 2 notas e 1 pausa: 4 notas e 2 pausas somem, 2 pausas de compasso"),
 ("m08-melodia-na-esquerda", "melodia na esquerda (4b)",
  "g11-melodia-esquerda.vsb", 0, ["g1cokkdt"], "pauta de cima com 1 nota, a de baixo com 2: 3 notas somem, 2 pausas de compasso"),
 ("m09-tercina", "compasso com tercina: o colchete e o número somem com as notas",
  "g11-tercina.vsb", 0, ["fz4nyf"], "uma tercina de colcheias (3 notas) e as outras notas do compasso"),
 ("m10-seis-oito", "6/8: o glifo é a semibreve mesmo assim",
  "g11-6-8.vsb", 0, ["h6n5g6x"], "compasso de 3 semínimas (6/8): `measure_len_q` = 3, menos de 8"),
 ("m11-pausa-no-compasso-dois-pautas-mistas", "uma pauta com notas e pausas, a outra já com pausa de compasso (fica, sem outra por cima)",
  "g11-especiais.vsb", 0, ["g11-m3"], "pauta 1: 2 notas e 2 pausas (as 2 pausas somem); pauta 2: só mRest, fica"),
 ("m12-tercina-e-ligadura", "um compasso: a tercina e a ligadura de dentro somem; a ligadura de prolongamento para o seguinte fica",
  "g11-especiais.vsb", 0, ["g11-m4"], "tercina g11-t1 e ligadura g11-sl1 (dentro do compasso) somem; g11-ti1 cruza para o compasso 5 e fica"),
 ("m13-compassos-vizinhos", "dois compassos vizinhos escondidos: cada um com a sua pausa, a ligadura de prolongamento entre eles some",
  "g11-especiais.vsb", 0, ["g11-m4", "g11-m5"], "ti1 toca só os compassos 4 e 5: some; sl2 sai do compasso 5 para o 6 (outra linha) e a primeira metade some"),
 ("m14-dois-semibreves", "compasso de 2 semibreves (4/2): o Verovio desenharia a pausa de breve, que não é glifo reservado",
  "g11-especiais.vsb", 0, ["g11-m2"], "8 semínimas ≥ 8: sem pausa de compasso substituta; as notas somem"),
 ("m15-anacruse", "anacruse (1 semínima): o Verovio desenha a mesma semibreve",
  "g11-especiais.vsb", 0, ["g11-m0"], "1 semínima < 8: a regra vale como nos outros; a pauta da pausa de verdade fica"),
]


def mei_counts(src, measure_ids):
    """Contagem independente no MEI da fonte: notas e pausas que somem, por compasso."""
    mei = os.path.join(VEC, os.path.basename(src) + ".mei")
    subprocess.run([VEROVIO, "-t", "mei", "--xml-id-seed", "42", "--resource-path", RES, "-o", mei, os.path.join(ROOT, src)],
                   check=True, capture_output=True)
    root = ET.parse(mei).getroot()
    out = {"notes": 0, "rests": 0}
    for m in root.iter(NS + "measure"):
        if m.get(XID) not in measure_ids:
            continue
        for st in m.findall(NS + "staff"):
            n = sum(1 for _ in st.iter(NS + "note"))
            if n:
                out["notes"] += n
                out["rests"] += sum(1 for _ in st.iter(NS + "rest"))
    return out


def main():
    base = os.path.join(DST, "vetores.json")
    vec = json.load(open(base))
    docs, cases, bad = {}, [], 0
    for slug, nome, vsb, page, measures, conta in CASES:
        src_vsb = os.path.join(VEC, vsb) if os.path.exists(os.path.join(VEC, vsb)) else os.path.join(DST, vsb)
        doc = docs.setdefault(vsb, hr.Doc(src_vsb))
        res = json.loads(json.dumps(hr.run_measures(doc, page, measures)))
        h = res["hidden"]
        resumo = dict(notes=len(h["notes"]), chords=len(h["chords"]), beams=len(h["beams"]), ledgers=len(h["ledgers"]),
                      rests=len(h["rests"]), tuplets=len(h["tuplets"]), controls=len(h["controls"]),
                      standIns=len(res["measureStandIn"]))
        ind = mei_counts(FONTES[vsb], set(measures))
        if (ind["notes"], ind["rests"]) != (resumo["notes"], resumo["rests"]):
            print("CONTAGEM INDEPENDENTE diverge:", slug, ind, resumo); bad += 1
        cases.append(dict(nome=nome, vsb=vsb, pagina=page, compassos=measures, resumo=resumo,
                          esperado=dict(hidden=h, measureStandIn=res["measureStandIn"]), conta=conta))
        # PNG de evidência: o sistema do primeiro compasso
        root = doc.page_root(page)
        ix = hr.PageIx(root)
        m0, sys0 = ix.measures[measures[0]]
        xs = [ix.measures[k][0]["bbox"] for k in ix.measures if ix.measures[k][1] is sys0]
        crop = (-60, min(b[1] for b in xs) - 80, max(b[2] for b in xs) + 60, max(b[3] for b in xs) + 80)
        ss.render_png_measures(doc, page, res, crop, os.path.join(VEC, slug + ".png"))
    for v in {c["vsb"] for c in cases}:
        if os.path.exists(os.path.join(VEC, v)):
            shutil.copy(os.path.join(VEC, v), os.path.join(DST, v))
    vec["casosCompasso"] = cases
    vec["descricao"] = vec["descricao"].split(" `casosCompasso`")[0] + (
        " `casosCompasso` (G11, regra 8, compasso inteiro): `compassos` = ids dos compassos escondidos por inteiro, `resumo` = contagens "
        "(as de notas e pausas conferidas contra o MEI da fonte), `esperado` = saída de `hide_ref.py run_measures` (`hidden`: notes, chords, "
        "beams, ledgers, rests, tuplets, controls; `measureStandIn`: [{measure, staff, g, x, y, sx, sy}]), tolerância 0,5.")
    json.dump(vec, open(base, "w"), indent=1, ensure_ascii=False)
    print("%d casos de compasso, %d divergências na contagem independente" % (len(cases), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
