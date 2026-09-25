/////////////////////////////////////////////////////////////////////////////
// Name:        bridgewriter.h
// Author:      Verovio Team
// Created:     2026
// Copyright (c) Authors and others. All rights reserved.
/////////////////////////////////////////////////////////////////////////////

#ifndef __VRV_BRIDGE_WRITER_H__
#define __VRV_BRIDGE_WRITER_H__

#include <map>
#include <string>
#include <vector>

//----------------------------------------------------------------------------

#include "bridgegeometry.h"
#include "pugixml.hpp"

namespace vrv {

class RunningElement;
struct MIDIEventLog;

//----------------------------------------------------------------------------
// BridgeAlternateSequence
//----------------------------------------------------------------------------

/**
 * One alternate page sequence (docs/formato/especificacao-v1.md §2.5, P02c): the arrival-point
 * measure id (`start`, already the notated id - §2.4's suffix rule already applied by whoever
 * built this) and the pages of its own paginated re-render, `index` 0-based within the sequence
 * (the same convention BridgeWriter::WriteScene uses for the normal pages). The pages point into
 * whatever BridgeDeviceContext rendered them; the caller must keep that device context alive at
 * least until WriteAlternates returns, and must not push any more pages into it after building
 * this - std::vector<BridgePage>'s own reallocation on push_back would invalidate these pointers.
 */
struct BridgeAlternateSequence {
    std::string start;
    std::vector<const BridgePage *> pages;
};

//----------------------------------------------------------------------------
// BridgeWriter
//----------------------------------------------------------------------------

/**
 * Serializes the Bridge scene IR (BridgePage / BridgeNode / BridgeShape / BridgeGlyphDef, built
 * by BridgeDeviceContext) into the JSON documents of the .vsb format
 * (docs/formato/especificacao-v1.md, normative). Key order matches the specification exactly and
 * numbers use a fixed, locale-independent formatting (at most 6 significant digits, no scientific
 * notation, no trailing zeros, "-0" normalized to "0"), so two exports of the same input are
 * byte-identical (S05 acceptance criterion 4) - callers must still seed a fixed, non-zero
 * Toolkit::ResetXmlIdSeed for that to hold, since auto-generated xml:id values are otherwise
 * randomized per process (see docs/plano/S04-bboxes-e-indice.md, "Achado importante").
 */
class BridgeWriter {
public:
    /**
     * Serializes scene.json: one entry per page, indexed by its position in `pages` (BridgePage
     * itself does not carry its own page index).
     */
    static std::string WriteScene(const std::vector<const BridgePage *> &pages);

    /**
     * Serializes glyphs.json: the glyph dictionary. Iteration order follows the map's own key
     * order (glyphId, ascending), satisfying the "ordenado por glyphId" determinism rule for free
     * since BridgeDeviceContext::GetGlyphs() already keys its cache the same way.
     */
    static std::string WriteGlyphs(const std::map<std::string, BridgeGlyphDef> &glyphs);

    /**
     * Builds the piece metadata (§2.3).
     *
     * The title is derived from what Verovio renders: `renderedHeader` is the first page's header
     * as Page::GetHeader() resolves it, so `--header none` (NULL - nothing is drawn) yields no
     * title, `--header auto` yields the first line of the title block generated from the MEI
     * header, and `--header encoded` yields the encoded header's title (a MusicXML <credit>, an
     * MEI <pgHead>) - the same text the SVG shows at the top of the page.
     *
     * The credited people come from the MEI header kept by Doc::m_header (filled by both the MEI
     * and the MusicXML importers), whatever the header option: the `titleStmt` elements
     * `composer`/`lyricist`/`arranger`/`author` plus the `respStmt/persName` whose @role credits
     * the music (composer, lyricist, arranger, translator, harmonizer, author, poet - never an
     * encoder or editor). Text is whitespace-normalized.
     */
    static BridgeMeta ExtractMeta(const pugi::xml_document &header, const RunningElement *renderedHeader);

    /**
     * Serializes meta.json (§2.3). Empty fields are omitted; the caller omits the whole document
     * when BridgeMeta::IsEmpty().
     */
    static std::string WriteMeta(const BridgeMeta &meta);

    /**
     * Serializes manifest.json. `generator` identifies the Verovio/bridge version; S06's
     * Toolkit/CLI integration supplies it, this class does not invent one.
     *
     * `hasDebug` (§2.6, debug mode, `--vsb-debug`) adds the `debugOptions`/`debugSource` file
     * entries: the effective Toolkit options and the source document exactly as loaded, embedded
     * so the render can be reproduced from the package alone.
     */
    static std::string WriteManifest(const std::string &generator, int pageCount, bool hasTimemap,
        bool hasMeta = false, bool hasAlternates = false, bool hasDebug = false, bool hasMidi = false);

    /**
     * Serializes alternates.json (§2.5): one entry per sequence, `start` plus its own pages
     * (indexed 0-based within the sequence, same convention as WriteScene). The caller omits the
     * whole document when `sequences` is empty - there is no "sequences": [] on disk.
     */
    static std::string WriteAlternates(const std::vector<BridgeAlternateSequence> &sequences);

    /**
     * Serializes midi.json (§2.7): the events GenerateMIDIFunctor emits when Doc::ExportMIDI is
     * given an event log (G01, docs/plano/G01-gravador-de-notas-midi.md), split into `notes` and
     * `pedal`, converted from quarter notes (`log`'s own unit) to milliseconds using the tempo
     * breakpoints in `log.tempos` - the same piecewise integration a MIDI player follows over the
     * .mid's own tempo track, without its tick quantization. The caller omits the whole document
     * when `log.events` is empty.
     */
    static std::string WriteMidi(const MIDIEventLog &log);

    /**
     * Serializes the single-file `-t vsb-json` document: {manifest, glyphs, scene[, timemap][,
     * meta][, alternates][, midi][, debug]}. `timemapJson` is the raw JSON array already produced by
     * Toolkit::RenderToTimemap; passing an empty string (the default, meaning no timemap) omits the
     * "timemap" key entirely - a timemap is never written as an empty array. An empty `meta` omits
     * "meta" the same way, an empty `sequences` omits "alternates", and a null/empty `midiLog`
     * omits "midi".
     *
     * `debugOptionsJson` (§2.6, debug mode, `--vsb-debug`) is the raw JSON object already produced
     * by Toolkit::GetOptions; `debugSource` is the source document exactly as Toolkit::LoadData
     * received it. Both empty (the default) omits the "debug" key entirely - passing one without
     * the other still writes it as an empty value, on the caller (only Toolkit::RenderToBridgeJson
     * calls this with the flag on, and always supplies both together).
     */
    static std::string WriteSingleJson(const std::vector<const BridgePage *> &pages,
        const std::map<std::string, BridgeGlyphDef> &glyphs, const std::string &generator,
        const std::string &timemapJson = "", const BridgeMeta &meta = BridgeMeta(),
        const std::vector<BridgeAlternateSequence> &sequences = {}, const std::string &debugOptionsJson = "",
        const std::string &debugSource = "", const MIDIEventLog *midiLog = nullptr);
};

} // namespace vrv

#endif // __VRV_BRIDGE_WRITER_H__
