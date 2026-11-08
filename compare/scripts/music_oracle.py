#!/usr/bin/env python3
"""Oráculo do `music.json` (M07, `docs/plano/M00-dados-musicais-para-o-aprendizado.md`).

Confere o bloco `music` que o Verovio deste repositório exporta (`-x 42 -t vsb-json`) contra a
fonte. A fonte é o oráculo: o que está sendo verificado é o Verovio, não a leitura do app.

- MusicXML (`.musicxml`, `.mxl`): lido direto (ElementTree), sem o Verovio. Cada regra de tradução
  (barras, casas, cifra, apojatura, andamento, direção) segue o que o importador faz, lido em
  `verovio/src/iomusxml.cpp`; os textos de cifra (sufixo de `kind`, símbolos de alteração, graus
  que recebem `add`) são lidos desse fonte, não digitados aqui. Isso mede a exportação, não o
  dicionário de cifras em si.
- MEI (`.mei`): não há MusicXML de origem (corpus nativo). Confere-se só o que o próprio MEI
  exportado traz: compassos (`n`, barras, casa), eventos por (compasso, pauta, camada) com o
  tipo, o acorde, a apojatura e a quiáltera, cifras (texto), direções (texto), andamentos e
  ornamentos (com `measure`, `tstamp` e `startid` ou `null`, §2.9 regra 6). Partes, fórmula e
  armadura não são conferidas no MEI (saem em `nao_conferido`): as partes saem da origem do
  arquivo (§2.9 regra 5), e o oráculo só lê o MEI exportado.

Causas conhecidas (M00; registradas, não corrigidas): R3 (nota invisível, `print-object="no"`),
R2 (pauta de cifra em parte de duas pautas), R4 (`numeral`).

Uso:
  music_oracle.py verificar FONTE MUSIC.json [--relatorio ARQ.json]
  music_oracle.py varredura [--out compare/out/m07] [--jobs 4]
  music_oracle.py vetores [--out-dir docs/formato/musica/vetores] [--out compare/out/m07]

`verificar` imprime o relatório em JSON. `varredura` roda o Verovio em todas as fontes (corpus,
fixtures do aprendizado, os 600 hinos), confere cada uma e grava o resumo em `--out`.
`vetores` grava o `music.json` esperado das fixtures (só se o oráculo der zero divergência).
"""
import argparse, collections, glob, hashlib, json, math, os, re, shutil, subprocess, sys, zipfile
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
VEROVIO = os.path.join(ROOT, "verovio", "tools", "verovio")
RES = os.path.join(ROOT, "verovio", "data")
IMPORTER = os.path.join(ROOT, "verovio", "src", "iomusxml.cpp")
SEED = "42"
APREND = "/home/mauricio/IdeaProjects/zywny-aprendizado"
HINOS = "/home/mauricio/IdeaProjects/Hymn_Grabber/musicxml_simplificado"
MEI_NS = "http://www.music-encoding.org/ns/mei"
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"


def q(tag):
    return "{%s}%s" % (MEI_NS, tag)


# ------------------------------------------------------------------ tabelas lidas do importador

def tabelas_do_importador():
    src = open(IMPORTER, encoding="utf-8").read()

    def bloco(inicio, fim="};"):
        i = src.index(inicio)
        return src[i:src.index(fim, i)]

    par = r'\{ "([^"]+)", "([^"]*)" \}'
    kind_text = dict(re.findall(par, bloco("std::string MusicXmlInput::ConvertKindToText")))
    addable = {k: int(v) for k, v in re.findall(r'\{ "([^"]+)", (\d+) \}',
                                                 bloco("std::string MusicXmlInput::ConvertDegreeToText"))}
    sym = dict(re.findall(par, bloco("std::string MusicXmlInput::ConvertAlterToSymbol")))
    i = src.index("Alter2PlusMinus{")
    pm = dict(re.findall(par, src[i:src.index("};", i)]))
    return kind_text, addable, sym, pm


KIND_TEXT, FIRST_ADDABLE, ALTER_SYM, ALTER_PM = tabelas_do_importador()


def figuras_do_importador():
    """ConvertTypeToVerovioText: figura (`beat-unit`) -> glifo SMuFL, lido do fonte."""
    src = open(IMPORTER, encoding="utf-8").read()
    i = src.index("std::u32string MusicXmlInput::ConvertTypeToVerovioText")
    bloco = src[i:src.index("};", i)]
    return {k: chr(int(h, 16)) for k, h in re.findall(r'\{ "([^"]+)", U"\\x([0-9A-Fa-f]+)" \}', bloco)}


FIGURAS = figuras_do_importador()


def alter_simbolo(valor, plus_minus=False):
    """ConvertAlterToSymbol: com plus-minus, usa a tabela de sinais; senão, a de símbolos."""
    if plus_minus:
        return ALTER_PM.get(valor, valor)
    return ALTER_SYM.get(valor, valor)


# ------------------------------------------------------------------ leitura do MusicXML

def load_musicxml(path):
    if path.endswith(".mxl"):
        z = zipfile.ZipFile(path)
        cont = ET.fromstring(z.read("META-INF/container.xml"))
        full = next(rf.get("full-path") for rf in cont.iter() if rf.tag.split("}")[-1] == "rootfile")
        return ET.fromstring(z.read(full))
    return ET.parse(path).getroot()


def inteiro(texto, padrao=0):
    try:
        return int(texto.strip())
    except (AttributeError, ValueError):
        return padrao


def texto_cifra(h):
    """Texto que o importador monta para um <harmony> (ReadMusicXmlHarmony). None = não modelado."""
    root_step = (h.findtext("root/root-step") or "").strip()
    texto = root_step
    if not root_step:
        nr = h.find("numeral/numeral-root")
        if nr is not None:
            texto = nr.get("text") if nr.get("text") is not None else (nr.text or "")
        alter_el = h.find("numeral/numeral-alter")
    else:
        alter_el = h.find("root/root-alter")
    if alter_el is not None:
        texto += alter_simbolo((alter_el.text or "").strip())
    kind = h.find("kind")
    if kind is not None:
        kv = (kind.text or "").strip()
        if kind.get("use-symbols") == "yes":
            return None
        if kind.get("text") is not None and (kind.text or "") != "none":
            texto += kind.get("text")
        else:
            texto += KIND_TEXT.get(kv, "")
    grau = ""
    for d in h.findall("degree"):
        if grau == "":
            grau = "("
        tn = d.find("degree-type")
        tipo = (tn.text or "").strip() if tn is not None else ""
        vn = d.find("degree-value")
        if vn is None:
            grau += "?"
            continue
        valor = (vn.text or "").strip()
        if tn is not None and tn.get("text") is not None:
            grau += tn.get("text")
        elif tipo == "subtract":
            grau += "no"
        elif tipo == "add":
            kv = (h.findtext("kind") or "").strip()
            if kv in FIRST_ADDABLE and int(valor) >= FIRST_ADDABLE[kv]:
                grau += "add"
        an = d.find("degree-alter")
        alter = (an.text or "").strip() if an is not None else ""
        if alter != "0":
            grau += alter_simbolo(alter, an is not None and an.get("plus-minus") == "yes")
        grau += valor
    if grau != "":
        grau += ")"
    texto += grau
    bass = h.find("bass")
    if bass is not None:
        texto += "/" + (bass.findtext("bass-step") or "").strip() + alter_simbolo(
            (bass.findtext("bass-alter") or "").strip())
    return texto


def estilo_para_barra(valor, repeat):
    """ConvertStyleToRend: valor da barra (MEI) ou None (BARRENDITION_NONE)."""
    if valor == "dashed": return "dashed"
    if valor == "dotted": return "dotted"
    if valor == "light-light": return "dbl"
    if valor == "heavy-heavy": return "dblheavy"
    if valor == "light-heavy" and not repeat: return "end"
    if valor == "heavy": return "heavy"
    if valor == "none": return "invis"
    if valor == "heavy-light" and repeat: return "rptstart"
    if valor == "light-heavy" and repeat: return "rptend"
    if valor in ("regular", "short", "tick"): return "single"
    return None


def texto_andamento(words, met):
    """Texto que o importador grava no `tempo` (TextRendition + PrintMetronome). None se vazio."""
    base = "".join("".join(w.itertext()) for w in words)
    if met is None:
        return base or None
    out = base
    if words and base and not base[-1].isspace():
        out += " "
    paren = (met.get("parentheses") or "") in ("yes", "true", "1")
    if paren:
        out += "("
    elems = [c for c in met if c.tag in ("beat-unit", "beat-unit-dot", "per-minute")]
    primeiro = True
    for k, c in enumerate(elems):
        if c.tag == "beat-unit-dot":
            continue
        if not primeiro:
            out += " = "
        if c.tag == "beat-unit":
            out += FIGURAS.get((c.text or "").strip(), "")
            j = k + 1
            while j < len(elems) and elems[j].tag == "beat-unit-dot":
                out += " \uECB7"
                j += 1
        else:
            out += c.text or ""
        primeiro = False
    if paren:
        out += ")"
    return out or None


def grace_de(el):
    """`grace` como o MEI o grava: apojatura (sem barra) = "acc" (acentuada); acciaccatura (barra) = "unacc".
    É o mapeamento de `ReadMusicXmlNote` (iomusxml.cpp L3370-3377). A R1 do M02 (inversão) não se confirmou."""
    if el is None:
        return False
    return "unacc" if (el.get("slash") or "") in ("yes", "true", "1") else "acc"


def espacos_da_lacuna(dur, ppq):
    """FillSpace (iomusxml.cpp L559): a lacuna de `dur` (em divisões) vira pedaços de até 2 semibreves
    (potência de 2 de semínimas, no máximo 2); cada pedaço é um `space`. Devolve a quantidade."""
    n, d = 0, int(dur)           # `dur` é int no importador: a subtração trunca (1 divisão vira 1 pedaço)
    while d > 0 and n < 100000:
        q = d / ppq
        q = 2 ** math.floor(math.log2(q))
        if q > 2:
            q = 2
        d = int(d - ppq * q)
        n += 1
    return n


def chave_sig(fifths):
    if fifths is None:
        return None
    if fifths == 0:
        return "0"
    if 1 <= fifths <= 7:
        return "%ds" % fifths
    if -7 <= fifths <= -1:
        return "%df" % -fifths
    return None


def meter_de(time_el):
    sym = time_el.get("symbol")
    return {"count": inteiro(time_el.findtext("beats")), "unit": inteiro(time_el.findtext("beat-type")),
            "sym": sym if sym in ("common", "cut") else None}


def key_de(key_el):
    fifths_txt = key_el.findtext("fifths")
    fifths = inteiro(fifths_txt, None) if fifths_txt is not None else None
    mode = (key_el.findtext("mode") or "").strip() or None
    return {"sig": chave_sig(fifths), "fifths": fifths, "mode": mode}


def esperado_musicxml(path):
    """Estrutura esperada do music.json, com os campos do oráculo; ids e posições são internos."""
    root = load_musicxml(path)
    score_parts = list(root.iter("score-part"))
    bodies = {p.get("id"): p for p in root.findall("part")}
    partes, offset = [], 0
    pinfo = []   # (body, offset, staves, pid)
    for sp in score_parts:
        pid = sp.get("id")
        body = bodies[pid]
        staves = 1
        for att in body.iter("attributes"):
            if att.findtext("staves"):
                staves = max(staves, inteiro(att.findtext("staves"), 1))
        for n in body.iter("note"):
            staves = max(staves, inteiro(n.findtext("staff"), 1))
        name = (sp.findtext("part-name") or "").strip() or None
        partes.append({"id": pid, "name": name, "staves": list(range(offset + 1, offset + staves + 1))})
        pinfo.append((body, offset, staves, pid))
        offset += staves

    ev = collections.defaultdict(list)        # (mi, staff, layer) -> eventos
    uid_loc = {}                              # uid -> (mi, staff, layer, idx)
    ornaments = []                            # (kind, uid)
    harm, dirs, tempi = [], [], []
    n_invis = collections.Counter()           # (mi, staff, layer) com nota invisível
    start_meter, start_key = {}, {}
    uid = 0
    grupo_seq = 0
    medidas_p1 = list(pinfo[0][0].findall("measure")) if pinfo else []
    n_medidas_partes = {}

    for pi, (body, off, staves, pid) in enumerate(pinfo):
        primeira = pi == 0
        divisions = 1
        unit = 4
        estado_meter = None
        estado_key = None
        last_grupo = {}
        fim = {}           # fim da camada no compasso (m_layerEndTimes; por compasso, como no importador)
        tup_open = {}      # colchete de quiáltera aberto por contêiner (camada) no compasso
        chord_tup = {}     # quiáltera da última nota de início de acorde, por contêiner
        mlist = body.findall("measure")
        n_medidas_partes[pid] = len(mlist)
        for mi, m in enumerate(mlist):
            cursor = 0
            snap = False
            fim.clear()
            tup_open.clear()
            chord_tup.clear()
            seg = None

            def snapshot():
                if primeira and not snap_flag[0]:
                    start_meter[mi] = dict(estado_meter) if estado_meter else None
                    start_key[mi] = dict(estado_key) if estado_key else None
                    snap_flag[0] = True
            snap_flag = [False]
            for child in m:
                tag = child.tag
                if tag in ("note", "backup", "forward") and primeira:
                    snapshot()
                if tag == "attributes":
                    if child.findtext("divisions"):
                        divisions = inteiro(child.findtext("divisions"), divisions)
                    tm = child.find("time")
                    if tm is not None:
                        mt = meter_de(tm)
                        unit = mt["unit"] or unit
                        if primeira:
                            estado_meter = mt
                    for k in child.findall("key"):
                        if k.get("number") in (None, "1"):
                            kd = key_de(k)
                            if primeira:
                                estado_key = kd
                elif tag == "backup":
                    cursor -= inteiro(child.findtext("duration"))
                    seg = None
                elif tag == "forward":
                    cursor += inteiro(child.findtext("duration"))
                elif tag == "harmony":
                    ts = (cursor + inteiro(child.findtext("offset"))) * unit / (4.0 * divisions) + 1.0
                    kind_el = child.find("kind")
                    harm.append({"m": mi, "staff": off + 1, "tstamp": ts,
                                 "root": (child.findtext("root/root-step") or "").strip() or None,
                                 "rootAlter": inteiro(child.findtext("root/root-alter")),
                                 "kind": (kind_el.text or "").strip() if kind_el is not None else None,
                                 "kindText": (kind_el.get("text") or None) if kind_el is not None else None,
                                 "bass": (child.findtext("bass/bass-step") or "").strip() or None,
                                 "bassAlter": inteiro(child.findtext("bass/bass-alter"))
                                 if child.find("bass") is not None else None,
                                 "degrees": [{"value": inteiro(d.findtext("degree-value")),
                                              "alter": inteiro(d.findtext("degree-alter")),
                                              "type": (d.findtext("degree-type") or "").strip()}
                                             for d in child.findall("degree")],
                                 "numeral": None,
                                 "text": texto_cifra(child)})
                    if child.find("numeral") is not None and child.find("root") is None:
                        nr = child.find("numeral/numeral-root")
                        harm[-1]["numeral"] = {"root": nr.get("text") if nr.get("text") is not None else (nr.text or ""),
                                               "alter": inteiro(child.findtext("numeral/numeral-alter"))}
                        harm[-1]["root"] = None
                elif tag == "direction":
                    snd = child.find("sound")
                    words = child.findall("direction-type/words")
                    tem_dyn = child.find("direction-type/dynamics") is not None or (
                        snd is not None and snd.get("dynamics") is not None)
                    tem_tempo = child.find("direction-type/metronome") is not None or (
                        snd is not None and snd.get("tempo") is not None)
                    texto = "".join("".join(w.itertext()) for w in words)
                    if tem_tempo:
                        bpm = float(snd.get("tempo")) if snd is not None and snd.get("tempo") is not None else None
                        met = next((x for x in child.findall("direction-type/metronome")
                                    if x.get("print-object") != "no"), None)
                        tempi.append({"m": mi, "bpm": bpm, "text": texto_andamento(words, met)})
                    elif words and texto != "" and not tem_dyn:   # <words> vazio não vira `dir`
                        primeiro = "".join(words[0].itertext())
                        if primeiro.startswith(("cresc", "dim", "decresc")):
                            pass   # o importador trata como dinâmica
                        else:
                            st = child.find("staff")
                            dirs.append({"m": mi, "staff": (off + inteiro(st.text, 1)) if st is not None else off + 1,
                                         "tstamp": (cursor + inteiro(child.findtext("offset"))) * unit / (4.0 * divisions) + 1.0,
                                         "place": child.get("placement"), "text": texto})
                elif tag == "note":
                    is_rest = child.find("rest") is not None
                    invis = child.get("print-object") == "no"
                    is_chord = child.find("chord") is not None
                    grace_el = child.find("grace")
                    staff = off + inteiro(child.findtext("staff"), 1)
                    voice = inteiro(child.findtext("voice"), 1)
                    dur = inteiro(child.findtext("duration"))
                    if is_rest:
                        rest = child.find("rest")
                        if invis:
                            t = "s"
                        elif child.find("type") is None or rest.get("measure") == "yes":
                            t = "mr"
                        else:
                            t = "r"
                    else:
                        t = "n"
                    tm_el = child.find("time-modification")
                    own = None
                    if tm_el is not None and tm_el.findtext("actual-notes") and tm_el.findtext("normal-notes"):
                        own = {"num": inteiro(tm_el.findtext("actual-notes")),
                               "numbase": inteiro(tm_el.findtext("normal-notes"))}
                    # SelectLayer (iomusxml.cpp L470): a camada é a da 1ª nota desde o começo do compasso ou
                    # do último <backup>; as notas seguintes entram nela, mesmo com outra pauta no <staff>.
                    # O @staff do nó continua o da nota (M01: nota cruzada). Por isso há duas chaves:
                    # ckey = contêiner (fim de camada, lacunas, acordes); chave = pauta do nó + camada do contêiner.
                    if seg is None:
                        seg = (staff, voice)
                    ckey = (mi, seg[0], seg[1])
                    chave = (mi, staff, seg[1])
                    if is_chord and ckey in last_grupo:
                        grupo = last_grupo[ckey]
                    else:
                        grupo_seq += 1
                        grupo = grupo_seq
                        last_grupo[ckey] = grupo
                    # colchete de quiáltera (<notations><tuplet>): o importador põe no Tuplet aberto da camada
                    # tudo o que entra enquanto ele está aberto (inclusive apojatura sem time-modification)
                    tuplets_nt = [t for nt in child.findall("notations") if nt.get("print-object") != "no"
                                  for t in nt.findall("tuplet")]
                    # ReadMusicXmlTupletStart (iomusxml.cpp L4325): a razão vem de <tuplet-actual>/<tuplet-normal>
                    # do próprio <tuplet>, senão da time-modification da nota de início. Sem colchete, sem quiáltera.
                    inicio = next((t for t in tuplets_nt if t.get("type") == "start"), None)
                    if inicio is not None:
                        ta = inteiro(inicio.findtext("tuplet-actual/tuplet-number"), 0)
                        tn = inteiro(inicio.findtext("tuplet-normal/tuplet-number"), 0)
                        razao = {"num": ta, "numbase": tn} if ta and tn else own
                        if razao is not None:
                            tup_open[ckey] = razao
                        else:
                            tup_open.pop(ckey, None)
                    # nota de acorde fica no acorde que começou: herda a quiáltera dele, mesmo que o colchete
                    # tenha fechado na nota de início (o Tuplet do acorde continua aberto)
                    if is_chord and ckey in chord_tup:
                        tup = chord_tup[ckey]
                    else:
                        tup = tup_open.get(ckey)
                        chord_tup[ckey] = tup
                    if any(t.get("type") == "stop" for t in tuplets_nt):
                        tup_open.pop(ckey, None)
                    uid += 1
                    if invis and not is_rest:
                        n_invis[chave] += 1
                    if not is_chord:   # só o começo de nota/pausa passa por AddLayerElement
                        fim_ant = fim.get(ckey, 0)
                        if fim_ant < cursor:
                            for _ in range(espacos_da_lacuna(cursor - fim_ant, divisions)):
                                ev[ckey].append({"t": "s", "grupo": None, "grace": False, "tuplet": None,
                                                 "invis": False, "uid": None, "preench": True})
                        fim[ckey] = cursor + (0 if grace_el is not None else dur)
                    lista = ev[chave]
                    uid_loc[uid] = (chave, len(lista))
                    lista.append({"t": t, "grupo": grupo, "grace": grace_de(grace_el), "tuplet": tup,
                                  "invis": invis, "uid": uid})
                    if grace_el is None and not is_chord:
                        cursor += dur
                    for nt in child.findall("notations"):
                        if nt.get("print-object") == "no":
                            continue
                        orn = nt.find("ornaments")
                        if orn is None:
                            continue
                        if orn.find("trill-mark") is not None or orn.find("wavy-line[@type='start']") is not None:
                            ornaments.append(("trill", uid))
                        for c in orn:
                            if "mordent" in c.tag:
                                ornaments.append(("mordent", uid))
                            if "turn" in c.tag:
                                ornaments.append(("turn", uid))
        if not primeira:
            continue
        # fim do loop de compassos da primeira parte
    # --- barras e casas (primeira parte)
    left, right, ending = {}, {}, {}
    atual = None
    for mi, m in enumerate(medidas_p1):
        for bl in m.findall("barline"):
            loc = bl.get("location") or "right"
            style = (bl.findtext("bar-style") or "").strip()
            rep = bl.find("repeat") is not None
            rend = estilo_para_barra(style, rep) if style else None
            if style:
                if loc == "left":
                    left[mi] = rend
                elif loc != "middle":
                    right[mi] = rend
            elif rep:
                if loc == "left":
                    left[mi] = "rptstart"
                elif loc != "middle":
                    right[mi] = "rptend"
            en = bl.find("ending")
            if en is not None:
                num = en.get("number") or ""
                if en.get("type") == "start":
                    later = any(ending_num_stop(medidas_p1[j], num) for j in range(mi, len(medidas_p1)))
                    if later:
                        atual = num
        ending[mi] = atual
        for bl in m.findall("barline"):
            en = bl.find("ending")
            if en is not None and en.get("type") in ("stop", "discontinue"):
                atual = None
    # --- compassos
    medidas = []
    for mi, m in enumerate(medidas_p1):
        staves_out = []
        conta_m = collections.Counter()      # notas por acorde no compasso (um acorde pode cruzar pautas)
        for (k_mi, _, _), lst in ev.items():
            if k_mi == mi:
                for x in lst:
                    if x["grupo"] is not None:
                        conta_m[x["grupo"]] += 1
        for sg in sorted({k[1] for k in ev if k[0] == mi}):
            layers_out = []
            for lv in sorted({k[2] for k in ev if k[0] == mi and k[1] == sg}):
                lista = ev[(mi, sg, lv)]
                grupos = {}
                evs = []
                for e in lista:
                    lab = None
                    if e["grupo"] is not None and conta_m[e["grupo"]] > 1:
                        lab = grupos.setdefault(e["grupo"], "c%d" % (len(grupos) + 1))
                    evs.append({"t": e["t"], "chord": lab, "grace": e["grace"], "tuplet": e["tuplet"],
                                "invis": e["invis"], "uid": e["uid"], "grupo": e["grupo"],
                                "preench": e.get("preench", False)})
                layers_out.append({"n": lv, "events": evs})
            staves_out.append({"n": sg, "layers": layers_out})
        medidas.append({"n": m.get("number"), "left": left.get(mi), "right": right.get(mi),
                        "ending": {"n": ending[mi]} if ending.get(mi) else None,
                        "meter": start_meter.get(mi), "key": start_key.get(mi), "staves": staves_out})

    # ornamentos: posição (compasso, pauta, camada, índice do início do acorde)
    orn_out = []
    for kind, u in ornaments:
        chave, idx = uid_loc[u]
        lista = ev[chave]
        g = lista[idx]["grupo"]
        ini = next(i for i, e in enumerate(lista) if e["grupo"] == g) if g is not None else idx
        orn_out.append({"kind": kind, "loc": [chave[0], chave[1], chave[2], ini]})
    return {"version": 1, "parts": partes, "measures": medidas, "harmonies": harm,
            "directions": dirs, "tempi": tempi, "ornaments": orn_out,
            "_medidas_por_parte": n_medidas_partes}


def ending_num_stop(m, num):
    for bl in m.findall("barline"):
        en = bl.find("ending")
        if en is not None and en.get("number") == num and en.get("type") in ("stop", "discontinue"):
            return True
    return False


# ------------------------------------------------------------------ leitura do MEI (parcial)

def esperado_mei(path):
    root = ET.parse(path).getroot()
    # só o corpo da partitura: o <incip> do cabeçalho traz compassos que não são a música
    cuerpo = root.find(".//{%s}body" % MEI_NS)
    parent = {c: p for p in cuerpo.iter() for c in p}

    def anc(el, tag):
        p = parent.get(el)
        while p is not None:
            if p.tag == q(tag):
                return p
            p = parent.get(p)
        return None

    measures = list(cuerpo.iter(q("measure")))
    midx = {m: i for i, m in enumerate(measures)}

    def mi_de(el):
        m = anc(el, "measure")
        return midx.get(m)

    medidas_e = []
    for i, m in enumerate(measures):
        en = anc(m, "ending")
        medidas_e.append({"n": m.get("n"), "left": m.get("left"), "right": m.get("right"),
                          "ending": {"n": en.get("n")} if en is not None else None, "staves": []})
    # <tupletSpan> (startid..endid): as notas do intervalo, na ordem do documento, têm a razão do span
    xid = {el.get(XML_ID): el for el in cuerpo.iter() if el.get(XML_ID)}
    ordem = [el for el in cuerpo.iter() if el.tag in (q("note"), q("rest"), q("mRest"), q("space"))]
    pos = {id(el): i for i, el in enumerate(ordem)}
    span_de = {}
    for ts in cuerpo.iter(q("tupletSpan")):
        a = xid.get((ts.get("startid") or "").lstrip("#"))
        b = xid.get((ts.get("endid") or "").lstrip("#"))
        if a is None or b is None or not (ts.get("num") and ts.get("numbase")):
            continue
        # início/fim num acorde: a primeira/última nota dele
        na = [x for x in a.iter() if id(x) in pos]
        nb = [x for x in b.iter() if id(x) in pos]
        if not na or not nb:
            continue
        for k in range(pos[id(na[0])], pos[id(nb[-1])] + 1):
            span_de[id(ordem[k])] = {"num": int(ts.get("num")), "numbase": int(ts.get("numbase"))}
    ev = collections.defaultdict(list)
    for layer in cuerpo.iter(q("layer")):
        m = anc(layer, "measure")
        if m is None:
            continue
        mi = midx[m]
        st = anc(layer, "staff")
        sg = int(st.get("n") or 1) if st is not None else 1
        lv = int(layer.get("n") or 1)
        for el in layer.iter():
            if el.tag not in (q("note"), q("rest"), q("mRest"), q("space")):
                continue
            staff_el = int(el.get("staff") or sg) if el.tag == q("note") else sg
            # grace: só "acc"/"unacc" contam; "unknown" (o @grace de notas de Scarlatti/Chopin) sai como false
            if el.tag == q("note"):
                t = "n"
                grace = el.get("grace") if el.get("grace") in ("acc", "unacc") else False
                if not grace:
                    gg = anc(el, "graceGrp")
                    grace = (gg.get("grace") if gg is not None and gg.get("grace") in ("acc", "unacc") else False)
            elif el.tag == q("rest"):
                t, grace = "r", False
            elif el.tag == q("mRest"):
                t, grace = "mr", False
            else:
                t, grace = "s", False
            ch = anc(el, "chord")
            tu = anc(el, "tuplet")
            tup = None
            if tu is not None and tu.get("num") and tu.get("numbase"):
                tup = {"num": int(tu.get("num")), "numbase": int(tu.get("numbase"))}
            elif id(el) in span_de:
                tup = span_de[id(el)]
            ev[(mi, staff_el, lv)].append({"t": t, "grupo": ch.get(XML_ID) if ch is not None else None,
                                            "grace": grace, "tuplet": tup, "invis": False,
                                            "uid": el.get(XML_ID)})
    for mi in range(len(medidas_e)):
        staves_out = []
        for sg in sorted({k[1] for k in ev if k[0] == mi}):
            layers_out = []
            for lv in sorted({k[2] for k in ev if k[0] == mi and k[1] == sg}):
                lista = ev[(mi, sg, lv)]
                grupos = {}
                evs = []
                for e in lista:
                    lab = None
                    if e["grupo"] is not None:
                        lab = grupos.setdefault(e["grupo"], "c%d" % (len(grupos) + 1))
                    evs.append(dict(e, chord=lab))
                layers_out.append({"n": lv, "events": evs})
            staves_out.append({"n": sg, "layers": layers_out})
        medidas_e[mi]["staves"] = staves_out
    harm, dirs, tempi, orn = [], [], [], []
    for h in cuerpo.iter(q("harm")):
        mi = mi_de(h)
        st = anc(h, "staff")
        harm.append({"m": mi, "staff": int(h.get("staff") or (st.get("n") if st is not None else 1)),
                     "tstamp": float(h.get("tstamp") or 1), "root": None, "rootAlter": None, "kind": None,
                     "kindText": None, "bass": None, "bassAlter": None, "degrees": [], "numeral": None,
                     "text": "".join(h.itertext()).strip()})
    for d in cuerpo.iter(q("dir")):
        mi = mi_de(d)
        st = anc(d, "staff")
        dirs.append({"m": mi, "staff": int(d.get("staff") or (st.get("n") if st is not None else 1)),
                     "tstamp": float(d.get("tstamp") or 1), "place": d.get("place"),
                     "text": "".join(d.itertext()).strip()})
    for tp in cuerpo.iter(q("tempo")):
        bpm = tp.get("midi.bpm")
        tempi.append({"m": mi_de(tp), "bpm": float(bpm) if bpm else None,
                      "text": "".join(tp.itertext()).strip() or None})
    for name in ("trill", "mordent", "turn"):
        for o in cuerpo.iter(q(name)):
            sid = (o.get("startid") or "").lstrip("#")
            ts = o.get("tstamp")
            orn.append({"kind": name, "startid": sid or None, "measure": mi_de(o),
                        "tstamp": float(ts) if ts and float(ts) >= 1 else None})
    return {"version": 1, "parts": None, "measures": medidas_e, "harmonies": harm, "directions": dirs,
            "tempi": tempi, "ornaments": None, "_ornaments_mei": orn}


# ------------------------------------------------------------------ comparação

def normaliza_fim(e):
    return None if e is None else re.sub(r"\s+", "", str(e))


def loc_de_startid(music, sid):
    """Posição (compasso, pauta, camada, índice) do evento com o id (ou do acorde) `sid`."""
    for mi, m in enumerate(music["measures"]):
        for st in m["staves"]:
            for ly in st["layers"]:
                for i, e in enumerate(ly["events"]):
                    if e.get("id") == sid:
                        return [mi, st["n"], ly["n"], i]
    for mi, m in enumerate(music["measures"]):
        for st in m["staves"]:
            for ly in st["layers"]:
                for i, e in enumerate(ly["events"]):
                    if e.get("chord") == sid:
                        return [mi, st["n"], ly["n"], i]
    return None


def normaliza_music(music):
    """Cópia do `music` com os ids de acorde trocados por rótulos c1, c2... (por camada, na ordem)."""
    out = dict(music)
    ms = []
    for m in music["measures"]:
        st = []
        for s in m["staves"]:
            ls = []
            for ly in s["layers"]:
                mapa, evs = {}, []
                for e in ly["events"]:
                    c = e.get("chord")
                    lab = mapa.setdefault(c, "c%d" % (len(mapa) + 1)) if c is not None else None
                    evs.append(dict(e, chord=lab))
                ls.append({"n": ly["n"], "events": evs})
            st.append({"n": s["n"], "layers": ls})
        ms.append(dict(m, staves=st))
    out["measures"] = ms
    return out


def num_igual(a, b, conf):
    """Números do JSON: o exportador grava 6 algarismos significativos (tstamp 1.16667 para 1.1666667).
    Diferença dentro de 5e-6 relativa conta como igual, e é contada em `arredondados_6_algarismos`."""
    if a is None or b is None:
        return a is b
    d = abs(a - b)
    if d <= 1e-9:
        return True
    if d <= 5e-6 * max(1.0, abs(a)):
        conf["arredondados_6_algarismos"] += 1
        return True
    return False


def norm_txt(x):
    """MEI: espaços e quebras do arquivo não contam (o texto vem indentado)."""
    if x is None:
        return None
    return re.sub(r"\s+", " ", x).strip() or None


def verifica(exp, music, eh_mei, fonte, tm_ids=None):
    """Compara o esperado com o `music` do Verovio. Devolve o relatório (dict)."""
    divs = []          # (categoria, caminho, esperado, obtido, causa)
    conf = collections.Counter()
    causas = collections.Counter()

    def dif(cat, caminho, e, o, causa=None):
        divs.append({"categoria": cat, "caminho": caminho, "esperado": e, "obtido": o, "causa": causa})
        causas[causa or "nova"] += 1

    if eh_mei:
        for h in music.get("harmonies", []):
            h["text"] = norm_txt(h.get("text"))
        for d in music.get("directions", []):
            d["text"] = norm_txt(d.get("text"))
        for t in music.get("tempi", []):
            t["text"] = norm_txt(t.get("text"))
        for h in exp["harmonies"]:
            h["text"] = norm_txt(h.get("text"))
        for d in exp["directions"]:
            d["text"] = norm_txt(d.get("text"))
        for t in exp["tempi"]:
            t["text"] = norm_txt(t.get("text"))

    # invisíveis por (compasso, pauta, camada) do esperado
    invis_loc = set()
    for m_i, m in enumerate(exp["measures"]):
        for st in m["staves"]:
            for ly in st["layers"]:
                if any(e.get("invis") for e in ly["events"]):
                    invis_loc.add((m_i, st["n"], ly["n"]))

    # partes
    if not eh_mei:
        conf["partes"] = len(exp["parts"])
        if exp["parts"] != music.get("parts"):
            dif("partes", "parts", exp["parts"], music.get("parts"))
        contagens = exp.get("_medidas_por_parte", {})
        if len(set(contagens.values())) > 1:
            dif("partes.compassos", "measures por parte", contagens, None)

    # compassos
    ma, me = normaliza_music(music)["measures"], exp["measures"]
    if len(ma) != len(me):
        dif("contagem", "measures", len(me), len(ma))
    # compassos depois da primeira barra final (right="end"): regra do M00 (não entram no timemap)
    fim_i = next((i for i, m in enumerate(me) if m.get("right") == "end"), None)
    depois_fim = set(range(fim_i + 1, len(me))) if fim_i is not None else set()
    conf["compassos"] = min(len(ma), len(me))
    for i, (a, b) in enumerate(zip(me, ma)):
        campos = ["n", "left", "right"]
        for c in campos:
            conf["campos"] += 1
            if (a.get(c) or None) != (b.get(c) or None):
                dif("compasso." + c, "measures[%d].%s" % (i, c), a.get(c), b.get(c))
        conf["campos"] += 1
        ea = normaliza_fim(a["ending"]["n"]) if a.get("ending") else None
        eb = normaliza_fim(b["ending"]["n"]) if b.get("ending") else None
        if ea != eb:
            dif("compasso.ending", "measures[%d].ending" % i, a.get("ending"), b.get("ending"))
        if not eh_mei:
            for c in ("meter", "key"):
                conf["campos"] += 1
                if a.get(c) != b.get(c):
                    dif("compasso." + c, "measures[%d].%s" % (i, c), a.get(c), b.get(c))
        # eventos
        ea_st = {s["n"]: {l["n"]: l["events"] for l in s["layers"]} for s in a["staves"]}
        eb_st = {s["n"]: {l["n"]: l["events"] for l in s["layers"]} for s in b["staves"]}
        for sg in sorted(set(ea_st) | set(eb_st)):
            la, lb = ea_st.get(sg, {}), eb_st.get(sg, {})
            for lv in sorted(set(la) | set(lb)):
                xa = la.get(lv, [])
                xb = lb.get(lv, [])
                if not xa and not xb:
                    conf["camadas_vazias"] += 1
                    continue
                conf["camadas"] += 1
                if len(xa) != len(xb):
                    causa = "R3 nota invisível" if (i, sg, lv) in invis_loc else None
                    dif("evento.contagem", "measures[%d] staff %s layer %s" % (i, sg, lv), len(xa), len(xb), causa)
                    continue
                for j, (ea_, eb_) in enumerate(zip(xa, xb)):
                    conf["eventos"] += 1
                    for campo in ("t", "chord", "grace", "tuplet"):
                        # `space` de preenchimento: o tuplet dele vem do contêiner aberto no importador (viga ou
                        # quiáltera), não da partitura; não se confere (ver docstring de esperado_musicxml)
                        if campo == "tuplet" and ea_.get("preench"):
                            continue
                        if ea_.get(campo) != eb_.get(campo):
                            causa = "R3 nota invisível" if (i, sg, lv) in invis_loc else None
                            dif("evento." + campo, "measures[%d] staff %s layer %s ev %d" % (i, sg, lv, j),
                                ea_.get(campo), eb_.get(campo), causa)
    # não tocado = compasso que o timemap não toca (o id notado não aparece nele). Se não vem depois de
    # uma barra final, é divergência: o timemap deixou de tocar algo sem motivo visível na fonte.
    if tm_ids is not None:
        fora = [i for i in range(min(len(ma), len(me))) if ma[i].get("id") not in tm_ids]
        conf["nao_tocados"] = len(fora)
        conf["nao_tocados_apos_barra_final"] = len(depois_fim)
        conf["apos_barra_final_no_timemap"] = len(depois_fim) - len([i for i in fora if i in depois_fim])
        for i in fora:
            if i not in depois_fim:
                dif("nao_tocado.sem_barra_final", "measures[%d]" % i, "tocado pelo timemap", "fora do timemap")

    # ornamentos
    if not eh_mei:
        orn_e = []
        for o in exp["ornaments"]:
            orn_e.append((o["kind"], tuple(o["loc"])))
        orn_b = []
        for o in music.get("ornaments", []):
            loc = loc_de_startid(music, o["startid"])
            orn_b.append((o["kind"], tuple(loc) if loc else ("?", o["startid"])))
            # o compasso do controle é o do evento a que ele aponta
            if loc and o.get("measure") != loc[0]:
                dif("ornamento.compasso", "ornaments[%s].measure" % o["startid"], loc[0], o.get("measure"))
        conf["ornamentos"] = len(orn_e)
        if sorted(orn_e, key=str) != sorted(orn_b, key=str):
            dif("ornamento", "ornaments", sorted(orn_e, key=str), sorted(orn_b, key=str))
    else:
        # chave: (kind, startid ou "", compasso, tstamp arredondado; None = null)
        def chave_orn(kind, sid, mi, ts):
            return (kind, sid or "", mi, None if ts is None else float("%.5g" % ts))
        orn_e = sorted((chave_orn(o["kind"], o["startid"], o["measure"], o["tstamp"])
                        for o in exp["_ornaments_mei"]), key=str)
        orn_b = sorted((chave_orn(o["kind"], o.get("startid"), o["measure"], o.get("tstamp"))
                        for o in music.get("ornaments", [])), key=str)
        conf["ornamentos"] = len(orn_e)
        if orn_e != orn_b:
            dif("ornamento", "ornaments (MEI)", orn_e, orn_b)

    # cifras, direções, andamentos
    def ordena(lst, chaves):
        return sorted(lst, key=lambda x: tuple("" if x.get(k) is None else str(x.get(k)) for k in chaves))

    ch = ("m", "staff", "tstamp", "text")
    he = ordena(exp["harmonies"], ch)
    hb = ordena(music.get("harmonies", []), ("measure", "staff", "tstamp", "text"))
    conf["cifras"] = len(he)
    if len(he) != len(hb):
        dif("cifra.contagem", "harmonies", len(he), len(hb))
    for a, b in zip(he, hb):
        bm = b.get("measure")
        if a["m"] != bm:
            dif("cifra.compasso", "harmonies", a["m"], bm)
        if a["staff"] != b.get("staff"):
            dif("cifra.pauta", "harmonies", a["staff"], b.get("staff"))
        if not num_igual(a["tstamp"], b.get("tstamp"), conf):
            dif("cifra.tstamp", "harmonies", a["tstamp"], b.get("tstamp"))
        if eh_mei:
            for c in ("root", "kind", "bass", "numeral"):
                if b.get(c) is not None:
                    dif("cifra.estrutura_mei", "harmonies." + c, None, b.get(c))
            if b.get("degrees"):
                dif("cifra.estrutura_mei", "harmonies.degrees", [], b.get("degrees"))
            if (a["text"] or "") != (b.get("text") or "").strip():
                dif("cifra.texto", "harmonies.text", a["text"], b.get("text"))
            continue
        for c, ac in (("root", "root"), ("rootAlter", "rootAlter"), ("kind", "kind"), ("kindText", "kindText"),
                      ("bass", "bass"), ("bassAlter", "bassAlter"), ("degrees", "degrees"),
                      ("numeral", "numeral")):
            va, vb = a.get(ac), b.get(c)
            if c == "kindText" and vb == "":
                vb = None
            if c == "degrees":
                va = va or []
                vb = vb or []
            if c == "numeral" and va is None and vb is None:
                continue
            if va != vb:
                causa = "R4 (numeral)" if c == "numeral" or (a.get("numeral") or b.get("numeral")) else None
                dif("cifra." + c, "harmonies[%s].%s" % (a["m"], c), va, vb, causa)
        if a["text"] != b.get("text"):
            causa = "R4 (numeral)" if a.get("numeral") is not None else None
            dif("cifra.texto", "harmonies[%s]" % a["m"], a["text"], b.get("text"), causa)

    dh = ordena(exp["directions"], ("m", "staff", "tstamp", "text"))
    db = ordena(music.get("directions", []), ("measure", "staff", "tstamp", "text"))
    conf["direcoes"] = len(dh)
    if len(dh) != len(db):
        dif("direcao.contagem", "directions", len(dh), len(db))
    for a, b in zip(dh, db):
        if a["m"] != b.get("measure") or a["staff"] != b.get("staff") or not num_igual(a["tstamp"], b.get("tstamp"), conf):
            dif("direcao.posicao", "directions[%s]" % a["m"], [a["m"], a["staff"], a["tstamp"]],
                [b.get("measure"), b.get("staff"), b.get("tstamp")])
        if (a.get("place") or None) != (b.get("place") or None):
            dif("direcao.place", "directions[%s]" % a["m"], a.get("place"), b.get("place"))
        if (a["text"] or "") != (b.get("text") or "") and not (eh_mei and (a["text"] or "") == (b.get("text") or "").strip()):
            dif("direcao.texto", "directions[%s]" % a["m"], a["text"], b.get("text"))

    te = sorted(exp["tempi"], key=lambda x: (x["m"] if x["m"] is not None else -1, x.get("text") or "",
                                              x.get("bpm") or -1))
    tb = sorted(music.get("tempi", []), key=lambda x: (x.get("measure") or 0, x.get("text") or "", x.get("bpm") or -1))
    conf["andamentos"] = len(te)
    if len(te) != len(tb):
        dif("andamento.contagem", "tempi", len(te), len(tb))
    for a, b in zip(te, tb):
        if a["m"] != b.get("measure") or not num_igual(a.get("bpm"), b.get("bpm"), conf) or (a.get("text") or None) != (b.get("text") or None):
            dif("andamento", "tempi[%s]" % a["m"], [a["m"], a.get("bpm"), a.get("text")],
                [b.get("measure"), b.get("bpm"), b.get("text")])

    return {"fonte": fonte, "conferidos": dict(conf), "divergencias": divs, "causas": dict(causas),
            "nao_conferido": ["partes (regra por formato de origem, §2.9 regra 5)", "compasso.meter",
                              "compasso.key", "harmonies (estrutura: só o texto)"] if eh_mei else []}


def music_do_vsb_json(fonte, saida_json):
    """Roda o Verovio (-x 42 -t vsb-json). Devolve (bloco `music`, ids dos compassos no timemap)."""
    subprocess.run([VEROVIO, "--resource-path", RES, "-x", SEED, "-t", "vsb-json", "-o", saida_json, fonte],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    with open(saida_json, encoding="utf-8") as fh:
        d = json.load(fh)
    ids_tm = {re.sub(r"-rend\d+$", "", e["measureOn"]) for e in d.get("timemap", []) if e.get("measureOn")}
    return d["music"], ids_tm


def limpa(exp):
    """Remove campos internos do esperado antes de comparar."""
    out = dict(exp)
    out["measures"] = []
    for m in exp["measures"]:
        mm = dict(m)
        mm["staves"] = [{"n": s["n"], "layers": [{"n": l["n"], "events": [
            {k: v for k, v in e.items() if k not in ("uid", "grupo")} for e in l["events"]]}
            for l in s["layers"]]} for s in m["staves"]]
        out["measures"].append(mm)
    out["harmonies"] = [dict(h, m=h["m"]) for h in exp["harmonies"]]
    return out


def verificar(fonte, music=None, tm_ids=None):
    """`music` é o dict do bloco `music` ou o caminho de um `music.json`. `tm_ids`: compassos do timemap."""
    if isinstance(music, str):
        with open(music, encoding="utf-8") as fh:
            music = json.load(fh)
    if fonte.endswith(".mei"):
        return verifica(esperado_mei(fonte), music, True, os.path.basename(fonte), tm_ids=tm_ids)
    exp = esperado_musicxml(fonte)
    return verifica(limpa(exp), music, False, os.path.basename(fonte), tm_ids=tm_ids)


# ------------------------------------------------------------------ varredura

def fontes():
    """(grupo, slug, caminho) de cada fonte da varredura."""
    out = []
    for p in sorted(glob.glob(os.path.join(ROOT, "corpus/musicxml/*.mxl"))):
        out.append(("corpus-musicxml", "corpus-" + os.path.splitext(os.path.basename(p))[0], p))
    for p in sorted(glob.glob(os.path.join(ROOT, "corpus/mei/*.mei"))):
        out.append(("corpus-mei", "corpus-" + os.path.splitext(os.path.basename(p))[0], p))
    for n in ("ode", "intro", "menor", "recusa"):
        out.append(("aprendizado-fixture", "apr-" + n,
                    os.path.join(APREND, "test/music_reading/fixtures/src", n + ".musicxml")))
    for slug, rel in (("apr-twinkle-lead-sheet", "test/fixtures/cursos/lead-sheet/media/twinkle.musicxml"),
                      ("apr-contrafato-1", "test/fixtures/cursos/lead-sheet/media/contrafato-1.musicxml"),
                      ("apr-folclore-2", "test/fixtures/cursos/harmonia/media/folclore-2.musicxml")):
        out.append(("aprendizado-curso", slug, os.path.join(APREND, rel)))
    for p in sorted(glob.glob(os.path.join(HINOS, "*.musicxml"))):
        out.append(("hino", "hino-" + os.path.splitext(os.path.basename(p))[0], p))
    return out


def varre_um(item, out):
    grupo, slug, src = item
    music_dir = os.path.join(out, "music")
    os.makedirs(music_dir, exist_ok=True)
    tmp = os.path.join(out, "tmp-" + slug + ".json")
    try:
        music, tm_ids = music_do_vsb_json(src, tmp)
    except (subprocess.CalledProcessError, KeyError, json.JSONDecodeError) as e:
        return {"grupo": grupo, "slug": slug, "fonte": src, "erro": "verovio: %s" % e}
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    with open(os.path.join(music_dir, slug + ".music.json"), "w", encoding="utf-8") as fh:
        json.dump(music, fh, ensure_ascii=False)
    rel = verificar(src, music=music, tm_ids=tm_ids)
    rel["grupo"], rel["slug"] = grupo, slug
    return rel


def varredura(args):
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    rels = []
    itens = fontes()
    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        rels = list(ex.map(lambda it: varre_um(it, out), itens))
    os.makedirs(os.path.join(out, "relatorios"), exist_ok=True)
    for r in rels:
        with open(os.path.join(out, "relatorios", r["slug"] + ".json"), "w", encoding="utf-8") as fh:
            json.dump(r, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(out, "resumo.json"), "w", encoding="utf-8") as fh:
        json.dump(rels, fh, ensure_ascii=False, indent=1)
    print("%d fontes; relatórios em %s" % (len(rels), os.path.join(out, "relatorios")))
    return rels


# ------------------------------------------------------------------ vetores

FIXTURES_VETORES = [
    ("m02", os.path.join(ROOT, "docs/formato/musica/m02-entrada.musicxml"), "repositorio"),
    ("ode", os.path.join(APREND, "test/music_reading/fixtures/src/ode.musicxml"), "aprendizado"),
    ("intro", os.path.join(APREND, "test/music_reading/fixtures/src/intro.musicxml"), "aprendizado"),
    ("menor", os.path.join(APREND, "test/music_reading/fixtures/src/menor.musicxml"), "aprendizado"),
    ("recusa", os.path.join(APREND, "test/music_reading/fixtures/src/recusa.musicxml"), "aprendizado"),
    ("twinkle", os.path.join(APREND, "test/fixtures/cursos/lead-sheet/media/twinkle.musicxml"), "aprendizado"),
    ("contrafato-1", os.path.join(APREND, "test/fixtures/cursos/lead-sheet/media/contrafato-1.musicxml"),
     "aprendizado"),
    ("folclore-2", os.path.join(APREND, "test/fixtures/cursos/harmonia/media/folclore-2.musicxml"), "aprendizado"),
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for bloco in iter(lambda: fh.read(1 << 16), b""):
            h.update(bloco)
    return h.hexdigest()


def vetores(args):
    out = os.path.abspath(args.out)
    dst = os.path.abspath(args.out_dir)
    os.makedirs(out, exist_ok=True)
    os.makedirs(dst, exist_ok=True)
    casos, ruins = [], []
    for nome, src, origem in FIXTURES_VETORES:
        tmp = os.path.join(out, "vet-" + nome + ".json")
        music, _ = music_do_vsb_json(src, tmp)
        os.remove(tmp)
        rel = verificar(src, music=music)
        nd = len(rel["divergencias"])
        if nd:
            ruins.append((nome, nd))
            continue
        destino = os.path.join(dst, nome + ".music.json")
        with open(destino, "w", encoding="utf-8") as fh:
            json.dump(music, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        c = rel["conferidos"]
        casos.append({"nome": nome, "music": os.path.basename(destino), "origem": origem,
                      "fonte": os.path.basename(src) if origem == "repositorio" else
                      os.path.relpath(src, APREND),
                      "fonte_sha256": sha256(src),
                      "compassos": c.get("compassos"), "eventos": c.get("eventos", 0),
                      "cifras": c.get("cifras", 0), "direcoes": c.get("direcoes", 0),
                      "andamentos": c.get("andamentos", 0), "ornamentos": c.get("ornamentos", 0)})
    if ruins:
        print("NÃO gravado (divergência): %s" % ruins)
        return 1
    m02 = json.load(open(os.path.join(dst, "m02.music.json"), encoding="utf-8"))
    esp = json.load(open(os.path.join(ROOT, "docs/formato/musica/m02-esperado.json"), encoding="utf-8"))
    igual = m02 == esp
    indice = {"descricao": "Vetores do music.json (M07). Cada `music` foi gerado por `-x 42 -t vsb-json` do Verovio "
              "deste repositório e conferido contra a fonte pelo oráculo (zero divergência). As fontes dos "
              "aprendizado ficam em zywny-aprendizado (só leitura); `fonte_sha256` identifica a versão conferida.",
              "gerado_por": "compare/scripts/music_oracle.py vetores", "semente": SEED,
              "m02_igual_a_esperado": igual, "casos": casos}
    with open(os.path.join(dst, "vetores.json"), "w", encoding="utf-8") as fh:
        json.dump(indice, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("%d vetores gravados em %s; m02 igual a m02-esperado.json: %s" % (len(casos), dst, igual))
    return 0 if igual else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("verificar")
    v.add_argument("fonte")
    v.add_argument("music")
    v.add_argument("--relatorio")
    s = sub.add_parser("varredura")
    s.add_argument("--out", default=os.path.join(ROOT, "compare/out/m07"))
    s.add_argument("--jobs", type=int, default=4)
    g = sub.add_parser("vetores")
    g.add_argument("--out", default=os.path.join(ROOT, "compare/out/m07"))
    g.add_argument("--out-dir", default=os.path.join(ROOT, "docs/formato/musica/vetores"))
    args = ap.parse_args()
    if args.cmd == "verificar":
        rel = verificar(args.fonte, music=args.music)
        texto = json.dumps(rel, ensure_ascii=False, indent=1)
        if args.relatorio:
            open(args.relatorio, "w", encoding="utf-8").write(texto)
        print(texto)
        return 0
    if args.cmd == "varredura":
        varredura(args)
        return 0
    return vetores(args)


if __name__ == "__main__":
    sys.exit(main())
