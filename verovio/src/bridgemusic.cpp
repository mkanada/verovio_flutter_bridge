/////////////////////////////////////////////////////////////////////////////
// Name:        bridgemusic.cpp
// Author:      Verovio Team
// Created:     2026
// Copyright (c) Authors and others. All rights reserved.
/////////////////////////////////////////////////////////////////////////////

#include "bridgemusic.h"

//----------------------------------------------------------------------------

#include <algorithm>
#include <map>
#include <set>

//----------------------------------------------------------------------------

#include "attconverter.h"
#include "chord.h"
#include "comparison.h"
#include "dir.h"
#include "doc.h"
#include "durationinterface.h"
#include "ending.h"
#include "gracegrp.h"
#include "harm.h"
#include "keysig.h"
#include "label.h"
#include "layer.h"
#include "layerelement.h"
#include "measure.h"
#include "metersig.h"
#include "mordent.h"
#include "note.h"
#include "scoredef.h"
#include "staff.h"
#include "tempo.h"
#include "text.h"
#include "timeinterface.h"
#include "transposition.h"
#include "trill.h"
#include "tuplet.h"
#include "turn.h"
#include "vrv.h"

namespace vrv {

namespace {

    //------------------------------------------------------------------------
    // Text of the enumeration values, as the MEI export writes them
    //------------------------------------------------------------------------

    const AttConverter &Converter()
    {
        static const AttConverter converter;
        return converter;
    }

    std::string BarrendText(data_BARRENDITION value)
    {
        if (value == BARRENDITION_NONE) return "";
        return Converter().BarrenditionToStr(value);
    }

    std::string GraceText(data_GRACE value)
    {
        if (value == GRACE_acc) return "acc";
        if (value == GRACE_unacc) return "unacc";
        return "";
    }

    // The text of every Text descendant (a Label, a Tempo), in document order, as the Verovio draws it
    std::string PlainText(const Object *object)
    {
        std::string text;
        for (const Object *textObject : object->FindAllDescendantsByType(TEXT)) {
            text += UTF32to8(vrv_cast<const Text *>(textObject)->GetText());
        }
        return text;
    }

    // Alteration (-2..2) of a written accidental, as bridgepitchpos.cpp reads it
    int WrittenAlteration(data_ACCIDENTAL_WRITTEN accid)
    {
        const int value = TransPitch::GetChromaticAlteration(ACCIDENTAL_GESTURAL_NONE, accid);
        return std::clamp(value, -2, 2);
    }

    //------------------------------------------------------------------------
    // Key and meter in force on each staff
    //------------------------------------------------------------------------

    struct KeyState {
        std::string sig; // "" = null
        int fifths = 0;
        std::string mode; // "" = null
    };

    struct MeterState {
        int count = 0;
        int unit = 0;
        std::string sym; // "" = null
        bool known = false;
    };

    KeyState KeyStateOf(const KeySig *keySig)
    {
        KeyState state;
        // A key signature that is not a standard one (keyAccid children) has no name in @sig
        const std::pair<int, data_ACCIDENTAL_WRITTEN> sig = keySig->GetSig();
        if (keySig->HasNonAttribKeyAccidChildren()) {
            state.sig = "";
        }
        else if (sig.second == ACCIDENTAL_WRITTEN_s) {
            state.sig = std::to_string(sig.first) + "s";
        }
        else if (sig.second == ACCIDENTAL_WRITTEN_f) {
            state.sig = std::to_string(sig.first) + "f";
        }
        else if (sig.first == 0) {
            state.sig = "0";
        }
        // Sum of the alterations the signature puts on each letter (sharp +1, flat -1): the same map
        // bridgepitchpos.cpp reads, one entry per letter in octave 0 (1..7)
        MapOfOctavedPitchAccid pitchAccids;
        keySig->FillMap(pitchAccids);
        for (const auto &[octaved, accid] : pitchAccids) {
            if ((octaved < 1) || (octaved > 7)) continue;
            state.fifths += WrittenAlteration(accid);
        }
        if (keySig->GetMode() != MODE_NONE) state.mode = Converter().ModeToStr(keySig->GetMode());
        return state;
    }

    MeterState MeterStateOf(const MeterSig *meterSig)
    {
        MeterState state;
        state.count = meterSig->GetTotalCount();
        state.unit = meterSig->GetUnit();
        // Only common and cut are symbols §2.9 knows; any other value (or none) is a plain numeric meter
        if (meterSig->GetSym() == METERSIGN_common) state.sym = "common";
        if (meterSig->GetSym() == METERSIGN_cut) state.sym = "cut";
        state.known = true;
        return state;
    }

    // Everything the walk over the document carries from one object to the next
    struct WalkState {
        std::set<int> staves; // every staff number the document defines
        std::map<int, KeyState> keys;
        std::map<int, MeterState> meters;
        std::set<const Object *> applied; // key/meter changes already in force
    };

    // The staves a key or meter change applies to: its staffDef's, its layer's, or all of them for a
    // change written in a scoreDef without staffDef.
    std::vector<int> TargetStaves(const Object *change, const WalkState &state)
    {
        const Object *parent = change->GetParent();
        if (!parent) return {};
        if (parent->Is(STAFFDEF)) return { vrv_cast<const StaffDef *>(parent)->GetN() };
        if (parent->Is(LAYER)) {
            const Object *staff = parent->GetFirstAncestor(STAFF);
            if (!staff) return {};
            return { vrv_cast<const Staff *>(staff)->GetN() };
        }
        if (parent->Is(SCOREDEF)) return std::vector<int>(state.staves.begin(), state.staves.end());
        return {};
    }

    // A change in a layer is at the start of its measure when only other changes or clefs come before it
    bool AtMeasureStart(const Object *change)
    {
        const Object *parent = change->GetParent();
        if (!parent || !parent->Is(LAYER)) return false;
        for (int i = 0; i < change->GetIdx(); ++i) {
            const Object *sibling = parent->GetChild(i);
            if (!sibling->Is(KEYSIG) && !sibling->Is(METERSIG) && !sibling->Is(CLEF)) return false;
        }
        return true;
    }

    void ApplyChange(const Object *change, WalkState &state)
    {
        state.applied.insert(change);
        if (change->Is(KEYSIG)) {
            const KeyState key = KeyStateOf(vrv_cast<const KeySig *>(change));
            for (int n : TargetStaves(change, state)) state.keys[n] = key;
        }
        else if (change->Is(METERSIG)) {
            const MeterState meter = MeterStateOf(vrv_cast<const MeterSig *>(change));
            for (int n : TargetStaves(change, state)) state.meters[n] = meter;
        }
    }

    //------------------------------------------------------------------------
    // Events
    //------------------------------------------------------------------------

    // The staff a note, rest, mRest or space is written on (§2.9, rule 4): its own @staff, else its
    // chord's, else the staff that holds it.
    int WrittenStaff(const LayerElement *element, int containingStaff)
    {
        const DurationInterface *durations = element->GetDurationInterface();
        if (durations && !durations->GetStaff().empty()) return durations->GetStaff().front();
        if (element->Is(NOTE)) {
            const Chord *chord = vrv_cast<const Note *>(element)->IsChordTone();
            const DurationInterface *chordDurations = chord ? chord->GetDurationInterface() : NULL;
            if (chordDurations && !chordDurations->GetStaff().empty()) return chordDurations->GetStaff().front();
        }
        return containingStaff;
    }

    // "acc", "unacc" or "" (false): the note's @grace, else its chord's, else its graceGrp's
    std::string EventGrace(const LayerElement *element)
    {
        if (!element->Is(NOTE)) return "";
        const Note *note = vrv_cast<const Note *>(element);
        std::string grace = GraceText(note->GetGrace());
        if (!grace.empty()) return grace;
        if (const Chord *chord = note->IsChordTone()) {
            grace = GraceText(chord->GetGrace());
            if (!grace.empty()) return grace;
        }
        if (const Object *graceGrp = element->GetFirstAncestor(GRACEGRP)) {
            return GraceText(vrv_cast<const GraceGrp *>(graceGrp)->GetGrace());
        }
        return "";
    }

    // The innermost tuplet around the element (§2.9, rule 4): num and numbase, or none (num 0)
    BridgeMusicTuplet TupletOf(const LayerElement *element)
    {
        BridgeMusicTuplet tuplet;
        if (const Object *object = element->GetFirstAncestor(TUPLET)) {
            const Tuplet *value = vrv_cast<const Tuplet *>(object);
            if ((value->GetNum() > 0) && (value->GetNumbase() > 0)) {
                tuplet.num = value->GetNum();
                tuplet.numbase = value->GetNumbase();
            }
        }
        return tuplet;
    }

    // Fills `event` for a note, rest, mRest or space; false for anything else
    bool EventOf(const LayerElement *element, BridgeMusicEvent &event)
    {
        if (element->Is(NOTE)) {
            event.t = "n";
            const Note *note = vrv_cast<const Note *>(element);
            if (const Chord *chord = note->IsChordTone()) event.chord = chord->GetID();
        }
        else if (element->Is(REST)) {
            event.t = "r";
        }
        else if (element->Is(MREST)) {
            event.t = "mr";
        }
        else if (element->Is(SPACE)) {
            event.t = "s";
        }
        else {
            return false;
        }
        event.id = element->GetID();
        event.grace = EventGrace(element);
        event.tuplet = TupletOf(element);
        return true;
    }

    BridgeMusicStaff &StaffEntry(std::vector<BridgeMusicStaff> &staves, int n)
    {
        for (BridgeMusicStaff &staff : staves) {
            if (staff.n == n) return staff;
        }
        BridgeMusicStaff staff;
        staff.n = n;
        staves.push_back(staff);
        return staves.back();
    }

    BridgeMusicLayer &LayerEntry(BridgeMusicStaff &staff, int n)
    {
        for (BridgeMusicLayer &layer : staff.layers) {
            if (layer.n == n) return layer;
        }
        BridgeMusicLayer layer;
        layer.n = n;
        staff.layers.push_back(layer);
        return staff.layers.back();
    }

    // Staves and layers of the measure: first every staff and layer the notation has, in document
    // order, then each event on the staff and layer it is written on (a cross-staff note moves to
    // its own @staff, keeping the layer of its origin).
    void AddStavesAndEvents(const Measure *measure, std::vector<BridgeMusicStaff> &staves)
    {
        for (int i = 0; i < measure->GetChildCount(); ++i) {
            const Object *child = measure->GetChild(i);
            if (!child->Is(STAFF)) continue;
            const Staff *staff = vrv_cast<const Staff *>(child);
            StaffEntry(staves, staff->GetN());
            for (int j = 0; j < staff->GetChildCount(); ++j) {
                const Object *layerObject = staff->GetChild(j);
                if (!layerObject->Is(LAYER)) continue;
                const Layer *layer = vrv_cast<const Layer *>(layerObject);
                LayerEntry(StaffEntry(staves, staff->GetN()), layer->GetN());
            }
        }

        for (int i = 0; i < measure->GetChildCount(); ++i) {
            const Object *child = measure->GetChild(i);
            if (!child->Is(STAFF)) continue;
            const Staff *staff = vrv_cast<const Staff *>(child);
            for (int j = 0; j < staff->GetChildCount(); ++j) {
                const Object *layerObject = staff->GetChild(j);
                if (!layerObject->Is(LAYER)) continue;
                const Layer *layer = vrv_cast<const Layer *>(layerObject);

                ClassIdsComparison comparison({ NOTE, REST, MREST, SPACE });
                ListOfConstObjects elements;
                layer->FindAllDescendantsByComparison(&elements, &comparison);
                for (const Object *elementObject : elements) {
                    const LayerElement *element = vrv_cast<const LayerElement *>(elementObject);
                    BridgeMusicEvent event;
                    if (!EventOf(element, event)) continue;
                    const int target = WrittenStaff(element, staff->GetN());
                    LayerEntry(StaffEntry(staves, target), layer->GetN()).events.push_back(event);
                }
            }
        }
    }

    //------------------------------------------------------------------------
    // Measures, parts, ornaments and tempi
    //------------------------------------------------------------------------

    // The key and meter in force at the start of the measure, from its first (lowest @n) staff
    int FirstStaffOf(const Measure *measure, const WalkState &state)
    {
        int first = -1;
        for (int i = 0; i < measure->GetChildCount(); ++i) {
            const Object *child = measure->GetChild(i);
            if (!child->Is(STAFF)) continue;
            const int n = vrv_cast<const Staff *>(child)->GetN();
            if ((first < 0) || (n < first)) first = n;
        }
        if (first < 0 && !state.staves.empty()) first = *state.staves.begin();
        return first;
    }

    BridgeMusicMeasure MeasureOf(const Measure *measure, int index, const WalkState &state)
    {
        BridgeMusicMeasure out;
        out.id = measure->GetID();
        out.index = index;
        out.n = measure->GetN();
        out.left = BarrendText(measure->GetLeft());
        out.right = BarrendText(measure->GetRight());
        // The ending the layout assigned to the measure (PrepareMilestonesFunctor, before the cast-off
        // moves the measures out of their endings): the enclosing <ending>'s @n
        if (const Ending *ending = measure->GetDrawingEnding()) out.ending = ending->GetN();

        const int staff = FirstStaffOf(measure, state);
        const auto meterIt = state.meters.find(staff);
        if ((meterIt != state.meters.end()) && meterIt->second.known) {
            out.meter.count = meterIt->second.count;
            out.meter.unit = meterIt->second.unit;
            out.meter.sym = meterIt->second.sym;
        }
        else {
            LogWarning("music: measure %s has no meter in force", out.id.c_str());
        }
        const auto keyIt = state.keys.find(staff);
        if (keyIt != state.keys.end()) {
            out.key.sig = keyIt->second.sig;
            out.key.fifths = keyIt->second.fifths;
            out.key.mode = keyIt->second.mode;
        }

        AddStavesAndEvents(measure, out.staves);
        return out;
    }

    // The part a candidate element stands for: its label, and the @n of its staffDef (or of every staffDef
    // under a staffGrp). A candidate with no staff gives an empty staves list: the caller leaves it out.
    BridgeMusicPart PartOf(const Object *candidate)
    {
        BridgeMusicPart part;
        part.id = candidate->GetID();
        for (int j = 0; j < candidate->GetChildCount(); ++j) {
            const Object *child = candidate->GetChild(j);
            if (child->Is(LABEL)) part.name = PlainText(child);
        }
        if (candidate->Is(STAFFDEF)) {
            part.staves.push_back(vrv_cast<const StaffDef *>(candidate)->GetN());
        }
        else {
            for (const Object *staffDef : candidate->FindAllDescendantsByType(STAFFDEF)) {
                part.staves.push_back(vrv_cast<const StaffDef *>(staffDef)->GetN());
            }
        }
        return part;
    }

    void AddPart(std::vector<BridgeMusicPart> &parts, const Object *candidate)
    {
        const BridgeMusicPart part = PartOf(candidate);
        if (!part.staves.empty()) parts.push_back(part);
    }

    // Parts of a MusicXML source (§2.9, rule 5): each <part> is a staffGrp (several staves) or a staffDef (one
    // staff) directly in the scoreDef's staffGrp.
    std::vector<BridgeMusicPart> PartsOfMusicXml(const Object *scoreDef)
    {
        std::vector<const Object *> candidates;
        for (int i = 0; i < scoreDef->GetChildCount(); ++i) {
            const Object *child = scoreDef->GetChild(i);
            if (child->Is(STAFFDEF)) {
                candidates.push_back(child);
            }
            else if (child->Is(STAFFGRP)) {
                for (int j = 0; j < child->GetChildCount(); ++j) {
                    const Object *part = child->GetChild(j);
                    if (part->Is(STAFFGRP) || part->Is(STAFFDEF)) candidates.push_back(part);
                }
            }
        }

        std::vector<BridgeMusicPart> parts;
        for (const Object *candidate : candidates) AddPart(parts, candidate);
        return parts;
    }

    // Parts of an MEI source (§2.9, rule 5): each staffGrp of the scoreDef is a part, and so is each of its
    // staffGrp children. A staffGrp with no staffGrp child is one part with all its staves (an MEI without
    // parts). A staffDef that sits directly in a staffGrp which has staffGrp children is a part of its own.
    std::vector<BridgeMusicPart> PartsOfMei(const Object *scoreDef)
    {
        std::vector<BridgeMusicPart> parts;
        for (int i = 0; i < scoreDef->GetChildCount(); ++i) {
            const Object *child = scoreDef->GetChild(i);
            if (child->Is(STAFFDEF)) {
                AddPart(parts, child);
            }
            else if (child->Is(STAFFGRP)) {
                bool hasGroup = false;
                for (int j = 0; j < child->GetChildCount(); ++j) {
                    if (child->GetChild(j)->Is(STAFFGRP)) hasGroup = true;
                }
                if (!hasGroup) {
                    AddPart(parts, child);
                    continue;
                }
                for (int j = 0; j < child->GetChildCount(); ++j) {
                    const Object *part = child->GetChild(j);
                    if (part->Is(STAFFGRP) || part->Is(STAFFDEF)) AddPart(parts, part);
                }
            }
        }
        return parts;
    }

    // "" when the element carries no @startid, else the id without its '#'
    std::string StartIdOf(const TimeSpanningInterface *span)
    {
        std::string startid = span->GetStartid();
        if (!startid.empty() && (startid[0] == '#')) startid.erase(0, 1);
        return startid;
    }

    //------------------------------------------------------------------------
    // Harmonies and directions
    //------------------------------------------------------------------------

    // "above", "below" or "" (null): the @place of a control element
    std::string PlaceText(data_STAFFREL place)
    {
        if (place == STAFFREL_above) return "above";
        if (place == STAFFREL_below) return "below";
        return "";
    }

    // The first staff of a control element's @staff; a MEI element may have none, then the measure's first staff
    int StaffOf(const xsdPositiveInteger_List &staves, int fallback)
    {
        if (!staves.empty()) return staves.front();
        return std::max(1, fallback);
    }

    // The structure the MusicXML gave the harmony (HarmData), and the text the Verovio draws
    BridgeMusicHarmony HarmonyOf(const Harm *harm, int measure, int staff)
    {
        BridgeMusicHarmony out;
        out.id = harm->GetID();
        out.measure = measure;
        out.staff = staff;
        out.tstamp = harm->GetTstamp();
        out.text = PlainText(harm);
        if (const HarmData *data = harm->GetHarmData()) {
            out.root = data->root;
            out.rootAlter = data->rootAlter;
            out.kind = data->kind;
            out.kindText = data->kindText;
            out.bass = data->bass;
            out.bassAlter = data->bassAlter;
            for (const HarmDegree &degree : data->degrees) {
                BridgeMusicDegree entry;
                entry.value = degree.value;
                entry.alter = degree.alter;
                entry.type = degree.type;
                out.degrees.push_back(entry);
            }
            out.numeralRoot = data->numeralRoot;
            out.numeralAlter = data->numeralAlter;
        }
        return out;
    }

} // namespace

BridgeMusic ReadBridgeMusic(Doc &doc)
{
    BridgeMusic music;

    // The first scoreDef (the Score's own, with the staffGrps and the initial key and meter) is not
    // reached by a search from the Doc once the Doc is cast off: its measures are in the pages, but the
    // Score keeps this scoreDef. So it is read on its own, first.
    const ScoreDef *firstScoreDef = doc.GetFirstScoreDef();
    ClassIdsComparison initialComparison({ STAFFDEF, KEYSIG, METERSIG });
    ListOfConstObjects initial;
    if (firstScoreDef) firstScoreDef->FindAllDescendantsByComparison(&initial, &initialComparison);

    // Everything else, in document order: a measure precedes its changes, layers and controls, and a
    // scoreDef of a section precedes the measures after it.
    ClassIdsComparison comparison(
        { SCOREDEF, STAFFDEF, STAFF, MEASURE, KEYSIG, METERSIG, TRILL, MORDENT, TURN, TEMPO, HARM, DIR });
    ListOfObjects objects;
    doc.FindAllDescendantsByComparison(&objects, &comparison);

    WalkState state;
    for (const Object *object : initial) {
        if (object->Is(STAFFDEF)) state.staves.insert(vrv_cast<const StaffDef *>(object)->GetN());
    }
    for (const Object *object : objects) {
        if (object->Is(STAFFDEF)) {
            state.staves.insert(vrv_cast<const StaffDef *>(object)->GetN());
        }
        else if (object->Is(STAFF)) {
            state.staves.insert(vrv_cast<const Staff *>(object)->GetN());
        }
    }
    for (int n : state.staves) state.keys[n] = KeyState{ "0", 0, "" };

    for (const Object *change : initial) {
        if (change->Is(KEYSIG) || change->Is(METERSIG)) ApplyChange(change, state);
    }
    if (firstScoreDef) {
        music.parts = (doc.GetSourceFormat() == MUSICXML) ? PartsOfMusicXml(firstScoreDef) : PartsOfMei(firstScoreDef);
    }

    ClassIdsComparison changeComparison({ KEYSIG, METERSIG });
    std::map<const Object *, int> measureIndex;
    for (const Object *object : objects) {
        if (object->Is(KEYSIG) || object->Is(METERSIG)) {
            if (!state.applied.count(object)) ApplyChange(object, state);
        }
        else if (object->Is(MEASURE)) {
            const Measure *measure = vrv_cast<const Measure *>(object);
            // The changes at the very start of this measure are in force for it: apply them first, the
            // loop reaches them later and skips them then.
            ListOfConstObjects changes;
            measure->FindAllDescendantsByComparison(&changes, &changeComparison);
            for (const Object *change : changes) {
                if (!state.applied.count(change) && AtMeasureStart(change)) ApplyChange(change, state);
            }
            const int index = static_cast<int>(music.measures.size());
            measureIndex[object] = index;
            music.measures.push_back(MeasureOf(measure, index, state));
        }
        else if (object->Is(TRILL) || object->Is(MORDENT) || object->Is(TURN)) {
            const TimeSpanningInterface *span = object->GetTimeSpanningInterface();
            const std::string startid = span ? StartIdOf(span) : "";
            const double tstamp = span ? span->GetTstamp() : 0.0;
            // A control with neither @startid nor @tstamp has no place in the score: left out (§2.9, rule 6)
            if (startid.empty() && (tstamp < 1.0)) {
                LogWarning("music: %s %s has no @startid or @tstamp, left out of music.json",
                    object->GetClassName().c_str(), object->GetID().c_str());
                continue;
            }
            const Object *measureObject = object->GetFirstAncestor(MEASURE);
            const auto indexIt = measureObject ? measureIndex.find(measureObject) : measureIndex.end();
            if (indexIt == measureIndex.end()) {
                LogWarning("music: %s %s is outside a measure, left out of music.json",
                    object->GetClassName().c_str(), object->GetID().c_str());
                continue;
            }
            BridgeMusicOrnament ornament;
            ornament.id = object->GetID();
            ornament.kind = object->Is(TRILL) ? "trill" : (object->Is(MORDENT) ? "mordent" : "turn");
            ornament.measure = indexIt->second;
            ornament.startid = startid;
            ornament.tstamp = (tstamp < 1.0) ? 0.0 : tstamp;
            music.ornaments.push_back(ornament);
        }
        else if (object->Is(TEMPO)) {
            const Tempo *tempo = vrv_cast<const Tempo *>(object);
            const Object *measure = object->GetFirstAncestor(MEASURE);
            const auto indexIt = measure ? measureIndex.find(measure) : measureIndex.end();
            if (indexIt == measureIndex.end()) {
                LogWarning("music: tempo %s is outside a measure, left out of music.json", tempo->GetID().c_str());
                continue;
            }
            BridgeMusicTempo entry;
            entry.id = tempo->GetID();
            entry.measure = indexIt->second;
            entry.bpm = tempo->HasMidiBpm() ? tempo->GetMidiBpm() : 0.0;
            entry.text = PlainText(tempo);
            music.tempi.push_back(entry);
        }
        else if (object->Is(HARM)) {
            const Harm *harm = vrv_cast<const Harm *>(object);
            // A figured bass (<figured-bass>) is a Harm too, with F elements instead of a text: not a <harmony>
            if (harm->FindDescendantByType(FB)) continue;
            const Object *measureObject = object->GetFirstAncestor(MEASURE);
            const auto indexIt = measureObject ? measureIndex.find(measureObject) : measureIndex.end();
            if (indexIt == measureIndex.end()) {
                LogWarning("music: harmony %s is outside a measure, left out of music.json", harm->GetID().c_str());
                continue;
            }
            if (PlainText(harm).empty() || (harm->GetTstamp() < 1.0)) {
                LogWarning("music: harmony %s has no text or no @tstamp, left out of music.json",
                    harm->GetID().c_str());
                continue;
            }
            const Measure *measure = vrv_cast<const Measure *>(measureObject);
            const int staff = StaffOf(harm->GetStaff(), FirstStaffOf(measure, state));
            music.harmonies.push_back(HarmonyOf(harm, indexIt->second, staff));
        }
        else if (object->Is(DIR)) {
            const Dir *dir = vrv_cast<const Dir *>(object);
            // A coda or a segno without words has no text: it is not a direction (§2.9, rule 8)
            const std::string text = PlainText(dir);
            if (text.empty()) continue;
            const Object *measureObject = object->GetFirstAncestor(MEASURE);
            const auto indexIt = measureObject ? measureIndex.find(measureObject) : measureIndex.end();
            if (indexIt == measureIndex.end()) {
                LogWarning("music: direction %s is outside a measure, left out of music.json", dir->GetID().c_str());
                continue;
            }
            if (dir->GetTstamp() < 1.0) {
                LogWarning("music: direction %s has no @tstamp, left out of music.json", dir->GetID().c_str());
                continue;
            }
            const Measure *measure = vrv_cast<const Measure *>(measureObject);
            BridgeMusicDirection entry;
            entry.id = dir->GetID();
            entry.measure = indexIt->second;
            entry.staff = StaffOf(dir->GetStaff(), FirstStaffOf(measure, state));
            entry.tstamp = dir->GetTstamp();
            entry.place = PlaceText(dir->GetPlace());
            entry.text = text;
            music.directions.push_back(entry);
        }
    }

    return music;
}

} // namespace vrv
