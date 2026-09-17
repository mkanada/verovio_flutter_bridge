/////////////////////////////////////////////////////////////////////////////
// Name:        bridgegeometry.h
// Author:      Verovio Team
// Created:     2026
// Copyright (c) Authors and others. All rights reserved.
/////////////////////////////////////////////////////////////////////////////

#ifndef __VRV_BRIDGE_GEOMETRY_H__
#define __VRV_BRIDGE_GEOMETRY_H__

#include <memory>
#include <optional>
#include <string>
#include <vector>

//----------------------------------------------------------------------------

#include "devicecontextbase.h"

namespace vrv {

//----------------------------------------------------------------------------
// BridgeVec, BridgeBezier, BridgeShape
//----------------------------------------------------------------------------

struct BridgeVec {
    double x = 0.0;
    double y = 0.0;
};

/**
 * A subpath in the Bridge scene IR: tangents are relative to their vertex.
 * Scene shapes store page coordinates; glyph definitions store font units.
 */
struct BridgeBezier {
    std::vector<BridgeVec> v; // vertices (page coordinates)
    std::vector<BridgeVec> i; // in-tangent of each vertex
    std::vector<BridgeVec> o; // out-tangent of each vertex
    bool closed = false;
};

enum class BridgeShapeKind { Path, Rect, Ellipse };

struct BridgeShape {
    BridgeShapeKind kind = BridgeShapeKind::Path;
    std::vector<BridgeBezier> paths; // Path: subpaths share the same fill
    BridgeVec center, size; // Rect / Ellipse
    double radius = 0.0; // rounded Rect
    bool hasFill = false;
    int fillColor = COLOR_NONE; // COLOR_NONE = inherit the group color
    double fillOpacity = 1.0;
    bool hasStroke = false;
    double strokeWidth = 1.0;
    int strokeColor = COLOR_NONE;
    double strokeOpacity = 1.0;
    LineCapStyle lineCap = LINECAP_DEFAULT;
    LineJoinStyle lineJoin = LINEJOIN_DEFAULT;
    double dashLength = 0.0;
    double gapLength = 0.0;
};

struct BridgeGlyphDef {
    std::string font;
    std::string codepoint;
    int unitsPerEm = 0;
    int horizAdvX = 0;
    int bbox[4] = { 0, 0, 0, 0 };
    std::vector<BridgeBezier> paths;
};

struct BridgeGlyphUse {
    std::string glyphId;
    double x = 0.0, y = 0.0, sx = 1.0, sy = 1.0;
};

/**
 * A run of non-SMuFL ("common") text, e.g. a title, tempo mark or fingering, built by
 * BridgeDeviceContext::DrawText (D01, docs/plano/D01-texto-comum.md) and carried as a native
 * text run in the Bridge scene IR instead of glyph shapes.
 */
struct BridgeTextRun {
    std::u32string text;
    Point origin; // anchor (page px), before any alignment offset
    data_HORIZONTALALIGNMENT alignment = HORIZONTALALIGNMENT_left;
    double pointSize = 0.0; // same unit space as glyph uses (already page px)
    double letterSpacing = 0.0;
    data_FONTSTYLE style = FONTSTYLE_NONE;
    data_FONTWEIGHT weight = FONTWEIGHT_NONE;
    int color = COLOR_NONE; // COLOR_NONE = inherit, same convention as BridgeShape::fillColor
    bool hasBBox = false;
    double bbox[4] = { 0, 0, 0, 0 };
};

//----------------------------------------------------------------------------
// BridgeNode, BridgeChild, BridgePage
//----------------------------------------------------------------------------

struct BridgeNode;

struct BridgeChild {
    std::unique_ptr<BridgeNode> group; // non-null = subgroup
    std::optional<BridgeTextRun> text; // set = common text run
    std::optional<BridgeGlyphUse> glyphUse; // set = glyph use
    BridgeShape shape; // used when group == nullptr, text == nullopt, and glyphUse == nullopt
};

struct BridgeNode {
    std::string id; // xml:id (empty if not PRIMARY)
    std::string className; // Object::GetClassName() (+ extra classes) or the custom graphic name
    std::string colorCss; // @color or SetCustomGraphicColor; empty = inherit
    bool hidden = false;
    bool hasRotation = false;
    double rotation = 0.0;
    Point rotationOrigin;
    bool hasBBox = false;
    double bbox[4] = { 0, 0, 0, 0 }; // x0, y0, x1, y1 in viewBox units
    std::vector<BridgeChild> children; // document order: later entries paint on top
};

struct BridgeIndexEntry {
    std::string id;
    std::string className;
    int nodePath = -1;
    double bbox[4] = { 0, 0, 0, 0 };
};

struct BridgePage {
    std::unique_ptr<BridgeNode> root;
    int width = 0, height = 0, contentHeight = 0;
    int baseWidth = 0, baseHeight = 0;
    double userScaleX = 1.0, userScaleY = 1.0;
    double viewBoxFactor = 10.0;
    int originX = 0, originY = 0;
    std::vector<BridgeIndexEntry> index;
};

} // namespace vrv

#endif // __VRV_BRIDGE_GEOMETRY_H__
