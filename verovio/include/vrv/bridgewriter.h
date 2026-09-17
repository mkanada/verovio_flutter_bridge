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

namespace vrv {

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
     * Serializes manifest.json. `generator` identifies the Verovio/bridge version; S06's
     * Toolkit/CLI integration supplies it, this class does not invent one.
     */
    static std::string WriteManifest(const std::string &generator, int pageCount, bool hasTimemap);

    /**
     * Serializes the single-file `-t vsb-json` document: {manifest, glyphs, scene[, timemap]}.
     * `timemapJson` is the raw JSON array already produced by Toolkit::RenderToTimemap; passing
     * an empty string (the default, meaning no timemap) omits the "timemap" key entirely - a
     * timemap is never written as an empty array.
     */
    static std::string WriteSingleJson(const std::vector<const BridgePage *> &pages,
        const std::map<std::string, BridgeGlyphDef> &glyphs, const std::string &generator,
        const std::string &timemapJson = "");
};

} // namespace vrv

#endif // __VRV_BRIDGE_WRITER_H__
