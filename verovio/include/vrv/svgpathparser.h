/////////////////////////////////////////////////////////////////////////////
// Name:        svgpathparser.h
// Author:      Verovio Team
// Created:     2026
// Copyright (c) Authors and others. All rights reserved.
/////////////////////////////////////////////////////////////////////////////

#ifndef __VRV_SVG_PATH_PARSER_H__
#define __VRV_SVG_PATH_PARSER_H__

#include <string>
#include <vector>

//----------------------------------------------------------------------------

#include "bridgegeometry.h"

namespace vrv {

//----------------------------------------------------------------------------
// SVG path parsing (glyph outlines)
//----------------------------------------------------------------------------

/**
 * Parses the "d" attribute of an SVG <path> (without any transform applied) into Bridge scene
 * subpaths, in the coordinate system of the path data itself. Returns false (after logging a
 * warning) if the data contains a command this parser cannot handle.
 */
bool ParseSvgPathData(const std::string &d, std::vector<BridgeBezier> &paths);

/**
 * Parses the XML of a Verovio SMuFL glyph (Glyph::GetXML(): one or more
 * "<g><path transform=\"scale(sx,sy)\" d=\"...\"/></g>"), applying each <path>'s scale
 * transform to both its vertices and its tangents. Subpaths are appended to `paths` in
 * document order.
 */
bool ParseGlyphXml(const std::string &xml, std::vector<BridgeBezier> &paths);

} // namespace vrv

#endif // __VRV_SVG_PATH_PARSER_H__
