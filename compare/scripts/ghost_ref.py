#!/usr/bin/env python3
"""Implementação de referência da nota fantasma (docs/formato/especificacao-v1.md §10, G04d).

Lê um `.vsb` (cena + glyphs + pitchpos) e, para os ids esperados de um instante e uma lista
de teclas MIDI erradas, devolve as fantasmas: pauta, `loc`, cabeça, acidente, linhas
suplementares e marcador de oitava. É a régua contra a qual o `zywny` valida a porta Dart
(vetores em docs/formato/fantasma/vetores.json).

Uso:
  ghost_ref.py --self-test                  confere todos os vetores
  ghost_ref.py <arquivo.vsb> <id[,id...]> <tecla[,tecla...]>   imprime as fantasmas (JSON)
"""
import json, os, sys, zipfile

SEM = [0, 2, 4, 5, 7, 9, 11]          # semitons da letra natural, pname 1..7
LETTERS = "cdefgab"
ACCID_GLYPH = {1: "E262", -1: "E260", 0: "E261", 2: "E263", -2: "E264"}  # ±2 só com a tecla certa (w == wE)
OCTAVE_GLYPH = {("up", 1): "E511", ("down", 1): "E512", ("up", 2): "E515", ("down", 2): "E516"}
MAX_LEDGERS = 4

# §10 passo 8, valores VISUAIS (o Verovio não desenha isto; fechados em G04d, ver §10):
ACC_GAP_PER_UNIT = None  # preenchido abaixo (folga do acidente, em `unit`); medido pelo oráculo
OCT_ABOVE_UNITS = 3
OCT_BELOW_UNITS = 5


def midi_natural(pname, octave):
    return 12 * (octave + 1) + SEM[pname - 1]


def natural_of(midi):
    """(pname 1..7, oct) da letra natural de uma tecla branca."""
    pc = midi % 12
    return SEM.index(pc) + 1, midi // 12 - 1


class Vsb:
    def __init__(self, path):
        z = zipfile.ZipFile(path)
        self.glyphs = json.loads(z.read("glyphs.json"))
        self.pages = json.loads(z.read("scene.json"))["pages"]
        self.pitchpos = json.loads(z.read("pitchpos.json"))["events"] if "pitchpos.json" in z.namelist() else {}
        self.font = next(iter(self.glyphs)).split(":")[0]
        self.nodes = {}     # id -> (node, staffnode)
        self.staffs = {}    # id -> staff node
        for page in self.pages:
            self._walk(page["root"], None)

    def _walk(self, node, staff):
        cls = node.get("class", "").split()
        if cls[:1] == ["staff"]:
            staff = node
            if "id" in node:
                self.staffs[node["id"]] = node
        if "id" in node:
            self.nodes[node["id"]] = (node, staff)
        for c in node.get("children", []):
            if c.get("t") == "g":
                self._walk(c, staff)

    def glyph_width(self, gid, sx):
        return self.glyphs[gid]["bbox"][2] / 10.0 * sx


def first_u(node, want_notehead):
    """Primeiro `u`: dentro de um nó `notehead` (notas) ou o primeiro em geral (pausas)."""
    def rec(n, in_head):
        cls = n.get("class", "").split()
        in_head = in_head or "notehead" in cls
        for c in n.get("children", []):
            if c.get("t") == "u" and (in_head or not want_notehead):
                return c
            if c.get("t") == "g":
                r = rec(c, in_head)
                if r:
                    return r
        return None
    return rec(node, False)


def candidates(doc, ids):
    out = []
    for i in ids:
        ev = doc.pitchpos[i]
        node, staff = doc.nodes[i]
        if "staff" in node:
            staff = doc.staffs[node["staff"]]
        top, unit, n = staff["lines"]
        u = first_u(node, ev["t"] == "n")
        c = dict(id=i, ev=ev, staff=staff, top=top, unit=unit, n=n, u=u, node=node)
        if ev["t"] == "n":
            c["written"] = midi_natural(LETTERS.index(ev["pn"]) + 1, ev["o"]) + ev["alt"]
            c["ref"] = c["written"] + ev.get("sh", 0)
        else:
            loc = n - 1                       # linha do meio
            pos = loc - ev["co"] + 28
            c["written"] = midi_natural(pos % 7 + 1, pos // 7)
            c["ref"] = c["written"] + ev.get("sh", 0)
        out.append(c)
    return out


def spell(w, wE, key, target_note):
    """§10 passo 3: (pname, oct, alt) da tecla escrita `w`."""
    if w == wE and target_note is not None:
        return target_note
    if w % 12 in SEM:
        p, o = natural_of(w)
        return p, o, 0
    pos = any(v > 0 for v in key.values())
    neg = any(v < 0 for v in key.values())
    if pos and not neg:
        sharp = True
    elif neg and not pos:
        sharp = False
    else:
        sharp = w > wE
    if sharp:
        p, o = natural_of(w - 1)
        return p, o, 1
    p, o = natural_of(w + 1)
    return p, o, -1


def ledger_count(loc, n):
    top = 2 * (n - 1)
    if loc > top:
        return (loc - top) // 2
    if loc < 0:
        return (-loc) // 2
    return 0


def ghosts(doc, ids, keys, acc_gap=None):
    """§10: uma fantasma por tecla de `keys` para os eventos esperados `ids`."""
    gap_units = ACC_GAP_PER_UNIT if acc_gap is None else acc_gap
    cands = candidates(doc, ids)
    placed = []       # fantasmas já postas (colisão), por pauta
    out = []
    for k in sorted(keys):
        # 1. alvo: menor |k - ref|; empate -> o de cima (maior ref)
        t = min(cands, key=lambda c: (abs(k - c["ref"]), -c["ref"]))
        ev = t["ev"]
        sh = ev.get("sh", 0)
        w = k - sh
        target_note = None
        if ev["t"] == "n":
            target_note = (LETTERS.index(ev["pn"]) + 1, ev["o"], ev["alt"])
        pname, octv, alt = spell(w, t["written"], ev.get("key", {}), target_note)
        co, n, top, unit = ev["co"], t["n"], t["top"], t["unit"]
        loc = (octv - 4) * 7 + (pname - 1) + co
        loc_raw = loc
        ledgers_raw = ledger_count(loc, n)
        m = 0
        led = ledgers_raw
        while led > MAX_LEDGERS and m < 2:
            loc = loc - 7 if loc_raw > 2 * (n - 1) else loc + 7
            m += 1
            led = ledger_count(loc, n)
        direction = "up" if loc_raw > 2 * (n - 1) else "down"
        if led > MAX_LEDGERS:   # além de duas oitavas: presa em 4 linhas (limitação aceita, §10 passo 5)
            loc = 2 * (n - 1) + 2 * MAX_LEDGERS if direction == "up" else -2 * MAX_LEDGERS
            led = MAX_LEDGERS
        # 6. acidente
        key_alt = ev.get("key", {}).get(LETTERS[pname - 1], 0)
        in_force = ev.get("acc", {}).get("%s%d" % (LETTERS[pname - 1], octv), key_alt)
        accid = ACCID_GLYPH[alt] if alt != in_force else None
        # 7. cabeça e x
        u = t["u"]
        head_g = "%s:E0A4" % doc.font
        sx, sy = (u["sx"], u["sy"]) if u else tuple(t["staff"]["gs"])
        if ev["t"] == "r":
            sx, sy = t["staff"]["gs"]
        x = u["x"] if u else t["node"].get("bbox", [0])[0]   # nó sem cabeça (ex. nota oculta): borda esquerda
        width = doc.glyph_width(head_g, sx)
        staff_id = t["staff"].get("id")
        if ev["t"] == "n":
            reals = []
            for c in cands:
                if c["ev"]["t"] == "n" and c["staff"] is t["staff"]:
                    cu = c["u"]
                    if cu is None:
                        continue
                    reals.append((c["ev"]["loc"], cu["x"], doc.glyph_width(cu["g"], cu["sx"])))
            moved = True
            while moved:
                moved = False
                for (rloc, rx, rw) in reals + [(p["loc"], p["x"], p["width"]) for p in placed if p["staff"] == staff_id]:
                    if abs(loc - rloc) <= 1 and rx < x + width and x < rx + rw:
                        x += width
                        moved = True
                        break
        y = top + (2 * (n - 1) - loc) * unit
        g = dict(key=k, staff=staff_id, loc=loc, locRaw=loc_raw, m=m, ledgersRaw=ledgers_raw,
                 pname=LETTERS[pname - 1], oct=octv, alt=alt, target=t["id"],
                 head=dict(g=head_g, x=x, y=y, sx=sx, sy=sy), accid=None, ledgers=[], octave=None,
                 width=width)
        if accid:
            aid = "%s:%s" % (doc.font, accid)
            aw = doc.glyph_width(aid, sx)
            g["accid"] = dict(g=aid, x=x - (gap_units or 0) * unit - aw, y=y, sx=sx, sy=sy)
        # 8. linhas suplementares
        if led > 0:
            cue = u is not None and sx < t["staff"]["gs"][0] * 0.999 and "ledgerCue" in t["staff"]
            thick, ext = t["staff"]["ledgerCue" if cue else "ledger"]
            for j in range(1, led + 1):
                lloc = 2 * (n - 1) + 2 * j if loc > 2 * (n - 1) else -2 * j
                ly = top + (2 * (n - 1) - lloc) * unit
                g["ledgers"].append(dict(y=ly, x1=x - ext, x2=x + width + ext, w=thick))
        if m > 0:
            oid = "%s:%s" % (doc.font, OCTAVE_GLYPH[(direction, m)])
            ow = doc.glyph_width(oid, sx)
            ext_y = g["ledgers"][-1]["y"] if g["ledgers"] else y
            by = ext_y - OCT_ABOVE_UNITS * unit if direction == "up" else ext_y + OCT_BELOW_UNITS * unit
            g["octave"] = dict(g=oid, x=x + width / 2 - ow / 2, y=by, sx=sx, sy=sy)
        placed.append(dict(staff=staff_id, loc=loc, x=x, width=width))
        out.append(g)
    return out


ACC_GAP_PER_UNIT = 0.0  # substituído pelo valor fechado em G04d


def _close(a, b, tol=0.5):
    if isinstance(a, dict):
        return set(a) == set(b) and all(_close(a[k], b[k], tol) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(_close(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return abs(a - b) <= tol
    return a == b


def self_test():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(here, "..", ".."))
    base = os.path.join(root, "docs", "formato", "fantasma")
    vec = json.load(open(os.path.join(base, "vetores.json")))
    global ACC_GAP_PER_UNIT
    ACC_GAP_PER_UNIT = vec["accGapPerUnit"]
    bad = 0
    docs = {}
    for case in vec["casos"]:
        doc = docs.setdefault(case["vsb"], Vsb(os.path.join(base, case["vsb"])))
        got = ghosts(doc, case["esperados"], case["teclas"])
        for i, (g, want) in enumerate(zip(got, case["resumo"])):
            mine = dict(loc=g["loc"], m=g["m"], accid=(g["accid"]["g"].split(":")[1] if g["accid"] else None),
                        ledgers=len(g["ledgers"]), pname=g["pname"], oct=g["oct"], alt=g["alt"], staff=g["staff"],
                        target=g["target"])
            if mine != want:
                print("RESUMO diverge:", case["nome"], "tecla", g["key"], "esperado", want, "obtido", mine); bad += 1
        if len(got) != len(case["resumo"]):
            print("nº de fantasmas:", case["nome"]); bad += 1
        if "fantasmas" in case and not _close(json.loads(json.dumps(got)), case["fantasmas"]):
            print("NÚMEROS divergem:", case["nome"]); bad += 1
    print("%d casos, %d divergências" % (len(vec["casos"]), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
        sys.exit(self_test())
    if len(sys.argv) == 4:
        d = Vsb(sys.argv[1])
        print(json.dumps(ghosts(d, sys.argv[2].split(","), [int(x) for x in sys.argv[3].split(",")]), indent=1))
        sys.exit(0)
    print(__doc__)
    sys.exit(2)
