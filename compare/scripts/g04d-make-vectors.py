#!/usr/bin/env python3
"""G04d: gera docs/formato/fantasma/vetores.json (+ os .vsb pequenos que ele usa).

Cada caso traz um `resumo` ESCRITO À MÃO (pela teoria musical, contas no comentário `conta`) e,
gerado pela referência depois de conferir o resumo, o bloco numérico completo `fantasmas`
(o que o `zywny` compara, com tolerância de 0,5 unidade de viewBox). Se um resumo escrito à mão
divergir da referência o script para: ou a referência, ou a conta, está errada.

Uso: g04d-make-vectors.py   (roda de qualquer diretório)
"""
import json, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import ghost_ref as gr

OUT = os.path.join(ROOT, "docs", "formato", "fantasma")
VEROVIO = os.path.join(ROOT, "verovio", "tools", "verovio")
RES = os.path.join(ROOT, "verovio", "data")
GAP = 0.5   # folga do acidente, em `unit` (medida em G04d: mediana 0,4996 com unit 60/90/120)

SOURCES = {
    "satie.vsb": os.path.join(ROOT, "corpus/musicxml/Erik_Satie_-_Gymnopedie_No.1.mxl"),
}
for n in ("f01-clave-no-meio", "f02-oitavas", "f03-transpositor", "f04-cross-staff", "f05-armadura-nao-padrao",
          "f06-mudanca-armadura", "f07-acidentes", "f08-pausas"):
    SOURCES[n + ".vsb"] = os.path.join(ROOT, "corpus/fantasma/%s.mei" % n)

os.makedirs(OUT, exist_ok=True)
for name, src in SOURCES.items():
    subprocess.run([VEROVIO, "-t", "vsb", "--xml-id-seed", "42", "--resource-path", RES, "-o", os.path.join(OUT, name), src],
                   check=True, capture_output=True)

# ids do Satie (1º compasso): acorde si3-ré4-fá#4 na pauta 1; pausa na pauta 1 e sol2 na pauta 2 (baixo)
CH = ["orw55dt", "q1t6l0ej", "r1c5f34m"]           # b3 (59), d4 (62), f#4 (66)
REST, BASS = "j97m9qh", "yw90mxt"                   # pausa (pauta 1), sol2 (43, pauta 2)

def R(loc, target, accid=None, m=0, ledgers=0, pname=None, octv=None, alt=0):
    return dict(loc=loc, m=m, accid=accid, ledgers=ledgers, pname=pname, oct=octv, alt=alt, target=target)

# (nome, vsb, esperados, teclas, [resumos por tecla, em ordem crescente de tecla], conta)
CASES = [
 ("acorde: tecla branca acima do acorde", "satie.vsb", CH, [69], [R(3, CH[2], None, 0, 0, "a", 4, 0)],
  "alvo f#4 (66, dist 4); A4 natural: loc=(4-4)*7+5-2=3; armadura de ré maior não altera lá; sem colisão (|3-1|=2)"),
 ("tecla preta, armadura de sustenidos: sustenido com acidente", "satie.vsb", CH, [70], [R(3, CH[2], "E262", 0, 0, "a", 4, 1)],
  "lá#4: loc 3; em vigor para lá = 0, alt +1 -> desenha ♯"),
 ("tecla preta já na armadura: sem acidente, desloca por colisão (segunda)", "satie.vsb", CH, [61], [R(-2, CH[1], None, 0, 1, "c", 4, 1)],
  "dó#4: loc -2, 1 linha suplementar; a armadura já tem dó# -> sem acidente; |-2-(-3)|=1 e |-2-(-1)|=1 com si3/ré4 na mesma coluna -> desloca"),
 ("duas fantasmas em segunda", "satie.vsb", CH, [61, 63], [R(-2, CH[1], None, 0, 1, "c", 4, 1), R(-1, CH[1], "E262", 0, 0, "d", 4, 1)],
  "dó#4 (loc -2) e ré#4 (loc -1, sem ré# na armadura -> ♯); a segunda colide com o ré4 real e com a 1ª fantasma -> 2 deslocamentos"),
 ("mesmo loc de uma cabeça real, bequadro necessário", "satie.vsb", CH, [65], [R(1, CH[2], "E261", 0, 0, "f", 4, 0)],
  "alvo f#4 (66, dist 1); fá4 natural: loc 1 = o do fá#4 real; armadura tem fá# -> alt 0 != +1 -> ♮; desloca"),
 ("empate de distância: vale a nota de cima", "satie.vsb", CH, [64], [R(0, CH[2], None, 0, 0, "e", 4, 0)],
  "mi4 (64): |64-62|=|64-66|=2 -> alvo f#4 (a de cima); mi4 natural loc=0+2-2=0; |0-1|=1 -> desloca"),
 ("8va: muito agudo cabe com uma oitava", "satie.vsb", CH, [100], [R(14, CH[2], None, 1, 3, "e", 7, 0)],
  "mi7 natural: loc=(7-4)*7+2-2=21 -> 6 linhas > 4 -> loc 14, 3 linhas, 8va"),
 ("15mb: muito grave na clave de sol fica presa em 4 linhas (limitação)", "satie.vsb", CH, [21], [R(-8, CH[0], None, 2, 4, "a", 0, 0)],
  "lá0 na clave de sol: loc=(0-4)*7+5-2=-25 (12 linhas); -18 (9), -11 (5) ainda > 4 com m=2 -> presa em -8 (4 linhas), 15mb"),
 ("8vb na clave de fá", "satie.vsb", [BASS], [21], [R(-6, BASS, None, 1, 3, "a", 0, 0)],
  "lá0 na clave de fá: loc=(0-4)*7+5+10=-13 (6 linhas) -> -6 (3 linhas), 8vb"),
 ("pausa e nota em pautas diferentes: vence a mais próxima (pausa)", "satie.vsb", [REST, BASS], [64], [R(0, REST, None, 0, 0, "e", 4, 0)],
  "linha do meio da clave de sol = si4 (71, dist 7); sol2 (43, dist 21) -> pausa; mi4: loc 0; x = o do glifo da pausa"),
 ("pausa e nota em pautas diferentes: vence a nota do baixo", "satie.vsb", [REST, BASS], [45], [R(1, BASS, None, 0, 0, "a", 2, 0)],
  "lá2 (45): dist 2 do sol2 -> baixo; lá2 na clave de fá: loc=(2-4)*7+5+10=1; |1-0|=1 com o sol2 real -> desloca"),
 ("sem armadura: sustenido se acima da nota esperada", "f01-clave-no-meio.vsb", ["f01-a"], [73], [R(5, "f01-a", "E262", 0, 0, "c", 5, 1)],
  "dó5 (72); 73 > 72 e sem armadura -> dó#5: loc=(5-4)*7+0-2=5; em vigor 0 -> ♯; = loc do dó5 real -> desloca"),
 ("sem armadura: bemol se abaixo da nota esperada", "f01-clave-no-meio.vsb", ["f01-a"], [70], [R(4, "f01-a", "E260", 0, 0, "b", 4, -1)],
  "70 < 72 e sem armadura -> si♭4: loc=0+6-2=4; ♭"),
 ("clave muda no meio do compasso", "f01-clave-no-meio.vsb", ["f01-c"], [50], [R(4, "f01-c", None, 0, 0, "d", 3, 0)],
  "após a clave de fá (co=10): ré3 loc=(3-4)*7+1+10=4"),
 ("8va escrita: a fantasma usa a altura escrita", "f02-oitavas.vsb", ["f02-a"], [86], [R(6, "f02-a", None, 0, 0, "d", 5, 0)],
  "dó5 sob 8va soa dó6 (sh=12); tecla 86 -> escrita 74 = ré5: loc=7+1-2=6"),
 ("8vb escrita", "f02-oitavas.vsb", ["f02-e"], [50], [R(-1, "f02-e", None, 0, 0, "d", 4, 0)],
  "dó4 sob 8vb soa dó3 (sh=-12); tecla 50 -> escrita 62 = ré4: loc=0+1-2=-1"),
 ("instrumento transpositor (clarinete em Si♭), tecla branca", "f03-transpositor.vsb", ["f03-b"], [77], [R(9, "f03-b", None, 0, 0, "g", 5, 0)],
  "sh=-2: som 77 -> escrita 79 = sol5 natural; loc=7+4-2=9; armadura de ré maior não altera sol"),
 ("instrumento transpositor, tecla preta", "f03-transpositor.vsb", ["f03-b"], [78], [R(9, "f03-b", "E262", 0, 0, "g", 5, 1)],
  "som 78 -> escrita 80 = sol#5 (armadura de sustenidos); em vigor 0 -> ♯"),
 ("cross-staff: a fantasma vai na pauta onde a nota está desenhada", "f04-cross-staff.vsb", ["f04-b"], [62], [R(11, "f04-b", None, 0, 1, "d", 4, 0)],
  "f04-b (mi4) é desenhada na pauta de baixo (clave de fá, co=10): ré4 loc=0+1+10=11 -> 1 linha acima da pauta"),
 ("armadura não padronizada (mista): sentido do erro", "f05-armadura-nao-padrao.vsb", ["f05-c"], [66], [R(2, "f05-c", "E260", 0, 0, "g", 4, -1)],
  "fá# e si♭ na armadura (mista) -> vale o sentido: 66 < 72 -> sol♭4 loc=0+4-2=2; em vigor sol=0 -> ♭"),
 ("armadura não padronizada: bemol já em vigor", "f05-armadura-nao-padrao.vsb", ["f05-c"], [70], [R(4, "f05-c", None, 0, 0, "b", 4, -1)],
  "70 < 72 -> si♭4 loc 4; a armadura já tem si♭ -> sem acidente"),
 ("mudança de armadura: sustenido já na nova armadura", "f06-mudanca-armadura.vsb", ["f06-k"], [68], [R(2, "f06-k", None, 0, 0, "g", 4, 1)],
  "compasso 3 tem 3 sustenidos (fá#, dó#, sol#): sol#4 loc 2, sem acidente"),
 ("mudança de armadura: bemol da nova armadura", "f06-mudanca-armadura.vsb", ["f06-q"], [68], [R(3, "f06-q", None, 0, 0, "a", 4, -1)],
  "compasso 5 tem 3 bemóis (si♭, mi♭, lá♭): 68 -> lá♭4 loc 3, sem acidente"),
 ("acidente escrito antes, em outra camada: bequadro necessário", "f07-acidentes.vsb", ["f07-c"], [65], [R(1, "f07-c", "E261", 0, 0, "f", 4, 0)],
  "fá#4 escrito antes na camada 1 (acc f4=+1); fá4 natural -> alt 0 != +1 -> ♮; loc = o do fá#4 real -> desloca"),
 ("acidente escrito antes no compasso: sustenido já em vigor", "f07-acidentes.vsb", ["f07-j"], [68], [R(2, "f07-j", None, 0, 0, "g", 4, 1)],
  "compasso 3 sem armadura; sol#4 escrito antes (acc g4=+1); 68 > 65 -> sol#4 loc 2; em vigor +1 -> sem acidente"),
 ("pausas e mRest em duas pautas: nota da outra pauta mais próxima", "f08-pausas.vsb", ["f08-mr1", "f08-mr2"], [50], [R(4, "f08-mr2", None, 0, 0, "d", 3, 0)],
  "mRest na clave de sol: linha do meio si4 (71, dist 21); na de fá: ré3 (50, dist 0) -> pauta de baixo; ré3 loc=(3-4)*7+1+10=4 = a linha do meio"),
 ("cross-staff: grave cabe no baixo, sem 8vb", "satie.vsb", CH + [BASS], [45], [R(1, BASS, None, 0, 0, "a", 2, 0)],
  "lá2 (45): na clave de sol loc=(2-4)*7+5-2=-11 (5 linhas); na clave de fá loc=-14+5+10=1 (0 linhas) -> baixo; |1-0|=1 com o sol2 real -> desloca"),
 ("cross-staff: proximidade diz sol, cabimento diz fá (a regra nova)", "satie.vsb", CH + [BASS], [55], [R(7, BASS, None, 0, 0, "g", 3, 0)],
  "sol3 (55): mais próximo do si3 (|55-59|=4 < |55-43|=12), mas na sol loc=(3-4)*7+4-2=-5 (2 linhas) e na fá loc=-7+4+10=7 (0) -> baixo; sol natural, sem acidente; |7-0|=7 sem colisão"),
 ("cross-staff: empate de cabimento decide pela proximidade", "satie.vsb", CH + [BASS], [60], [R(-2, CH[0], "E261", 0, 1, "c", 4, 0)],
  "dó4 na sol: loc=0+0-2=-2 (1 linha); na fá: loc=0+0+10=10 (1 linha); empate 1-1 -> proximidade (|60-59|=1 do si3 contra |60-43|=17) -> sol, coluna do si3; armadura tem dó# -> bequadro; |=1 com si3/ré4 -> desloca"),
 ("cross-staff: agudo extremo continua na sol com 8va", "satie.vsb", CH + [BASS], [100], [R(14, CH[2], None, 1, 3, "e", 7, 0)],
  "mi7 na sol: loc=21 (6 linhas); na fá: loc=(7-4)*7+2+10=33 (12 linhas) -> sol; 6 > 4 -> loc 14, 3 linhas, 8va"),
 ("cross-staff: grave extremo vai ao baixo com 8vb", "satie.vsb", CH + [BASS], [21], [R(-6, BASS, None, 1, 3, "a", 0, 0)],
  "lá0 na sol: loc=(0-4)*7+5-2=-25 (12 linhas); na fá: loc=-28+5+10=-13 (6 linhas) -> baixo; 6 > 4 -> loc -6, 3 linhas, 8vb (pela regra antiga ficaria presa em 15mb na sol)"),
 ("cross-staff: duas fantasmas, uma em cada pauta", "satie.vsb", CH + [BASS], [45, 100], [R(1, BASS, None, 0, 0, "a", 2, 0), R(14, CH[2], None, 1, 3, "e", 7, 0)],
  "45 -> baixo (0 linhas contra 5 na sol), 100 -> sol com 8va (6 contra 12 no baixo); pautas distintas, sem colisão entre si"),
]

vectors = dict(
    _comentario="G04d: vetores de teste da nota fantasma (§10). `resumo` escrito à mão; `fantasmas` gerado por compare/scripts/ghost_ref.py depois de conferir o resumo. Tolerância dos números: 0,5 unidade de viewBox.",
    accGapPerUnit=GAP, casos=[])
gr.ACC_GAP_PER_UNIT = GAP
docs = {}
bad = 0
for nome, vsb, ids, keys, resumo, conta in CASES:
    doc = docs.setdefault(vsb, gr.Vsb(os.path.join(OUT, vsb)))
    got = gr.ghosts(doc, ids, keys)
    for g, want in zip(got, resumo):
        mine = dict(loc=g["loc"], m=g["m"], accid=(g["accid"]["g"].split(":")[1] if g["accid"] else None),
                    ledgers=len(g["ledgers"]), pname=g["pname"], oct=g["oct"], alt=g["alt"], target=g["target"])
        if mine != want:
            print("CONTA NÃO BATE:", nome, "tecla", g["key"], "\n  escrito à mão:", want, "\n  referência  :", mine); bad += 1
    if len(got) != len(resumo):
        print("nº de teclas:", nome); bad += 1
    resumo = [dict(r, staff=g["staff"]) for r, g in zip(resumo, got)]
    vectors["casos"].append(dict(nome=nome, vsb=vsb, esperados=ids, teclas=keys, conta=conta, resumo=resumo,
                                 fantasmas=json.loads(json.dumps(got))))
if bad:
    sys.exit("%d divergências entre as contas à mão e a referência — nada gravado" % bad)
with open(os.path.join(OUT, "vetores.json"), "w") as f:
    json.dump(vectors, f, ensure_ascii=False, indent=1)
print("%d casos gravados em %s" % (len(CASES), os.path.relpath(os.path.join(OUT, "vetores.json"), ROOT)))
