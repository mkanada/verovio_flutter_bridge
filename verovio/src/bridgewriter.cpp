/////////////////////////////////////////////////////////////////////////////
// Name:        bridgewriter.cpp
// Author:      Verovio Team
// Created:     2026
// Copyright (c) Authors and others. All rights reserved.
/////////////////////////////////////////////////////////////////////////////

#include "bridgewriter.h"

//----------------------------------------------------------------------------

#include <algorithm>
#include <cassert>
#include <cmath>
#include <iomanip>
#include <locale>
#include <sstream>

//----------------------------------------------------------------------------

#include "csscolor.h"
#include "vrv.h"

//----------------------------------------------------------------------------

namespace vrv {

//----------------------------------------------------------------------------
// Local helpers - number/string formatting (docs/formato/especificacao-v1.md §7)
//----------------------------------------------------------------------------

namespace {

    // At most 6 significant digits, fixed notation (never scientific), "." decimal separator,
    // no trailing zeros, integers without ".0", "-0" normalized to "0". Locale-independent: the
    // stream is explicitly imbued with the classic ("C") locale, so LC_NUMERIC (a comma decimal
    // separator, e.g. tr_TR.UTF-8) never leaks in - this is what S05 acceptance criterion 4
    // (byte-identical export under a comma-locale) actually tests.
    std::string FormatNumber(double value)
    {
        if (!std::isfinite(value)) value = 0.0;
        if (value == 0.0) return "0"; // also normalizes -0.0

        const bool negative = (value < 0.0);
        const double absValue = std::fabs(value);

        // Number of fractional decimals that keeps 6 significant digits in total.
        int exponent = static_cast<int>(std::floor(std::log10(absValue)));
        int decimals = 5 - exponent;
        if (decimals < 0) decimals = 0;
        if (decimals > 12) decimals = 12;

        const double factor = std::pow(10.0, decimals);
        const double rounded = std::round(absValue * factor) / factor;
        if (rounded == 0.0) return "0";

        std::ostringstream oss;
        oss.imbue(std::locale::classic());
        oss << std::fixed << std::setprecision(decimals) << rounded;
        std::string s = oss.str();

        const std::size_t dot = s.find('.');
        if (dot != std::string::npos) {
            std::size_t last = s.find_last_not_of('0');
            if (s[last] == '.') --last;
            s.erase(last + 1);
        }

        return negative ? ("-" + s) : s;
    }

    std::string FormatColor(int color) { return StringFormat("#%06x", color & 0xFFFFFF); }

    // Class names, ids and glyph ids are always plain ASCII, but common text runs (D01) and glyph
    // font names can carry arbitrary UTF-8/control characters (e.g. an embedded newline in a
    // MusicXML credit line), so every control character is escaped, not just '"'/'\\'.
    std::string EscapeJsonString(const std::string &s)
    {
        static const char *const kHex = "0123456789abcdef";

        std::string out;
        out.reserve(s.size());
        for (unsigned char c : s) {
            switch (c) {
                case '"': out += "\\\""; break;
                case '\\': out += "\\\\"; break;
                case '\n': out += "\\n"; break;
                case '\r': out += "\\r"; break;
                case '\t': out += "\\t"; break;
                default:
                    if (c < 0x20) {
                        out += "\\u00";
                        out.push_back(kHex[(c >> 4) & 0xF]);
                        out.push_back(kHex[c & 0xF]);
                    }
                    else {
                        out.push_back(static_cast<char>(c));
                    }
            }
        }
        return out;
    }

    std::string LineCapString(LineCapStyle cap)
    {
        switch (cap) {
            case LINECAP_BUTT: return "butt";
            case LINECAP_ROUND: return "round";
            case LINECAP_SQUARE: return "square";
            case LINECAP_DEFAULT:
            default: return "default";
        }
    }

    std::string LineJoinString(LineJoinStyle join)
    {
        switch (join) {
            case LINEJOIN_ARCS: return "arcs";
            case LINEJOIN_BEVEL: return "bevel";
            case LINEJOIN_MITER: return "miter";
            case LINEJOIN_MITER_CLIP: return "miter-clip";
            case LINEJOIN_ROUND: return "round";
            case LINEJOIN_DEFAULT:
            default: return "default";
        }
    }

    // `none`/`justify` normalize to `left` (§5.4).
    std::string AlignString(data_HORIZONTALALIGNMENT alignment)
    {
        switch (alignment) {
            case HORIZONTALALIGNMENT_center: return "center";
            case HORIZONTALALIGNMENT_right: return "right";
            default: return "left";
        }
    }

} // namespace

//----------------------------------------------------------------------------
// Local helpers - CSS class bold/italic resolution (§6, ported from lottiewriter.cpp)
//----------------------------------------------------------------------------

namespace {

    // Reproduces SvgDeviceContext::Commit's global CSS rule ("g.ending, g.fing, g.reh, g.tempo
    // {font-weight:bold;} g.dir, g.dynam, g.mNum {font-style:italic;} g.label
    // {font-weight:normal;}"), so common-text runs come out with the same effective bold/italic
    // as the SVG even though the format never carries CSS classes to the reader. Cumulative down
    // the tree, matching CSS inheritance: "label" always wins over an ancestor's bold.
    struct TextStyleContext {
        bool bold = false;
        bool italic = false;
    };

    bool HasClassToken(const std::string &classNames, const char *token)
    {
        std::istringstream iss(classNames);
        std::string word;
        while (iss >> word) {
            if (word == token) return true;
        }
        return false;
    }

    TextStyleContext ApplyClassStyleRule(const std::string &classNames, TextStyleContext ctx)
    {
        if (HasClassToken(classNames, "ending") || HasClassToken(classNames, "fing") || HasClassToken(classNames, "reh")
            || HasClassToken(classNames, "tempo")) {
            ctx.bold = true;
        }
        if (HasClassToken(classNames, "dir") || HasClassToken(classNames, "dynam") || HasClassToken(classNames, "mNum")) {
            ctx.italic = true;
        }
        if (HasClassToken(classNames, "label")) {
            ctx.bold = false;
        }
        return ctx;
    }

} // namespace

//----------------------------------------------------------------------------
// Local helpers - page metrics (§3, ported from lottiewriter.cpp ComputePageMetrics)
//----------------------------------------------------------------------------

namespace {

    struct PageMetrics {
        int wpx = 0;
        int hpx = 0;
        int vw = 0;
        int vh = 0;
        double scale = 1.0;
        double tx = 0.0;
        double ty = 0.0;
    };

    // Non-facsimile viewBox only: BridgeDeviceContext/BridgePage carry no facsimile flag yet
    // (SvgDeviceContext::SetFacsimile has no Bridge equivalent), and the test corpus has no
    // facsimile-encoded piece either - see docs/plano/S05-writer-json.md notes.
    PageMetrics ComputePageMetrics(const BridgePage &page)
    {
        PageMetrics metrics;

        if (page.baseWidth && page.baseHeight) {
            metrics.wpx = page.baseWidth;
            metrics.hpx = page.baseHeight;
        }
        else {
            metrics.wpx = static_cast<int>(std::ceil(page.width * page.userScaleX));
            metrics.hpx = static_cast<int>(std::ceil(page.height * page.userScaleY));
        }

        metrics.vw = static_cast<int>(page.width * page.viewBoxFactor);
        metrics.vh = static_cast<int>(page.contentHeight * page.viewBoxFactor);

        const double scaleX = (metrics.vw != 0) ? static_cast<double>(metrics.wpx) / metrics.vw : 1.0;
        const double scaleY = (metrics.vh != 0) ? static_cast<double>(metrics.hpx) / metrics.vh : 1.0;
        metrics.scale = std::min(scaleX, scaleY);

        metrics.tx = (metrics.wpx - metrics.vw * metrics.scale) / 2.0;
        metrics.ty = (metrics.hpx - metrics.vh * metrics.scale) / 2.0;

        return metrics;
    }

} // namespace

//----------------------------------------------------------------------------
// Local helpers - geometry
//----------------------------------------------------------------------------

namespace {

    void AppendFlatVec(std::string &out, const std::vector<BridgeVec> &vecs)
    {
        out += '[';
        for (std::size_t i = 0; i < vecs.size(); ++i) {
            if (i) out += ',';
            out += FormatNumber(vecs[i].x);
            out += ',';
            out += FormatNumber(vecs[i].y);
        }
        out += ']';
    }

    void AppendBezier(std::string &out, const BridgeBezier &bezier)
    {
        out += "{\"closed\":";
        out += bezier.closed ? "true" : "false";
        out += ",\"v\":";
        AppendFlatVec(out, bezier.v);
        out += ",\"i\":";
        AppendFlatVec(out, bezier.i);
        out += ",\"o\":";
        AppendFlatVec(out, bezier.o);
        out += '}';
    }

    void AppendBezierArray(std::string &out, const std::vector<BridgeBezier> &paths)
    {
        out += '[';
        for (std::size_t i = 0; i < paths.size(); ++i) {
            if (i) out += ',';
            AppendBezier(out, paths[i]);
        }
        out += ']';
    }

    // Common style block shared by path/rect/ellipse shapes (§5.2). fillOpacity/strokeOpacity are
    // omitted when 1.0; dash is omitted when there is no dashing; every other field is always
    // written (no "ausente quando" clause for them in the spec).
    void AppendShapeStyle(std::string &out, const BridgeShape &shape)
    {
        if (!shape.hasFill) {
            out += ",\"fill\":\"none\"";
        }
        else if (shape.fillColor != COLOR_NONE) {
            out += ",\"fill\":\"" + FormatColor(shape.fillColor) + "\"";
        }
        if (shape.fillOpacity != 1.0) {
            out += ",\"fillOpacity\":" + FormatNumber(shape.fillOpacity);
        }

        if (!shape.hasStroke) {
            out += ",\"stroke\":\"none\"";
        }
        else if (shape.strokeColor != COLOR_NONE) {
            out += ",\"stroke\":\"" + FormatColor(shape.strokeColor) + "\"";
        }
        out += ",\"strokeWidth\":" + FormatNumber(shape.strokeWidth);
        if (shape.strokeOpacity != 1.0) {
            out += ",\"strokeOpacity\":" + FormatNumber(shape.strokeOpacity);
        }

        out += ",\"lineCap\":\"" + LineCapString(shape.lineCap) + "\"";
        out += ",\"lineJoin\":\"" + LineJoinString(shape.lineJoin) + "\"";

        if (shape.dashLength > 0) {
            out += ",\"dash\":[" + FormatNumber(shape.dashLength) + "," + FormatNumber(shape.gapLength) + "]";
        }
    }

    void AppendShape(std::string &out, const BridgeShape &shape)
    {
        switch (shape.kind) {
            case BridgeShapeKind::Rect: {
                const double x = shape.center.x - shape.size.x / 2.0;
                const double y = shape.center.y - shape.size.y / 2.0;
                out += "{\"t\":\"r\",\"x\":" + FormatNumber(x) + ",\"y\":" + FormatNumber(y)
                    + ",\"w\":" + FormatNumber(shape.size.x) + ",\"h\":" + FormatNumber(shape.size.y)
                    + ",\"rx\":" + FormatNumber(shape.radius);
                AppendShapeStyle(out, shape);
                out += '}';
                break;
            }
            case BridgeShapeKind::Ellipse: {
                out += "{\"t\":\"e\",\"cx\":" + FormatNumber(shape.center.x) + ",\"cy\":" + FormatNumber(shape.center.y)
                    + ",\"rx\":" + FormatNumber(shape.size.x / 2.0) + ",\"ry\":" + FormatNumber(shape.size.y / 2.0);
                AppendShapeStyle(out, shape);
                out += '}';
                break;
            }
            case BridgeShapeKind::Path:
            default: {
                out += "{\"t\":\"p\",\"paths\":";
                AppendBezierArray(out, shape.paths);
                AppendShapeStyle(out, shape);
                out += '}';
                break;
            }
        }
    }

    void AppendGlyphUse(std::string &out, const BridgeGlyphUse &use)
    {
        out += "{\"t\":\"u\",\"g\":\"" + EscapeJsonString(use.glyphId) + "\",\"x\":" + FormatNumber(use.x)
            + ",\"y\":" + FormatNumber(use.y) + ",\"sx\":" + FormatNumber(use.sx) + ",\"sy\":" + FormatNumber(use.sy)
            + '}';
    }

    void AppendTextRun(std::string &out, const BridgeTextRun &run, const TextStyleContext &ctx)
    {
        const bool bold = (run.weight == FONTWEIGHT_bold) || ctx.bold;
        const bool italic
            = (run.style == FONTSTYLE_italic) || (run.style == FONTSTYLE_oblique) || ctx.italic;

        out += "{\"t\":\"t\",\"s\":\"" + EscapeJsonString(UTF32to8(run.text)) + "\"";
        out += ",\"x\":" + FormatNumber(run.origin.x) + ",\"y\":" + FormatNumber(run.origin.y);
        out += ",\"size\":" + FormatNumber(run.pointSize);
        out += ",\"align\":\"" + AlignString(run.alignment) + "\"";
        out += ",\"letterSpacing\":" + FormatNumber(run.letterSpacing);
        out += ",\"bold\":";
        out += bold ? "true" : "false";
        out += ",\"italic\":";
        out += italic ? "true" : "false";
        out += ",\"family\":\"" + EscapeJsonString(run.family) + "\"";
        if (run.color != COLOR_NONE) {
            out += ",\"color\":\"" + FormatColor(run.color) + "\"";
        }
        out += '}';
    }

    void AppendChild(std::string &out, const BridgeChild &child, const TextStyleContext &ctx);

    void AppendNode(std::string &out, const BridgeNode &node, TextStyleContext ctx)
    {
        ctx = ApplyClassStyleRule(node.className, ctx);

        out += "{\"t\":\"g\"";
        if (!node.id.empty()) {
            out += ",\"id\":\"" + EscapeJsonString(node.id) + "\"";
        }
        out += ",\"class\":\"" + EscapeJsonString(node.className) + "\"";
        if (!node.colorCss.empty()) {
            out += ",\"color\":\"" + FormatColor(ResolveColor(node.colorCss, COLOR_BLACK)) + "\"";
        }
        out += ",\"hidden\":";
        out += node.hidden ? "true" : "false";
        if (node.hasRotation) {
            out += ",\"rotate\":{\"angle\":" + FormatNumber(node.rotation) + ",\"origin\":["
                + FormatNumber(node.rotationOrigin.x) + "," + FormatNumber(node.rotationOrigin.y) + "]}";
        }
        if (node.hasBBox) {
            out += ",\"bbox\":[" + FormatNumber(node.bbox[0]) + "," + FormatNumber(node.bbox[1]) + ","
                + FormatNumber(node.bbox[2]) + "," + FormatNumber(node.bbox[3]) + "]";
        }
        out += ",\"children\":[";
        for (std::size_t i = 0; i < node.children.size(); ++i) {
            if (i) out += ',';
            AppendChild(out, node.children[i], ctx);
        }
        out += "]}";
    }

    void AppendChild(std::string &out, const BridgeChild &child, const TextStyleContext &ctx)
    {
        if (child.group) {
            AppendNode(out, *child.group, ctx);
        }
        else if (child.text) {
            AppendTextRun(out, *child.text, ctx);
        }
        else if (child.glyphUse) {
            AppendGlyphUse(out, *child.glyphUse);
        }
        else {
            AppendShape(out, child.shape);
        }
    }

    void AppendPage(std::string &out, const BridgePage &page, int index)
    {
        const PageMetrics metrics = ComputePageMetrics(page);

        out += "{\"index\":" + std::to_string(index);
        out += ",\"width\":" + std::to_string(page.width);
        out += ",\"height\":" + std::to_string(page.height);
        out += ",\"contentHeight\":" + std::to_string(page.contentHeight);
        out += ",\"viewBoxFactor\":" + FormatNumber(page.viewBoxFactor);
        out += ",\"viewBox\":[0,0," + std::to_string(metrics.vw) + "," + std::to_string(metrics.vh) + "]";
        out += ",\"baseWidth\":" + std::to_string(page.baseWidth);
        out += ",\"baseHeight\":" + std::to_string(page.baseHeight);
        out += ",\"userScaleX\":" + FormatNumber(page.userScaleX);
        out += ",\"userScaleY\":" + FormatNumber(page.userScaleY);
        out += ",\"widthPx\":" + std::to_string(metrics.wpx);
        out += ",\"heightPx\":" + std::to_string(metrics.hpx);
        out += ",\"fit\":{\"scale\":" + FormatNumber(metrics.scale) + ",\"tx\":" + FormatNumber(metrics.tx)
            + ",\"ty\":" + FormatNumber(metrics.ty) + "}";
        out += ",\"origin\":[" + std::to_string(page.originX) + "," + std::to_string(page.originY) + "]";
        out += ",\"root\":";
        if (page.root) {
            AppendNode(out, *page.root, TextStyleContext{});
        }
        else {
            out += "null";
        }
        out += "}";
    }

    void AppendGlyphDef(std::string &out, const BridgeGlyphDef &def)
    {
        out += "{\"font\":\"" + EscapeJsonString(def.font) + "\",\"codepoint\":\"" + EscapeJsonString(def.codepoint)
            + "\",\"unitsPerEm\":" + std::to_string(def.unitsPerEm) + ",\"horizAdvX\":" + std::to_string(def.horizAdvX)
            + ",\"bbox\":[" + FormatNumber(def.bbox[0]) + "," + FormatNumber(def.bbox[1]) + ","
            + FormatNumber(def.bbox[2]) + "," + FormatNumber(def.bbox[3]) + "],\"paths\":";
        AppendBezierArray(out, def.paths);
        out += '}';
    }

} // namespace

//----------------------------------------------------------------------------
// BridgeWriter
//----------------------------------------------------------------------------

std::string BridgeWriter::WriteScene(const std::vector<const BridgePage *> &pages)
{
    std::string out;
    out.reserve(1 << 20);
    out += "{\"pages\":[";
    for (std::size_t i = 0; i < pages.size(); ++i) {
        if (i) out += ',';
        assert(pages[i]);
        AppendPage(out, *pages[i], static_cast<int>(i));
    }
    out += "]}";
    return out;
}

std::string BridgeWriter::WriteGlyphs(const std::map<std::string, BridgeGlyphDef> &glyphs)
{
    std::string out;
    out.reserve(1 << 16);
    out += '{';
    bool first = true;
    // std::map<std::string, ...> already iterates in ascending key order, satisfying the "glyph
    // dictionaries are ordered by glyphId" determinism rule for free.
    for (const auto &entry : glyphs) {
        if (!first) out += ',';
        first = false;
        out += '"';
        out += EscapeJsonString(entry.first);
        out += "\":";
        AppendGlyphDef(out, entry.second);
    }
    out += '}';
    return out;
}

std::string BridgeWriter::WriteManifest(const std::string &generator, int pageCount, bool hasTimemap)
{
    std::string out = "{\"format\":\"vsb\",\"version\":1,\"generator\":\"" + EscapeJsonString(generator) + "\"";
    out += ",\"pageCount\":" + std::to_string(pageCount);
    out += ",\"files\":{\"scene\":\"scene.json\",\"glyphs\":\"glyphs.json\"";
    if (hasTimemap) {
        out += ",\"timemap\":\"timemap.json\"";
    }
    out += "}}";
    return out;
}

std::string BridgeWriter::WriteSingleJson(const std::vector<const BridgePage *> &pages,
    const std::map<std::string, BridgeGlyphDef> &glyphs, const std::string &generator, const std::string &timemapJson)
{
    const bool hasTimemap = !timemapJson.empty();

    std::string out;
    out.reserve(1 << 20);
    out += "{\"manifest\":";
    out += WriteManifest(generator, static_cast<int>(pages.size()), hasTimemap);
    out += ",\"glyphs\":";
    out += WriteGlyphs(glyphs);
    out += ",\"scene\":";
    out += WriteScene(pages);
    if (hasTimemap) {
        out += ",\"timemap\":";
        out += timemapJson;
    }
    out += '}';
    return out;
}

} // namespace vrv
