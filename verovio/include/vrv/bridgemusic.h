/////////////////////////////////////////////////////////////////////////////
// Name:        bridgemusic.h
// Author:      Verovio Team
// Created:     2026
// Copyright (c) Authors and others. All rights reserved.
/////////////////////////////////////////////////////////////////////////////

#ifndef __VRV_BRIDGE_MUSIC_H__
#define __VRV_BRIDGE_MUSIC_H__

#include <string>
#include <vector>

namespace vrv {

class Doc;

//----------------------------------------------------------------------------
// BridgeMusic
//----------------------------------------------------------------------------

// Null convention: an empty string means null for the nullable text fields (left, right, ending,
// chord, grace = "" is false, sym, mode, name, text, sig), and a zero count or zero bpm means null.

struct BridgeMusicPart {
    std::string id;
    std::string name; // "" = null
    std::vector<int> staves;
};

struct BridgeMusicTuplet {
    int num = 0; // 0 = no tuplet
    int numbase = 0;
};

// One note, rest, multi-measure rest or space of a layer (docs/formato/especificacao-v1.md §2.9, rule 4).
struct BridgeMusicEvent {
    std::string id;
    std::string t; // "n", "r", "mr" or "s"
    std::string chord; // "" = null
    std::string grace; // "" = false, "acc" or "unacc"
    BridgeMusicTuplet tuplet;
};

struct BridgeMusicLayer {
    int n = 0;
    std::vector<BridgeMusicEvent> events;
};

struct BridgeMusicStaff {
    int n = 0;
    std::vector<BridgeMusicLayer> layers;
};

struct BridgeMusicMeter {
    int count = 0;
    int unit = 0;
    std::string sym; // "" = null, "common" or "cut"
};

struct BridgeMusicKey {
    std::string sig; // "" = null (no standard name)
    int fifths = 0;
    std::string mode; // "" = null
};

struct BridgeMusicMeasure {
    std::string id;
    int index = 0;
    std::string n;
    std::string left; // "" = null
    std::string right; // "" = null
    std::string ending; // "" = null, else the @n of the enclosing <ending>
    BridgeMusicMeter meter;
    BridgeMusicKey key;
    std::vector<BridgeMusicStaff> staves;
};

struct BridgeMusicOrnament {
    std::string id;
    std::string kind; // "trill", "mordent" or "turn"
    std::string startid; // without the '#'
};

struct BridgeMusicTempo {
    std::string id;
    int measure = 0; // index of the measure that holds the tempo
    double bpm = 0.0; // 0 = null
    std::string text; // "" = null
};

// The notated musical structure of a document (docs/formato/especificacao-v1.md §2.9, music.json).
// harmonies and directions are filled by M04; until then the writer emits them empty.
struct BridgeMusic {
    std::vector<BridgeMusicPart> parts;
    std::vector<BridgeMusicMeasure> measures;
    std::vector<BridgeMusicOrnament> ornaments;
    std::vector<BridgeMusicTempo> tempi;

    // The caller omits music.json when there is no measure (same rule as the other documents).
    bool IsEmpty() const { return measures.empty(); }
};

/**
 * Reads the notated structure of `doc` (M03). Reads only; it never changes the Doc. It works on the
 * Doc as the render left it (cast-off pages included), so it must run before anything that Select()s
 * or re-lays-out the Doc (the alternates). Ids are the notated xml:ids; no "-rend<N>" suffix appears
 * because the notated Doc is never expanded here.
 */
BridgeMusic ReadBridgeMusic(Doc &doc);

} // namespace vrv

#endif // __VRV_BRIDGE_MUSIC_H__
