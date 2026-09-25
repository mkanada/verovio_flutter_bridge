#!/usr/bin/env python3
"""Verifica midi.json contra o .mid da mesma peça (docs/plano/G01-gravador-de-notas-midi.md,
critérios 2 e 4).

Uso: verify-midi-json.py <peça.vsb> <peça.mid>

Sem dependências externas: lê o SMF (Standard MIDI File) e o midi.json de dentro do .vsb com um
parser mínimo. Compara:

  1. o multiconjunto (canal, pitch, on_ms) das notas de midi.json contra os note-on do .mid
     (critério 2 - "midi.json = .mid"), convertendo os ticks do .mid para ms pelo próprio mapa de
     andamento do arquivo (tolerância: round() em ambos os lados, ou seja, 1 ms).
  2. o mesmo para os eventos de pedal (CC 64: value>=64 é "down", value<64 é "up").
  3. quando midi.json também vem com timemap.json no mesmo .vsb, o "on"/"off" de cada nota (sem
     "tied"/"orn") contra o timemap do mesmo id (critério 4 - "dois relógios").
"""
import json
import sys
import zipfile
from collections import Counter


def read_varlen(data, pos):
    value = 0
    while True:
        byte = data[pos]
        pos += 1
        value = (value << 7) | (byte & 0x7F)
        if not (byte & 0x80):
            break
    return value, pos


def parse_smf(data):
    assert data[0:4] == b"MThd"
    header_len = int.from_bytes(data[4:8], "big")
    division = int.from_bytes(data[8 + 4:8 + 6], "big")
    pos = 8 + header_len

    tracks = []
    while pos < len(data):
        chunk_type = data[pos:pos + 4]
        chunk_len = int.from_bytes(data[pos + 4:pos + 8], "big")
        pos += 8
        if chunk_type != b"MTrk":
            pos += chunk_len
            continue
        end = pos + chunk_len
        events = []
        tick = 0
        running_status = None
        while pos < end:
            delta, pos = read_varlen(data, pos)
            tick += delta
            status = data[pos]
            if status < 0x80:
                # running status: reuse previous status byte, don't consume this one
                status = running_status
            else:
                pos += 1
                if status < 0xF0:
                    running_status = status
            if status == 0xFF:
                meta_type = data[pos]
                pos += 1
                length, pos = read_varlen(data, pos)
                payload = data[pos:pos + length]
                pos += length
                events.append((tick, "meta", meta_type, payload))
            elif status in (0xF0, 0xF7):
                length, pos = read_varlen(data, pos)
                pos += length
            elif 0x80 <= status < 0xF0:
                kind = status & 0xF0
                channel = status & 0x0F
                if kind in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                    d1, d2 = data[pos], data[pos + 1]
                    pos += 2
                    events.append((tick, "chan", kind, channel, d1, d2))
                else:  # 0xC0 program change, 0xD0 channel pressure: 1 data byte
                    pos += 1
            else:
                raise ValueError(f"unexpected status byte {status:#x} at {pos}")
        tracks.append(events)
        pos = end
    return division, tracks


def build_tempo_ms(division, tracks):
    """(tick, bpm) breakpoints from every track's tempo meta events, then a tick->ms function."""
    tempos = []
    for events in tracks:
        for event in events:
            if event[1] == "meta" and event[2] == 0x51:
                tick, payload = event[0], event[3]
                micros_per_quarter = int.from_bytes(payload, "big")
                bpm = 60000000.0 / micros_per_quarter
                tempos.append((tick, bpm))
    if not tempos or tempos[0][0] != 0:
        tempos.insert(0, (0, 120.0))
    tempos.sort(key=lambda t: t[0])

    breakpoints = []
    ms = 0.0
    for i, (tick, bpm) in enumerate(tempos):
        if i > 0:
            prev_tick, prev_bpm = tempos[i - 1]
            ms += (tick - prev_tick) * 60000.0 / prev_bpm / division
        breakpoints.append((tick, ms, bpm))

    def tick_to_ms(tick):
        index = 0
        for i, bp in enumerate(breakpoints):
            if bp[0] > tick:
                break
            index = i
        bp_tick, bp_ms, bp_bpm = breakpoints[index]
        return bp_ms + (tick - bp_tick) * 60000.0 / bp_bpm / division

    return tick_to_ms


def collect_midi_events(division, tracks):
    tick_to_ms = build_tempo_ms(division, tracks)
    note_ons = Counter()
    pedal_events = Counter()
    for events in tracks:
        for event in events:
            if event[1] != "chan":
                continue
            _, _, kind, channel, d1, d2 = event
            tick = event[0]
            ms = round(tick_to_ms(tick), 3)
            if kind == 0x90 and d2 > 0:
                note_ons[(channel, d1, round(ms))] += 1
            elif kind == 0xB0 and d1 == 64:
                direction = "down" if d2 >= 64 else "up"
                pedal_events[(channel, direction, round(ms))] += 1
    return note_ons, pedal_events


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    vsb_path, mid_path = sys.argv[1], sys.argv[2]

    with zipfile.ZipFile(vsb_path) as z:
        midi_doc = json.loads(z.read("midi.json"))
        timemap = None
        if "timemap.json" in z.namelist():
            timemap = json.loads(z.read("timemap.json"))

    with open(mid_path, "rb") as f:
        division, tracks = parse_smf(f.read())
    midi_note_ons, midi_pedal_events = collect_midi_events(division, tracks)

    json_note_ons = Counter()
    for note in midi_doc["notes"]:
        json_note_ons[(note.get("c", 0), note["p"], round(note["on"]))] += 1
    json_pedal_events = Counter()
    for event in midi_doc["pedal"]:
        json_pedal_events[(event.get("c", 0), event["dir"], round(event["t"]))] += 1

    note_diff = midi_note_ons - json_note_ons
    note_diff_rev = json_note_ons - midi_note_ons
    pedal_diff = midi_pedal_events - json_pedal_events
    pedal_diff_rev = json_pedal_events - midi_pedal_events

    print(f"notas: midi.json={sum(json_note_ons.values())} .mid={sum(midi_note_ons.values())}")
    print(f"  só no .mid: {sum(note_diff.values())}, só no midi.json: {sum(note_diff_rev.values())}")
    if note_diff:
        print("  exemplos só no .mid:", list(note_diff.items())[:5])
    if note_diff_rev:
        print("  exemplos só no midi.json:", list(note_diff_rev.items())[:5])

    print(f"pedal: midi.json={sum(json_pedal_events.values())} .mid={sum(midi_pedal_events.values())}")
    print(f"  só no .mid: {sum(pedal_diff.values())}, só no midi.json: {sum(pedal_diff_rev.values())}")
    if pedal_diff:
        print("  exemplos só no .mid:", list(pedal_diff.items())[:5])
    if pedal_diff_rev:
        print("  exemplos só no midi.json:", list(pedal_diff_rev.items())[:5])

    if timemap is not None:
        tstamp_by_id = {}
        for entry in timemap:
            for note_id in entry.get("on", []):
                tstamp_by_id.setdefault(note_id, {})["on"] = entry["tstamp"]
            for note_id in entry.get("off", []):
                tstamp_by_id.setdefault(note_id, {})["off"] = entry["tstamp"]

        checked = 0
        mismatches = []
        for note in midi_doc["notes"]:
            if note.get("orn") or note.get("tied"):
                continue
            times = tstamp_by_id.get(note["id"])
            if not times:
                continue
            checked += 1
            if abs(times.get("on", -1e9) - note["on"]) > 1.0:
                mismatches.append((note["id"], "on", times.get("on"), note["on"]))
            if abs(times.get("off", -1e9) - note["off"]) > 1.0:
                mismatches.append((note["id"], "off", times.get("off"), note["off"]))
        print(f"dois relógios: {checked} ids comparados contra o timemap, {len(mismatches)} divergências (>1ms)")
        for m in mismatches[:10]:
            print("  ", m)

    ok = not note_diff and not note_diff_rev and not pedal_diff and not pedal_diff_rev
    ok = ok and (timemap is None or not mismatches)
    print("RESULTADO:", "OK" if ok else "DIVERGÊNCIAS ENCONTRADAS")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
