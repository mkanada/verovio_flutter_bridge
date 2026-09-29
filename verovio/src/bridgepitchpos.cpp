/////////////////////////////////////////////////////////////////////////////
// Name:        bridgepitchpos.cpp
// Author:      Verovio Team
// Created:     2026
// Copyright (c) Authors and others. All rights reserved.
/////////////////////////////////////////////////////////////////////////////

#include "bridgepitchpos.h"

//----------------------------------------------------------------------------

#include <algorithm>
#include <cassert>
#include <regex>
#include <set>
#include <tuple>

//----------------------------------------------------------------------------

#include "accid.h"
#include "comparison.h"
#include "doc.h"
#include "horizontalaligner.h"
#include "keysig.h"
#include "layer.h"
#include "layerelement.h"
#include "midifunctor.h"
#include "note.h"
#include "page.h"
#include "pages.h"
#include "staff.h"
#include "transposition.h"
#include "vrv.h"

namespace vrv {

namespace {

    // Alteration (-2..2) of a written accidental, as GetMIDIPitch would apply it.
    int WrittenAlteration(data_ACCIDENTAL_WRITTEN accid)
    {
        const int value = TransPitch::GetChromaticAlteration(ACCIDENTAL_GESTURAL_NONE, accid);
        return std::clamp(value, -2, 2);
    }

    // Same expressions as PitchInterface::CalcLoc, with the cross-staff resolution of
    // CalcAlignmentPitchPosFunctor::VisitLayerElement: the clefLocOffset of the clef in force in
    // the staff the element is drawn on.
    int ClefLocOffset(const LayerElement *element)
    {
        const Layer *parentLayer = vrv_cast<const Layer *>(element->GetFirstAncestor(LAYER));
        assert(parentLayer);
        const Layer *layer = parentLayer;
        const LayerElement *elementY = element;
        if (element->m_crossStaff && element->m_crossLayer) {
            elementY = element->m_crossLayer->GetAtPos(element->GetDrawingX());
            layer = element->m_crossLayer;
        }
        int offset = layer->GetClefLocOffset(elementY);
        if (parentLayer != layer) {
            offset = parentLayer->GetCrossStaffClefLocOffset(element, offset);
        }
        return offset;
    }

    // pname (1..7) -> alteration for the key signature in force at `element`: a KeySig inside the
    // layer before it wins, otherwise the one of the staff definition of its measure.
    std::map<int, int> KeyAt(const LayerElement *element)
    {
        const Layer *layer = vrv_cast<const Layer *>(element->GetFirstAncestor(LAYER));
        assert(layer);

        const KeySig *keySig = NULL;
        const Object *top = element;
        while (top->GetParent() && (top->GetParent() != layer)) top = top->GetParent();
        if (top->GetParent() == layer) {
            layer->ResetList();
            const Object *found = layer->GetListFirstBackward(top, KEYSIG);
            if (found) keySig = vrv_cast<const KeySig *>(found);
        }
        if (!keySig) keySig = layer->GetCurrentKeySig();

        std::map<int, int> key;
        if (!keySig) return key;
        MapOfOctavedPitchAccid pitchAccids;
        keySig->FillMap(pitchAccids);
        for (const auto &[octaved, accid] : pitchAccids) {
            // FillMap repeats every letter over ten octaves; octave 0 is 1..7
            if ((octaved < 1) || (octaved > 7)) continue;
            const int alteration = WrittenAlteration(accid);
            if (alteration != 0) key[octaved] = alteration;
        }
        return key;
    }

    // Position of `element` in its measure's horizontal alignment: (time, 0 for a grace column, 1
    // for the main one) - a grace note's accidental counts before the main note of the same time.
    using AlignKey = std::pair<Fraction, int>;

    bool GetAlignKey(const LayerElement *element, AlignKey &key)
    {
        const Object *object = element;
        while (object) {
            if (object->IsLayerElement()) {
                const Alignment *alignment = vrv_cast<const LayerElement *>(object)->GetAlignment();
                if (alignment) {
                    key = { alignment->GetTime(), (alignment->GetType() == ALIGNMENT_GRACENOTE) ? 0 : 1 };
                    return true;
                }
            }
            object = object->GetParent();
        }
        return false;
    }

    std::string PitchKey(int pname, int oct)
    {
        return std::string(1, "cdefgab"[pname - 1]) + std::to_string(oct);
    }

    struct WrittenAccid {
        AlignKey at;
        std::string pitch; // "g4"
        int alteration;
    };

    int NoteOct(const Note *note)
    {
        return note->HasOct() ? note->GetOct() : note->GetOctDefault();
    }

    bool IsPitched(const Note *note)
    {
        return note->HasPname() && (note->HasOct() || note->HasOctDefault());
    }

    // Trim the "-rend<N>" suffix of an expanded id (§2.4, rule 2); the caller decides whether the
    // base is a real id.
    std::string NotatedId(const std::string &id)
    {
        static const std::regex suffix("^(.*)-rend([0-9]+)$");
        std::smatch match;
        if (std::regex_match(id, match, suffix)) return match[1].str();
        return id;
    }

} // namespace

BridgePitchPos BridgePitchPosBuilder::Build(Doc *doc, int firstPage, int lastPage, const MIDIEventLog &midiLog)
{
    assert(doc);
    BridgePitchPos result;

    // Shift by id. The first pass carries the notated id, later passes `<id>-rend<N>`; the notation
    // context is the same in every pass, so a pass that disagrees with the first one is a bug.
    std::map<std::string, int> shifts;
    for (const auto &[id, shift] : midiLog.shifts) {
        const auto [it, inserted] = shifts.try_emplace(id, shift);
        if (!inserted && (it->second != shift)) ++result.conflictingShift;
    }
    for (const auto &[id, shift] : shifts) {
        const std::string base = NotatedId(id);
        if (base == id) continue;
        const auto baseIt = shifts.find(base);
        if ((baseIt != shifts.end()) && (baseIt->second != shift)) ++result.conflictingShift;
    }

    const int pageCount = doc->GetPageCount();
    for (int p = std::max(firstPage, 0); (p <= lastPage) && (p < pageCount); ++p) {
        Page *page = vrv_cast<Page *>(doc->GetPages()->GetChild(p));
        assert(page);

        ListOfObjects measures = page->FindAllDescendantsByType(MEASURE);
        for (Object *measureObject : measures) {
            // Notes and rests in document order
            ClassIdsComparison comparison({ NOTE, REST, MREST, MULTIREST });
            ListOfObjects elements;
            measureObject->FindAllDescendantsByComparison(&elements, &comparison);

            // Written accidentals of the measure, by the staff they are drawn on
            std::map<const Staff *, std::vector<WrittenAccid>> written;
            for (Object *object : elements) {
                if (!object->Is(NOTE)) continue;
                Note *note = vrv_cast<Note *>(object);
                if (!IsPitched(note)) continue;
                const Accid *accid = note->GetDrawingAccid();
                if (!accid || !accid->HasAccid()) continue;
                const Staff *staff = note->GetAncestorStaff(RESOLVE_CROSS_STAFF, false);
                AlignKey at;
                if (!staff || !GetAlignKey(note, at)) continue;
                written[staff].push_back(
                    { at, PitchKey(note->GetPname(), NoteOct(note)), WrittenAlteration(accid->GetAccid()) });
            }
            for (auto &[staff, list] : written) {
                std::stable_sort(list.begin(), list.end(),
                    [](const WrittenAccid &a, const WrittenAccid &b) { return a.at < b.at; });
            }

            for (Object *object : elements) {
                const bool isNote = object->Is(NOTE);
                const LayerElement *element = vrv_cast<const LayerElement *>(object);
                const Note *note = isNote ? vrv_cast<const Note *>(element) : NULL;
                if (note && !IsPitched(note)) continue;

                BridgePitchPosEvent event;
                event.isNote = isNote;
                event.clefLocOffset = ClefLocOffset(element);
                event.key = KeyAt(element);

                const auto shiftIt = shifts.find(element->GetID());
                if (shiftIt != shifts.end()) {
                    event.shift = shiftIt->second;
                }
                else {
                    ++result.missingShift;
                }

                // Alterations in force in this element's column, on its staff
                const Staff *staff = element->GetAncestorStaff(RESOLVE_CROSS_STAFF, false);
                AlignKey at;
                std::map<std::string, int> inForce;
                if (staff && written.count(staff) && GetAlignKey(element, at)) {
                    for (const WrittenAccid &accid : written.at(staff)) {
                        if (at < accid.at) break;
                        inForce[accid.pitch] = accid.alteration;
                    }
                }
                for (const auto &[pitch, alteration] : inForce) {
                    const int pname = int(std::string("cdefgab").find(pitch[0])) + 1;
                    const auto keyIt = event.key.find(pname);
                    const int keyAlteration = (keyIt == event.key.end()) ? 0 : keyIt->second;
                    if (alteration != keyAlteration) event.acc[pitch] = alteration;
                }

                if (note) {
                    event.pname = note->GetPname();
                    event.oct = NoteOct(note);
                    event.loc = note->GetDrawingLoc();
                    // The sounding alteration, exactly what Note::GetMIDIPitch applies (accid.ges over
                    // accid, else none): the Verovio never applies the key signature by itself - the
                    // importers write accid.ges on the notes the key signature alters.
                    const Accid *accid = note->GetDrawingAccid();
                    if (accid) {
                        event.alt = std::clamp(
                            TransPitch::GetChromaticAlteration(accid->GetAccidGes(), accid->GetAccid()), -2, 2);
                    }
                }

                result.events.emplace_back(element->GetID(), std::move(event));
            }
        }
    }

    return result;
}

} // namespace vrv
