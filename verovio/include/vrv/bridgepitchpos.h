/////////////////////////////////////////////////////////////////////////////
// Name:        bridgepitchpos.h
// Author:      Verovio Team
// Created:     2026
// Copyright (c) Authors and others. All rights reserved.
/////////////////////////////////////////////////////////////////////////////

#ifndef __VRV_BRIDGE_PITCHPOS_H__
#define __VRV_BRIDGE_PITCHPOS_H__

#include <map>
#include <string>
#include <utility>
#include <vector>

namespace vrv {

class Doc;
struct MIDIEventLog;

//----------------------------------------------------------------------------
// BridgePitchPosEvent, BridgePitchPos
//----------------------------------------------------------------------------

/**
 * Notation context of one note or rest (docs/formato/especificacao-v1.md §2.8, G04c): what the host
 * needs to compute where any MIDI key would be written at that point (the ghost note, §10).
 */
struct BridgePitchPosEvent {
    bool isNote = false;
    int clefLocOffset = 0; // `co`
    int shift = 0; // `sh`: sound - written, in semitones
    std::map<int, int> key; // `key`: pname (1 = c ... 7 = b) -> alteration of the key signature in force
    std::map<std::string, int> acc; // `acc`: "g4" -> alteration in force, when different from `key`
    // Written figure (§2.8, G08b): the denominator (1 = whole ... 1024), 0 when unknown (breve, long,
    // maxima, no @dur, mRest); `dots` only means something with `dur`.
    int dur = 0;
    int dots = 0;
    // Notes only
    int pname = 0; // 1 = c ... 7 = b
    int oct = 0;
    int alt = 0; // effective alteration
    int loc = 0; // the loc the Verovio drew the head with
};

struct BridgePitchPos {
    // Document order; the key is the notated xml:id
    std::vector<std::pair<std::string, BridgePitchPosEvent>> events;
    // false when the drawing positions were not computed (M05, RenderToMusicJson of a document without
    // layout at load): `loc` and `acc` of every event are then written as null (§2.8).
    bool layout = true;
    // Diagnostics (LogWarning-ed by the caller when non-zero): elements the MIDI functor never
    // visited (no shift), and ids visited more than once with different shifts.
    int missingShift = 0;
    int conflictingShift = 0;

    bool IsEmpty() const { return events.empty(); }
};

//----------------------------------------------------------------------------
// BridgePitchPosBuilder
//----------------------------------------------------------------------------

class BridgePitchPosBuilder {
public:
    /**
     * Collect the context of every pitched note and every rest of the pages [firstPage, lastPage]
     * (0-based, inclusive) of the notated `doc`, which must already be laid out for those pages
     * (the drawing loc and the cross-staff pointers are layout products). `midiLog->shifts` comes
     * from the expanded document; ids are matched by the §2.4 suffix rule.
     *
     * `withLayout` false (M05, RenderToMusicJson of a document whose layout was not computed at
     * load: `--breaks none`, or a page-based MEI) skips what only the layout provides - `loc` and
     * `acc` - and sets BridgePitchPos::layout to false. Every other field is read from the notated
     * data and is the same with or without layout (measured on the corpus, M05).
     */
    static BridgePitchPos Build(
        Doc *doc, int firstPage, int lastPage, const MIDIEventLog &midiLog, bool withLayout = true);
};

} // namespace vrv

#endif // __VRV_BRIDGE_PITCHPOS_H__
