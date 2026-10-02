#!/usr/bin/env python3
"""Verifica as cadeias de ligadura (`tied`) de midi.json
(docs/nota-do-zywny-ligadura-entre-camadas.md, especificacao-v1.md §2.7).

Uso: verify-tied-chains.py <peça.vsb> [<esperado.json>]

Sempre confere, sem depender da peça:

  1. nenhum id aparece em duas cadeias, nem duas vezes na mesma;
  2. nenhum id de continuação tem evento próprio em `notes`;
  3. nenhuma entrada `orn` carrega `tied`.

Com <esperado.json> (`{"id da cabeça": ["id da continuação", ...]}`), confere também que as
cabeças com `tied` e suas cadeias são exatamente as esperadas - nem a mais, nem a menos.
"""
import json
import sys
import zipfile


def main():
    if len(sys.argv) not in (2, 3):
        print(__doc__)
        return 2

    with zipfile.ZipFile(sys.argv[1]) as vsb:
        notes = json.loads(vsb.read("midi.json"))["notes"]

    errors = []
    event_ids = {note["id"] for note in notes}
    owner = {}
    chains = {}
    for note in notes:
        tied = note.get("tied")
        if not tied:
            continue
        if note.get("orn"):
            errors.append(f"entrada orn com tied: {note['id']}")
        chains[note["id"]] = tied
        for continuation in tied:
            if continuation in owner:
                errors.append(f"{continuation} em duas cadeias: {owner[continuation]} e {note['id']}")
            owner[continuation] = note["id"]
            if continuation in event_ids:
                errors.append(f"continuação {continuation} (de {note['id']}) tem evento próprio")

    print(f"{len(notes)} notas, {len(chains)} cabeças com tied, {len(owner)} continuações")

    if len(sys.argv) == 3:
        with open(sys.argv[2], encoding="utf-8") as expected_file:
            expected = json.load(expected_file)
        for head in sorted(set(expected) | set(chains)):
            if expected.get(head) != chains.get(head):
                errors.append(f"{head}: esperado {expected.get(head)}, obtido {chains.get(head)}")

    for error in errors:
        print("  " + error)
    print("RESULTADO: " + ("DIVERGÊNCIAS ENCONTRADAS" if errors else "OK"))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
