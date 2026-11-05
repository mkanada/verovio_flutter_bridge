#!/usr/bin/env python3
"""G11: copia MEI com o conteúdo de compassos trocado por `<mRest/>` (uma camada por pauta).

Usado pela varredura (`g11-sweep.py`) e pelo oráculo (`hide_oracle.py --measures`). O `<staff>` do
compasso mantém `n`, perde todas as camadas e ganha `<layer n="1"><mRest xml:id=…/></layer>`; os
controles do compasso (ligaduras, dinâmicas, andamento, harmonia, pedais…) saem, porque apontam para
ids que deixam de existir (o Verovio dá SIGSEGV num `endid` solto).
"""
import xml.etree.ElementTree as ET

MEI_NS = "http://www.music-encoding.org/ns/mei"
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"
ET.register_namespace("", MEI_NS)
ET.register_namespace("xml", "http://www.w3.org/XML/1998/namespace")


def q(tag):
    return "{%s}%s" % (MEI_NS, tag)


def measures(root):
    return [m for m in root.iter(q("measure"))]


def swap_measure(meas, mid, removed):
    """Troca o conteúdo da pauta de cada <staff> de `meas` por uma mRest. Devolve {pauta n: id da mRest};
    `removed` (conjunto) recebe os ids que deixaram de existir."""
    out = {}
    for ch in list(meas):
        if ch.tag != q("staff"):
            removed |= {e.get(XML_ID) for e in ch.iter() if e.get(XML_ID)}
            meas.remove(ch)
    for st in meas.findall(q("staff")):
        for ch in list(st):
            removed |= {e.get(XML_ID) for e in ch.iter() if e.get(XML_ID)}
            st.remove(ch)
        layer = ET.SubElement(st, q("layer"))
        layer.set("n", "1")
        mr = ET.SubElement(layer, q("mRest"))
        n = st.get("n", "1")
        rid = "mr-%s-s%s" % (mid, n)
        mr.set(XML_ID, rid)
        out[n] = rid
    return out


def swap_file(src, dst, pick=lambda i, m: True):
    """Grava em `dst` a cópia de `src` com os compassos para os quais `pick(i, compasso)` é verdadeiro
    trocados por mRest. Devolve {id do compasso: {pauta: id da mRest}}."""
    tree = ET.parse(src)
    root = tree.getroot()
    done = {}
    removed = set()
    for i, m in enumerate(measures(root)):
        if pick(i, m):
            mid = m.get(XML_ID) or "m%d" % i
            done[mid] = swap_measure(m, mid, removed)
    # controles (ligaduras, dinâmicas, pedais, barras entre compassos…) de OUTROS compassos que apontam
    # para ids removidos: o Verovio dá SIGSEGV num `endid` solto
    parent = {c: p for p in root.iter() for c in p}
    for el in list(root.iter()):
        if el.tag in (q("note"), q("rest"), q("chord"), q("layer"), q("staff"), q("measure"), q("mRest")):
            continue
        refs = [t.lstrip("#") for a in ("startid", "endid", "plist", "copyof", "sameas") for t in el.get(a, "").split()]
        if any(r in removed for r in refs):
            pr = parent.get(el)
            if pr is not None and el in list(pr):
                pr.remove(el)
    tree.write(dst, encoding="utf-8", xml_declaration=True)
    return done
