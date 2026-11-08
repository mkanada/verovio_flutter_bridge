#!/usr/bin/env python3
"""Medições do M01 (M00, dados musicais): confirma os fatos de "Fatos medidos" e as perguntas 1-3.

Lê o MusicXML direto (o oráculo: é o Verovio que está sendo medido) e compara com o que o
Verovio exporta: `-t mei` (o `Doc` notado, com os ids) e `-t vsb-json` do MEI (a cena, o timemap
com ids estáveis, porque o MEI traz os `xml:id`). Não altera nada fora de `compare/out/m01/`.

Seções (cada uma imprime uma linha `[secao] ...` e vai para `resumo.json`):
  id     ids de parte (staffGrp/staffDef) e rótulo de layer = <voice>
  layers nº de compassos e notas/pausas por (compasso, pauta, voz)
  casas  <ending>, barras de repetição (left/right) e rótulo n dos compassos
  harm   <harmony>: quantos chegam ao Harm; kinds que ConvertKindToText não conhece
  words  <direction><words>: formatação (<rend>), várias <words> por direção, direção com tempo/dinâmica
  mode   <mode> no <key>: MusicXML × keySig@mode do MEI, e os dois casos sintéticos
  tm     compassos do MEI que o timemap não toca (barra final, D-TM)

Uso: m01-medicoes.py [--all-hymns] [--out compare/out/m01]
"""
import argparse, collections, glob, json, os, re, subprocess, sys, zipfile
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
VEROVIO = os.path.join(ROOT, "verovio", "tools", "verovio")
RESOURCE = os.path.join(ROOT, "verovio", "data")
IDIOMAS = "/home/mauricio/IdeaProjects"
APREND = os.path.join(IDIOMAS, "zywny-aprendizado")
HYMNS = os.path.join(IDIOMAS, "Hymn_Grabber", "musicxml_simplificado")
ITER_KIND_SRC = os.path.join(ROOT, "verovio", "src", "iomusxml.cpp")
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"


def local(tag):
    return tag.split("}")[-1]


def load_musicxml(path):
    if path.endswith(".mxl"):
        z = zipfile.ZipFile(path)
        cont = ET.fromstring(z.read("META-INF/container.xml"))
        full = next(rf.get("full-path") for rf in cont.iter() if local(rf.tag) == "rootfile")
        return ET.fromstring(z.read(full))
    return ET.parse(path).getroot()


def kinds_known():
    """Chaves de Kind2Text em ConvertKindToText (lidas da fonte, não copiadas)."""
    src = open(ITER_KIND_SRC, encoding="utf-8").read()
    i = src.index("std::string MusicXmlInput::ConvertKindToText")
    j = src.index("};", i)
    return set(re.findall(r'\{ "([^"]+)", "', src[i:j]))


def cli_mei(path, out_dir):
    """`-t mei` do arquivo (ids gerados pelo Verovio, gravados no MEI)."""
    base = os.path.basename(path).rsplit(".", 1)[0]
    if path.startswith(HYMNS):
        base = "hymn-" + base
    out = os.path.join(out_dir, "mei", base + ".mei")
    if not os.path.exists(out):
        subprocess.run([VEROVIO, "--resource-path", RESOURCE, "-t", "mei", "-o", out, path],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return out


def cli_vsb_json(mei_path, out_dir):
    out = os.path.join(out_dir, "vsbjson", os.path.basename(mei_path) + ".json")
    if not os.path.exists(out):
        subprocess.run([VEROVIO, "--resource-path", RESOURCE, "-t", "vsb-json", "-o", out, mei_path],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return json.load(open(out, encoding="utf-8"))


# ---------------------------------------------------------------- oracle (MusicXML)

def oracle(path):
    root = load_musicxml(path)
    parts = []
    for sp in root.iter("score-part"):
        parts.append({"id": sp.get("id"), "name": (sp.findtext("part-name") or "").strip()})
    body = {p.get("id"): p for p in root.findall("part")}
    staves_of = {}
    for pid, p in body.items():
        n = 1
        for att in p.iter("attributes"):
            if att.findtext("staves"):
                n = max(n, int(att.findtext("staves")))
        staves_of[pid] = n
    for part in parts:
        part["staves"] = staves_of.get(part["id"], 1)
    first = root.find("part")
    measures = first.findall("measure") if first is not None else []
    numbers = [m.get("number") for m in measures]
    implicit = sum(1 for m in measures if m.get("implicit") == "yes")
    nonint = [n for n in numbers if n is not None and not n.isdigit()]

    # notas e pausas por (compasso, pauta global, voz)
    counts = collections.Counter()
    voices = set()
    for pid, p in body.items():
        off = 0
        for part in parts:
            if part["id"] == pid:
                break
            off += part["staves"]
        for mi, m in enumerate(p.findall("measure")):
            for note in m.findall("note"):
                staff = int(note.findtext("staff") or 1)
                voice = int(note.findtext("voice") or 1)
                counts[(mi, off + staff, voice)] += 1
                voices.add(voice)

    harmonies = list(root.iter("harmony"))
    kinds = collections.Counter()
    kind_lost = collections.Counter()
    known = kinds_known()
    for h in harmonies:
        kind = h.find("kind")
        if kind is None:
            kinds["<sem kind>"] += 1
            continue
        value = (kind.text or "").strip()
        kinds[value] += 1
        has_text = kind.get("text") is not None
        if kind.get("use-symbols") == "yes":
            continue
        if has_text and (kind.text or "").strip() != "none":
            continue
        if value not in known:
            kind_lost[value] += 1

    dirs_words = 0
    words_fmt = 0
    words_multi = 0
    words_with_tempo_or_dyn = 0
    words_fmt_attrs = collections.Counter()
    words_texts = []
    for d in root.iter("direction"):
        ws = d.findall("direction-type/words")
        if not ws:
            continue
        dirs_words += 1
        if len(ws) > 1:
            words_multi += 1
        if d.find("direction-type/metronome") is not None or d.find("sound[@tempo]") is not None or \
                d.find("sound[@dynamics]") is not None or d.find("direction-type/dynamics") is not None:
            words_with_tempo_or_dyn += 1
        fmt = False
        for w in ws:
            for a in ("xml:lang", "xml:space", "color", "halign", "font-family", "font-style", "font-weight",
                      "enclosure"):
                if w.get(a) is not None:
                    words_fmt_attrs[a] += 1
                    fmt = True
        if fmt:
            words_fmt += 1
        if len(words_texts) < 12:
            words_texts.append([(w.text or "").strip() for w in ws])

    keys = []
    for k in root.iter("key"):
        keys.append({"mode": (k.findtext("mode") or None), "traditional": k.find("fifths") is not None})
    key_modes = collections.Counter(k["mode"] for k in keys)
    endings = [(e.get("number"), (e.text or "").strip()) for e in (first.iter("ending") if first is not None else [])
               if e.get("type") == "start"]
    repeats = collections.Counter()
    for b in root.iter("barline"):
        rep = b.find("repeat")
        if rep is not None:
            repeats["repeat-" + rep.get("direction", "?")] += 1
        elif b.findtext("bar-style") in ("light-heavy", "light-light", "heavy-light"):
            repeats["bar-" + b.findtext("bar-style")] += 1
    return {
        "parts": parts, "measures": len(measures), "measure_numbers_nonint": nonint[:5],
        "implicit_measures": implicit, "voices": sorted(voices), "note_counts": counts,
        "harmonies": len(harmonies), "kinds": kinds, "kind_lost": kind_lost,
        "dirs_words": dirs_words, "words_multi": words_multi, "words_fmt": words_fmt,
        "words_fmt_attrs": dict(words_fmt_attrs), "words_with_tempo_or_dyn": words_with_tempo_or_dyn,
        "words_samples": words_texts, "keys": len(keys), "key_modes": dict(key_modes),
        "endings": endings, "repeats": dict(repeats),
    }


# ---------------------------------------------------------------- MEI (Verovio)

def mei_facts(mei_path):
    root = ET.parse(mei_path).getroot()
    f = {"measures": [], "ids": {}, "harm": [], "dir": [], "keysig": [], "meter": [], "endings": 0,
         "layer_counts": collections.Counter(), "mode_attr": 0}
    stack = []

    def walk(el, ending_n):
        nonlocal f
        name = local(el.tag)
        if name == "ending":
            ending_n = el.get("n")
            f["endings"] += 1
        if name in ("staffGrp", "staffDef") and el.get(XML_ID):
            f["ids"].setdefault(name, []).append((el.get(XML_ID), el.findtext("{*}label") or ""))
        if name == "measure":
            f["measures"].append({"id": el.get(XML_ID), "n": el.get("n"), "left": el.get("left"),
                                  "right": el.get("right"), "metcon": el.get("metcon"),
                                  "ending": ending_n})
            mi = len(f["measures"]) - 1
            for st in el.iter():
                if local(st.tag) == "staff":
                    sn = int(st.get("n") or 1)
                    for ly in st.iter():
                        if local(ly.tag) == "layer":
                            ln = int(ly.get("n") or 1)
                            c = sum(1 for x in ly.iter() if local(x.tag) in ("note", "rest", "mRest"))
                            f["layer_counts"][(mi, sn, ln)] += c
        if name == "harm":
            f["harm"].append("".join(el.itertext()).strip())
        if name == "dir":
            f["dir"].append("".join(el.itertext()).strip())
        if name == "keySig":
            f["keysig"].append({"sig": el.get("sig"), "mode": el.get("mode"), "id": el.get(XML_ID)})
            if el.get("mode"):
                f["mode_attr"] += 1
        if name == "meterSig":
            f["meter"].append({"count": el.get("count"), "unit": el.get("unit"), "sym": el.get("sym")})
        for ch in el:
            walk(ch, ending_n)

    walk(root, None)
    return f


def mei_text(mei_path):
    root = ET.parse(mei_path).getroot()
    return re.sub(r"\s+", " ", " ".join(t for t in root.itertext() if t)).strip()


def words_perdidas(root, texto_mei):
    """<words> (texto não vazio) cujo texto não aparece em nenhum lugar do MEI notado."""
    total = perdidas = 0
    exemplos = []
    for w in root.iter("words"):
        t = re.sub(r"\s+", " ", "".join(w.itertext())).strip()
        if not t:
            continue
        total += 1
        if t not in texto_mei:
            perdidas += 1
            if len(exemplos) < 8:
                exemplos.append(t)
    return total, perdidas, exemplos


def timemap_base_ids(vsb):
    base = set()
    for e in vsb.get("timemap", []):
        mo = e.get("measureOn")
        if mo:
            base.add(re.sub(r"-rend\d+$", "", mo))
    return base


# ---------------------------------------------------------------- casos sintéticos

def make_sintetico(out_dir):
    """Twinkle (lead sheet) com <mode> minor na 1ª armadura, e uma troca de armadura no compasso 5
    (com <mode> major); e a mesma troca sem <mode>."""
    src = os.path.join(APREND, "test/fixtures/cursos/lead-sheet/media/twinkle.musicxml")
    res = {}
    d = os.path.join(out_dir, "sint")
    os.makedirs(d, exist_ok=True)
    for nome, com_modo in (("modo", True), ("sem-modo", False)):
        root = ET.parse(src).getroot()
        m1 = root.find("part").find("measure")
        key = m1.find("attributes").find("key")
        if com_modo:
            ET.SubElement(key, "mode").text = "minor"
        m5 = root.find("part").findall("measure")[4]
        attrs = m5.find("attributes")
        if attrs is None:
            attrs = ET.Element("attributes")
            m5.insert(0, attrs)
        for old in attrs.findall("key"):
            attrs.remove(old)
        newkey = ET.Element("key")
        ET.SubElement(newkey, "fifths").text = "2"
        if com_modo:
            ET.SubElement(newkey, "mode").text = "major"
        attrs.insert(0, newkey)
        path = os.path.join(d, f"twinkle-{nome}.musicxml")
        ET.ElementTree(root).write(path, xml_declaration=True, encoding="UTF-8")
        res[nome] = path
    return res


# ---------------------------------------------------------------- lista de arquivos

def arquivos(all_hymns):
    fixtures = [
        ("aprendizado", os.path.join(APREND, "test/music_reading/fixtures/src", n + ".musicxml"))
        for n in ("ode", "intro", "menor", "recusa")
    ] + [
        ("curso", os.path.join(APREND, "test/fixtures/cursos/lead-sheet/media/twinkle.musicxml")),
        ("curso", os.path.join(APREND, "test/fixtures/cursos/repertorio/media/twinkle.musicxml")),
        ("curso", os.path.join(APREND, "test/fixtures/cursos/lead-sheet/media/contrafato-1.musicxml")),
        ("curso", os.path.join(APREND, "test/fixtures/cursos/harmonia/media/folclore-1.musicxml")),
        ("curso", os.path.join(APREND, "test/fixtures/cursos/harmonia/media/folclore-2.musicxml")),
        ("asset", os.path.join(APREND, "assets/cursos/iniciacao/media/vale-ate-a-barra.musicxml")),
        ("asset", os.path.join(APREND, "assets/cursos/iniciacao/media/ode-a-alegria.musicxml")),
    ] + [
        ("corpus", p) for p in sorted(glob.glob(os.path.join(ROOT, "corpus/musicxml/*.mxl")))
    ]
    hymns = sorted(glob.glob(os.path.join(HYMNS, "*.musicxml")))
    if all_hymns:
        sel = hymns
    else:
        sel = []
        def pick(n):
            p = os.path.join(HYMNS, n + ".musicxml")
            if os.path.exists(p) and p not in sel:
                sel.append(p)
        for n in ("001", "213", "248", "458"):
            pick(n)
        with_end = [p for p in hymns if b"<ending" in open(p, "rb").read()]
        implicit = [p for p in hymns if b'implicit="yes"' in open(p, "rb").read()]
        for p in with_end[:8] + implicit[:4]:
            if p not in sel:
                sel.append(p)
        i = 0
        while len(sel) < 20 and i < len(hymns):
            if hymns[i] not in sel:
                sel.append(hymns[i])
            i += 1
    return fixtures, [("hino", p) for p in sel]


def levantamento(out):
    """Só leitura do MusicXML: todos os hinos e o corpus. Kinds, campos da cifra, casas e direções."""
    known = kinds_known()
    kinds = collections.Counter()
    lost = collections.Counter()
    campos = collections.Counter()
    numerais = 0
    casas_n = collections.Counter()
    arquivos_com = collections.Counter()
    texts = collections.Counter()
    paths = sorted(glob.glob(os.path.join(HYMNS, "*.musicxml")))
    paths += sorted(glob.glob(os.path.join(ROOT, "corpus/musicxml/*.mxl")))
    paths += [os.path.join(APREND, "test/fixtures/cursos", c) for c in (
        "lead-sheet/media/twinkle.musicxml", "repertorio/media/twinkle.musicxml",
        "lead-sheet/media/contrafato-1.musicxml", "harmonia/media/folclore-1.musicxml",
        "harmonia/media/folclore-2.musicxml")]
    for path in paths:
        root = load_musicxml(path)
        for h in root.iter("harmony"):
            campos["harmony"] += 1
            kind = h.find("kind")
            if kind is not None:
                v = (kind.text or "").strip()
                kinds[v] += 1
                if kind.get("use-symbols") == "yes":
                    arquivos_com["use-symbols"] += 1
                elif kind.get("text") is not None and v != "none":
                    arquivos_com["kind@text"] += 1
                elif v not in known:
                    lost[v] += 1
            if h.find("root/root-step") is not None:
                campos["root"] += 1
            if h.find("root/root-alter") is not None:
                campos["root-alter"] += 1
            if h.find("numeral") is not None:
                numerais += 1
            if h.find("degree") is not None:
                campos["degree"] += 1
            if h.find("bass") is not None:
                campos["bass"] += 1
        first = root.find("part")
        for e in (first.iter("ending") if first is not None else []):
            if e.get("type") == "start":
                casas_n[(e.get("number"), (e.text or "").strip())] += 1
        for w in root.iter("words"):
            t = re.sub(r"\s+", " ", "".join(w.itertext())).strip()
            if t:
                texts[t] += 1
        arquivos_com["com-harmony"] += 1 if any(True for _ in root.iter("harmony")) else 0
    res = {"arquivos": len(paths), "kinds": dict(kinds), "kind_nao_conhecido_sem_texto": dict(lost),
           "campos": dict(campos), "numeral": numerais, "casas_(numero,texto)": {str(k): v for k, v in casas_n.items()},
           "usos": dict(arquivos_com), "words_top": texts.most_common(25), "words_distintos": len(texts)}
    json.dump(res, open(os.path.join(out, "levantamento.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False, indent=1)[:4000])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all-hymns", action="store_true")
    ap.add_argument("--levantamento", action="store_true", help="só lê o MusicXML de todo o corpus e dos hinos")
    ap.add_argument("--out", default=os.path.join(ROOT, "compare", "out", "m01"))
    args = ap.parse_args()
    out = args.out
    os.makedirs(out, exist_ok=True)
    if args.levantamento:
        levantamento(out)
        return
    os.makedirs(os.path.join(out, "mei"), exist_ok=True)
    os.makedirs(os.path.join(out, "vsbjson"), exist_ok=True)

    fixtures, hymns = arquivos(args.all_hymns)
    sint = make_sintetico(out)
    todos = fixtures + hymns + [("sintetico", p) for p in sint.values()]

    def proc(item):
        kind, path = item
        mei = cli_mei(path, out)
        return kind, path, mei

    with ThreadPoolExecutor(max_workers=4) as ex:
        done = list(ex.map(proc, todos))

    resumo = {"arquivos": []}
    tot = collections.Counter()
    for kind, path, mei in done:
        o = oracle(path)
        m = mei_facts(mei)
        wt, wp, wex = words_perdidas(load_musicxml(path), mei_text(mei))
        vsb = cli_vsb_json(mei, out)
        tmids = timemap_base_ids(vsb)
        mids = [x["id"] for x in m["measures"]]
        fora_tm = [i for i in mids if re.sub(r"-rend\d+$", "", i or "") not in tmids]
        right_end = [i for i, x in enumerate(m["measures"]) if x["right"] == "end"]
        after_end = len(m["measures"]) - (right_end[0] + 1) if right_end else 0
        # layers: MusicXML × MEI, mesma contagem por (compasso, pauta, voz)
        dif = 0
        keys = set(o["note_counts"]) | set(m["layer_counts"])
        for k in keys:
            if o["note_counts"].get(k, 0) != m["layer_counts"].get(k, 0):
                dif += 1
        part_ids_mei = [i for i, _ in m["ids"].get("staffGrp", [])] + [i for i, _ in m["ids"].get("staffDef", [])]
        parts_found = [p["id"] for p in o["parts"] if p["id"] in part_ids_mei]
        registro = {
            "kind": kind, "file": os.path.relpath(path, IDIOMAS) if path.startswith(IDIOMAS) else path,
            "measures_xml": o["measures"], "measures_mei": len(m["measures"]),
            "parts_xml": [p["id"] for p in o["parts"]], "parts_found_in_mei": parts_found,
            "voices_xml": o["voices"], "layer_diff_cells": dif, "cells": len(keys),
            "implicit": o["implicit_measures"], "nonint_numbers": o["measure_numbers_nonint"],
            "mei_n_samples": [x["n"] for x in m["measures"][:3]],
            "endings_xml": len(o["endings"]), "endings_mei": m["endings"], "ending_numbers_xml": o["endings"][:4],
            "repeats": dict(o["repeats"]), "right_end_mei": len(right_end), "after_right_end": after_end,
            "measures_not_in_timemap": len(fora_tm),
            "harmonies_xml": o["harmonies"], "harm_mei": len(m["harm"]),
            "kinds_xml": dict(o["kinds"]), "kind_lost": dict(o["kind_lost"]),
            "harm_samples": m["harm"][:6],
            "dirs_words_xml": o["dirs_words"], "words_multi": o["words_multi"], "words_fmt": o["words_fmt"],
            "words_fmt_attrs": o["words_fmt_attrs"], "words_tempo_or_dyn": o["words_with_tempo_or_dyn"],
            "dir_mei": len(m["dir"]), "dir_samples": m["dir"][:6], "words_samples": o["words_samples"][:6],
            "words_texto": wt, "words_perdidas": wp, "words_perdidas_exemplos": wex,
            "mei_endings_n": sorted({x["ending"] for x in m["measures"] if x["ending"]}),
            "keys_xml": o["keys"], "key_modes_xml": o["key_modes"], "mode_attr_mei": m["mode_attr"],
            "keysig_mei": m["keysig"][:4], "meter_mei": m["meter"][:2],
        }
        resumo["arquivos"].append(registro)
        tot["arquivos"] += 1
        tot["layer_diff_cells"] += dif
        tot["harm_xml"] += o["harmonies"]
        tot["harm_mei"] += len(m["harm"])
        tot["measures_not_in_timemap"] += len(fora_tm)
        tot["endings_xml"] += len(o["endings"])
        tot["endings_mei"] += m["endings"]
        tot["dirs_words_xml"] += o["dirs_words"]
        tot["dir_mei"] += len(m["dir"])
        tot["words_texto"] += wt
        tot["words_perdidas"] += wp
        for k, v in o["kinds"].items():
            tot["kind:" + k] += v
        for k, v in o["kind_lost"].items():
            tot["kind_lost:" + k] += v
        print(f"[{kind}] {registro['file']}: compassos {registro['measures_xml']}/{registro['measures_mei']}"
              f" partes {registro['parts_xml']} achadas {len(parts_found)}"
              f" celulas {registro['cells']} dif {dif}"
              f" harm {registro['harmonies_xml']}/{registro['harm_mei']}"
              f" casas {registro['endings_xml']}/{registro['endings_mei']}"
              f" dirWords {registro['dirs_words_xml']}/{registro['dir_mei']}"
              f" fora_tm {len(fora_tm)} apos_barra_final {after_end}"
              f" modeXML {registro['key_modes_xml']} modeMEI {registro['mode_attr_mei']}"
              f" words {wt} perdidas {wp}")

    resumo["total"] = dict(tot)
    with open(os.path.join(out, "resumo.json"), "w", encoding="utf-8") as fh:
        json.dump(resumo, fh, ensure_ascii=False, indent=1, default=str)
    print("TOTAL", dict(tot))


if __name__ == "__main__":
    main()
