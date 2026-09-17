/////////////////////////////////////////////////////////////////////////////
// Name:        bridgedevicecontext.cpp
// Author:      Verovio Team
// Created:     2026
// Copyright (c) Authors and others. All rights reserved.
/////////////////////////////////////////////////////////////////////////////

#include "bridgedevicecontext.h"

//----------------------------------------------------------------------------

#include <algorithm>
#include <cassert>
#include <cctype>
#include <cmath>
#include <cstdlib>
#include <set>

//----------------------------------------------------------------------------

#include "atts_shared.h"
#include "csscolor.h"
#include "glyph.h"
#include "object.h"
#include "smufl.h"
#include "svgpathparser.h"
#include "vrv.h"

//----------------------------------------------------------------------------

namespace vrv {

//----------------------------------------------------------------------------
// Local helpers
//----------------------------------------------------------------------------

namespace {

    BridgeVec ToVec(int x, int y)
    {
        return BridgeVec{ double(x), double(y) };
    }

    BridgeVec ToVec(const Point &p)
    {
        return ToVec(p.x, p.y);
    }

    BridgeVec Sub(const BridgeVec &a, const BridgeVec &b)
    {
        return BridgeVec{ a.x - b.x, a.y - b.y };
    }

    BridgeVec Scale(const BridgeVec &v, double factor)
    {
        return BridgeVec{ v.x * factor, v.y * factor };
    }

    // A subpath made of straight segments only (no curve tangents).
    BridgeBezier MakeStraightBezier(const std::vector<BridgeVec> &vertices, bool closed)
    {
        BridgeBezier bezier;
        bezier.v = vertices;
        bezier.i.assign(vertices.size(), BridgeVec());
        bezier.o.assign(vertices.size(), BridgeVec());
        bezier.closed = closed;
        return bezier;
    }

    // The SVG output always has a visible outline (global CSS: "stroke:currentColor"), so every
    // shape in the Bridge IR carries an explicit stroke too. Width defaults to 1 (SVG default),
    // color/opacity stay COLOR_NONE / default so they are inherited from the enclosing group.
    void ApplyStrokeFromPen(BridgeShape &shape, const Pen &pen)
    {
        shape.hasStroke = true;
        shape.strokeWidth = (pen.GetWidth() > 0) ? pen.GetWidth() : 1;
        shape.strokeColor = pen.HasColor() ? pen.GetColor() : COLOR_NONE;
        if (pen.HasOpacity()) {
            shape.strokeOpacity = pen.GetOpacity();
        }
        shape.lineCap = pen.GetLineCap();
        shape.lineJoin = pen.GetLineJoin();
    }

    // Only DrawLine, DrawPolyline and DrawPolygon reproduce dashing in SVG (DrawRoundedRectangle
    // and DrawEllipse never call AppendStrokeDashArray there either).
    void ApplyDashFromPen(BridgeShape &shape, const Pen &pen)
    {
        if (pen.GetDashLength() > 0) {
            shape.dashLength = pen.GetDashLength();
            shape.gapLength = (pen.GetGapLength() > 0) ? pen.GetGapLength() : pen.GetDashLength();
        }
    }

    void ApplyFillFromBrush(BridgeShape &shape, const Brush &brush)
    {
        shape.hasFill = true;
        shape.fillColor = brush.HasColor() ? brush.GetColor() : COLOR_NONE;
        if (brush.HasOpacity()) {
            shape.fillOpacity = brush.GetOpacity();
        }
    }

    struct BridgeBBox {
        double x0 = 0.0;
        double y0 = 0.0;
        double x1 = 0.0;
        double y1 = 0.0;
        bool valid = false;
    };

    struct BridgeTransform {
        double a = 1.0;
        double b = 0.0;
        double c = 0.0;
        double d = 1.0;
        double e = 0.0;
        double f = 0.0;

        BridgeVec Apply(const BridgeVec &point) const
        {
            return BridgeVec{ a * point.x + c * point.y + e, b * point.x + d * point.y + f };
        }
    };

    BridgeTransform RotationTransform(const BridgeNode &node)
    {
        if (!node.hasRotation) {
            return {};
        }
        const double radians = node.rotation * std::acos(-1.0) / 180.0;
        const double cosine = std::cos(radians);
        const double sine = std::sin(radians);
        return BridgeTransform{ cosine, sine, -sine, cosine,
            node.rotationOrigin.x - cosine * node.rotationOrigin.x + sine * node.rotationOrigin.y,
            node.rotationOrigin.y - sine * node.rotationOrigin.x - cosine * node.rotationOrigin.y };
    }

    BridgeTransform ComposeTransform(const BridgeTransform &outer, const BridgeTransform &inner)
    {
        return BridgeTransform{ outer.a * inner.a + outer.c * inner.b, outer.b * inner.a + outer.d * inner.b,
            outer.a * inner.c + outer.c * inner.d, outer.b * inner.c + outer.d * inner.d,
            outer.a * inner.e + outer.c * inner.f + outer.e, outer.b * inner.e + outer.d * inner.f + outer.f };
    }

    void UnionBBox(BridgeBBox &target, const BridgeBBox &source)
    {
        if (!source.valid) return;
        if (!target.valid) {
            target = source;
            return;
        }
        target.x0 = std::min(target.x0, source.x0);
        target.y0 = std::min(target.y0, source.y0);
        target.x1 = std::max(target.x1, source.x1);
        target.y1 = std::max(target.y1, source.y1);
    }

    void ExpandBBox(BridgeBBox &bbox, double amount)
    {
        if (!bbox.valid) return;
        bbox.x0 -= amount;
        bbox.y0 -= amount;
        bbox.x1 += amount;
        bbox.y1 += amount;
    }

    void AddPoint(BridgeBBox &bbox, const BridgeVec &point)
    {
        if (!bbox.valid) {
            bbox.x0 = bbox.x1 = point.x;
            bbox.y0 = bbox.y1 = point.y;
            bbox.valid = true;
            return;
        }
        bbox.x0 = std::min(bbox.x0, point.x);
        bbox.y0 = std::min(bbox.y0, point.y);
        bbox.x1 = std::max(bbox.x1, point.x);
        bbox.y1 = std::max(bbox.y1, point.y);
    }

    BridgeBBox ShapeBBox(const BridgeShape &shape)
    {
        if (!shape.hasFill && !shape.hasStroke) {
            return {};
        }

        BridgeBBox bbox;
        if (shape.kind == BridgeShapeKind::Path) {
            for (const BridgeBezier &path : shape.paths) {
                const std::size_t count = std::min(path.v.size(), std::min(path.i.size(), path.o.size()));
                for (std::size_t idx = 0; idx < count; ++idx) {
                    AddPoint(bbox, path.v[idx]);
                    AddPoint(bbox, BridgeVec{ path.v[idx].x + path.i[idx].x, path.v[idx].y + path.i[idx].y });
                    AddPoint(bbox, BridgeVec{ path.v[idx].x + path.o[idx].x, path.v[idx].y + path.o[idx].y });
                }
            }
        }
        else if (shape.kind == BridgeShapeKind::Rect) {
            const double x0 = shape.center.x - shape.size.x / 2.0;
            const double y0 = shape.center.y - shape.size.y / 2.0;
            AddPoint(bbox, BridgeVec{ x0, y0 });
            AddPoint(bbox, BridgeVec{ x0 + shape.size.x, y0 + shape.size.y });
        }
        else {
            const double x0 = shape.center.x - shape.size.x / 2.0;
            const double y0 = shape.center.y - shape.size.y / 2.0;
            AddPoint(bbox, BridgeVec{ x0, y0 });
            AddPoint(bbox, BridgeVec{ x0 + shape.size.x, y0 + shape.size.y });
        }

        if (!bbox.valid || ((bbox.x1 - bbox.x0 <= 0.0) && (bbox.y1 - bbox.y0 <= 0.0) && !shape.hasStroke)) {
            return {};
        }
        if (shape.hasStroke) {
            ExpandBBox(bbox, shape.strokeWidth / 2.0);
        }
        return bbox;
    }

    BridgeBBox GlyphBBox(
        const BridgeGlyphUse &use, const std::map<std::string, BridgeGlyphDef> &glyphs)
    {
        const auto glyphIt = glyphs.find(use.glyphId);
        if (glyphIt == glyphs.end()) {
            return {};
        }
        const int *glyphBBox = glyphIt->second.bbox;
        // use.sx/sy already are the same "translate(x,y) scale(sx,sy)" factors SvgDeviceContext
        // applies to the <use> element (font units -> viewBox units), so no further division by
        // DEFINITION_FACTOR is needed here.
        const double x0 = use.x + glyphBBox[0] * use.sx;
        const double y0 = use.y + glyphBBox[1] * use.sy;
        const double x1 = use.x + (glyphBBox[0] + glyphBBox[2]) * use.sx;
        const double y1 = use.y + (glyphBBox[1] + glyphBBox[3]) * use.sy;
        if ((x1 - x0 <= 0.0) || (y1 - y0 <= 0.0)) {
            return {};
        }
        return BridgeBBox{ std::min(x0, x1), std::min(y0, y1), std::max(x0, x1), std::max(y0, y1), true };
    }

    BridgeBBox TextBBox(const BridgeTextRun &run)
    {
        if (!run.hasBBox) {
            return {};
        }
        return BridgeBBox{ run.bbox[0], run.bbox[1], run.bbox[2], run.bbox[3], true };
    }

    BridgeBBox TransformBBox(const BridgeBBox &source, const BridgeTransform &transform)
    {
        if (!source.valid) {
            return {};
        }
        BridgeBBox transformed;
        const BridgeVec corners[4] = { BridgeVec{ source.x0, source.y0 }, BridgeVec{ source.x1, source.y0 },
            BridgeVec{ source.x0, source.y1 }, BridgeVec{ source.x1, source.y1 } };
        for (const BridgeVec &corner : corners) {
            AddPoint(transformed, transform.Apply(corner));
        }
        return transformed;
    }

    BridgeBBox RotateBBox(const BridgeBBox &source, const BridgeNode &node)
    {
        return TransformBBox(source, RotationTransform(node));
    }

    BridgeBBox CalculateNodeBBox(
        BridgeNode &node, const std::map<std::string, BridgeGlyphDef> &glyphs, const BridgeTransform &toPage)
    {
        if (node.hidden) {
            node.hasBBox = false;
            return {};
        }

        BridgeBBox bbox;
        const BridgeTransform childToPage = ComposeTransform(toPage, RotationTransform(node));
        for (BridgeChild &child : node.children) {
            BridgeBBox childBBox;
            if (child.group != NULL) {
                childBBox = CalculateNodeBBox(*child.group, glyphs, childToPage);
            }
            else if (child.text != std::nullopt) {
                childBBox = TextBBox(*child.text);
            }
            else if (child.glyphUse != std::nullopt) {
                childBBox = GlyphBBox(*child.glyphUse, glyphs);
            }
            else {
                childBBox = ShapeBBox(child.shape);
            }

            childBBox = RotateBBox(childBBox, node);
            UnionBBox(bbox, childBBox);
        }

        node.hasBBox = bbox.valid;
        if (bbox.valid) {
            const BridgeBBox pageBBox = TransformBBox(bbox, toPage);
            node.bbox[0] = pageBBox.x0;
            node.bbox[1] = pageBBox.y0;
            node.bbox[2] = pageBBox.x1;
            node.bbox[3] = pageBBox.y1;
        }
        return bbox;
    }

    void BuildIndex(const BridgeNode &node, int &nodePath, std::vector<BridgeIndexEntry> &index)
    {
        ++nodePath;
        if (!node.id.empty()) {
            BridgeIndexEntry entry;
            entry.id = node.id;
            entry.className = node.className;
            entry.nodePath = nodePath;
            if (node.hasBBox) {
                std::copy(std::begin(node.bbox), std::end(node.bbox), std::begin(entry.bbox));
            }
            index.push_back(std::move(entry));
        }
        for (const BridgeChild &child : node.children) {
            if (child.group != NULL) {
                BuildIndex(*child.group, nodePath, index);
            }
        }
    }

} // namespace

//----------------------------------------------------------------------------
// BridgeDeviceContext
//----------------------------------------------------------------------------

BridgeDeviceContext::BridgeDeviceContext() : DeviceContext(BRIDGE_DEVICE_CONTEXT) {}

BridgeDeviceContext::~BridgeDeviceContext() {}

void BridgeDeviceContext::SetBackground(int color, int style) {}

void BridgeDeviceContext::SetBackgroundImage(void *image, double opacity) {}

void BridgeDeviceContext::SetBackgroundMode(int mode) {}

void BridgeDeviceContext::SetTextForeground(int color) {}

void BridgeDeviceContext::SetTextBackground(int color) {}

void BridgeDeviceContext::SetLogicalOrigin(int x, int y)
{
    m_originX = -x;
    m_originY = -y;
}

Point BridgeDeviceContext::GetLogicalOrigin()
{
    return Point(m_originX, m_originY);
}

void BridgeDeviceContext::DrawQuadBezierPath(Point bezier[3])
{
    assert(!m_penStack.empty());
    const Pen &currentPen = m_penStack.top();

    const BridgeVec p0 = ToVec(bezier[0]);
    const BridgeVec p1 = ToVec(bezier[1]);
    const BridgeVec p2 = ToVec(bezier[2]);

    BridgeBezier path = MakeStraightBezier({ p0, p2 }, false);
    // Degree-elevated to a cubic (C1 = P0 + 2/3(P1-P0), C2 = P2 + 2/3(P1-P2)); as a tangent
    // relative to its vertex, C1-P0 and C2-P2 reduce to 2/3 of P1-P0 and P1-P2.
    path.o[0] = Scale(Sub(p1, p0), 2.0 / 3.0);
    path.i[1] = Scale(Sub(p1, p2), 2.0 / 3.0);

    BridgeShape shape;
    shape.paths.push_back(std::move(path));

    // fill="none" in SVG: no ApplyFillFromBrush call, hasFill stays false.
    ApplyStrokeFromPen(shape, currentPen);
    // linecap/linejoin are fixed to round in SVG, regardless of the pen.
    shape.lineCap = LINECAP_ROUND;
    shape.lineJoin = LINEJOIN_ROUND;
    ApplyDashFromPen(shape, currentPen);

    this->AddShape(std::move(shape));
}

void BridgeDeviceContext::DrawCubicBezierPath(Point bezier[4])
{
    assert(!m_penStack.empty());
    const Pen &currentPen = m_penStack.top();

    const BridgeVec p0 = ToVec(bezier[0]);
    const BridgeVec p1 = ToVec(bezier[1]);
    const BridgeVec p2 = ToVec(bezier[2]);
    const BridgeVec p3 = ToVec(bezier[3]);

    BridgeBezier path = MakeStraightBezier({ p0, p3 }, false);
    path.o[0] = Sub(p1, p0);
    path.i[1] = Sub(p2, p3);

    BridgeShape shape;
    shape.paths.push_back(std::move(path));

    // fill="none" in SVG: no ApplyFillFromBrush call, hasFill stays false.
    ApplyStrokeFromPen(shape, currentPen);
    shape.lineCap = LINECAP_ROUND;
    shape.lineJoin = LINEJOIN_ROUND;
    ApplyDashFromPen(shape, currentPen);

    this->AddShape(std::move(shape));
}

void BridgeDeviceContext::DrawCubicBezierPathFilled(Point bezier1[4], Point bezier2[4])
{
    assert(!m_penStack.empty());
    assert(!m_brushStack.empty());

    const Pen &currentPen = m_penStack.top();
    const Brush &currentBrush = m_brushStack.top();

    const BridgeVec b1_0 = ToVec(bezier1[0]);
    const BridgeVec b1_1 = ToVec(bezier1[1]);
    const BridgeVec b1_2 = ToVec(bezier1[2]);
    const BridgeVec b1_3 = ToVec(bezier1[3]);
    const BridgeVec b2_0 = ToVec(bezier2[0]);
    const BridgeVec b2_1 = ToVec(bezier2[1]);
    const BridgeVec b2_2 = ToVec(bezier2[2]);

    // SVG: M b1[0] C b1[1] b1[2] b1[3] C b2[2] b2[1] b2[0] (no Z; the closing segment
    // b2[0]->b1[0] only exists in Bridge, where every subpath must state c=true explicitly).
    BridgeBezier path = MakeStraightBezier({ b1_0, b1_3, b2_0 }, true);
    path.o[0] = Sub(b1_1, b1_0);
    path.i[1] = Sub(b1_2, b1_3);
    path.o[1] = Sub(b2_2, b1_3);
    path.i[2] = Sub(b2_1, b2_0);
    // i[0] and o[2] stay (0,0): the explicit closing segment in the Bridge IR is straight.

    BridgeShape shape;
    shape.paths.push_back(std::move(path));

    ApplyStrokeFromPen(shape, currentPen);
    shape.lineCap = LINECAP_ROUND;
    shape.lineJoin = LINEJOIN_ROUND;
    ApplyFillFromBrush(shape, currentBrush);

    this->AddShape(std::move(shape));
}

void BridgeDeviceContext::DrawBentParallelogramFilled(Point side[4], int height)
{
    assert(!m_penStack.empty());
    assert(!m_brushStack.empty());

    const Pen &currentPen = m_penStack.top();
    const Brush &currentBrush = m_brushStack.top();

    const BridgeVec s0 = ToVec(side[0]);
    const BridgeVec s1 = ToVec(side[1]);
    const BridgeVec s2 = ToVec(side[2]);
    const BridgeVec s3 = ToVec(side[3]);
    const BridgeVec s0h{ s0.x, s0.y + height };
    const BridgeVec s3h{ s3.x, s3.y + height };

    // SVG: M s0 C s1 s2 s3 L s3+h C (s2+h)(s1+h)(s0+h) Z.
    BridgeBezier path = MakeStraightBezier({ s0, s3, s3h, s0h }, true);
    path.o[0] = Sub(s1, s0);
    path.i[1] = Sub(s2, s3);
    // o[1]/i[2] stay (0,0): s3 -> s3+h is the straight "L" segment.
    path.o[2] = Sub(s2, s3);
    path.i[3] = Sub(s1, s0);
    // o[3]/i[0] stay (0,0): the closing "Z" segment (s0+h -> s0) is straight.

    BridgeShape shape;
    shape.paths.push_back(std::move(path));

    ApplyStrokeFromPen(shape, currentPen);
    shape.lineCap = LINECAP_ROUND;
    shape.lineJoin = LINEJOIN_ROUND;
    ApplyFillFromBrush(shape, currentBrush);

    this->AddShape(std::move(shape));
}

void BridgeDeviceContext::DrawCircle(int x, int y, int radius)
{
    this->DrawEllipse(x - radius, y - radius, 2 * radius, 2 * radius);
}

void BridgeDeviceContext::DrawEllipse(int x, int y, int width, int height)
{
    assert(!m_penStack.empty());
    assert(!m_brushStack.empty());

    const Pen &currentPen = m_penStack.top();
    const Brush &currentBrush = m_brushStack.top();

    // Integer division on purpose: it reproduces the same half-pixel truncation as
    // SvgDeviceContext::DrawEllipse, which also declares rw/rh as int.
    const int rw = width / 2;
    const int rh = height / 2;

    BridgeShape shape;
    shape.kind = BridgeShapeKind::Ellipse;
    shape.center = ToVec(x + rw, y + rh);
    shape.size = ToVec(2 * rw, 2 * rh);

    ApplyStrokeFromPen(shape, currentPen);
    ApplyFillFromBrush(shape, currentBrush);

    this->AddShape(std::move(shape));
}

void BridgeDeviceContext::DrawEllipticArc(int x, int y, int width, int height, double start, double end) {}

void BridgeDeviceContext::DrawLine(int x1, int y1, int x2, int y2)
{
    assert(!m_penStack.empty());
    const Pen &currentPen = m_penStack.top();

    BridgeShape shape;
    shape.paths.push_back(MakeStraightBezier({ ToVec(x1, y1), ToVec(x2, y2) }, false));

    ApplyStrokeFromPen(shape, currentPen);
    ApplyDashFromPen(shape, currentPen);

    this->AddShape(std::move(shape));
}

void BridgeDeviceContext::DrawPolyline(int n, Point points[], bool close)
{
    assert(!m_penStack.empty());
    const Pen &currentPen = m_penStack.top();

    std::vector<BridgeVec> vertices;
    vertices.reserve(n);
    for (int i = 0; i < n; ++i) {
        vertices.push_back(ToVec(points[i]));
    }

    BridgeShape shape;
    // No fill: mirrors SvgDeviceContext::DrawPolyline, which never sets a fill color and only
    // forces fill="none" explicitly when n > 2 (for n <= 2 the enclosed area is zero anyway).
    shape.paths.push_back(MakeStraightBezier(vertices, close));

    ApplyStrokeFromPen(shape, currentPen);
    ApplyDashFromPen(shape, currentPen);

    this->AddShape(std::move(shape));
}

void BridgeDeviceContext::DrawPolygon(int n, Point points[])
{
    assert(!m_penStack.empty());
    assert(!m_brushStack.empty());

    const Pen &currentPen = m_penStack.top();
    const Brush &currentBrush = m_brushStack.top();

    std::vector<BridgeVec> vertices;
    vertices.reserve(n);
    for (int i = 0; i < n; ++i) {
        vertices.push_back(ToVec(points[i]));
    }

    BridgeShape shape;
    shape.paths.push_back(MakeStraightBezier(vertices, true));

    ApplyStrokeFromPen(shape, currentPen);
    ApplyDashFromPen(shape, currentPen);
    ApplyFillFromBrush(shape, currentBrush);

    this->AddShape(std::move(shape));
}

void BridgeDeviceContext::DrawRectangle(int x, int y, int width, int height)
{
    this->DrawRoundedRectangle(x, y, width, height, 0);
}

void BridgeDeviceContext::DrawRotatedText(const std::string &text, int x, int y, double angle) {}

void BridgeDeviceContext::DrawRoundedRectangle(int x, int y, int width, int height, int radius)
{
    assert(!m_penStack.empty());
    assert(!m_brushStack.empty());

    const Pen &currentPen = m_penStack.top();
    const Brush &currentBrush = m_brushStack.top();

    // Negative heights or widths are not allowed in SVG; normalize the same way
    // SvgDeviceContext::DrawRoundedRectangle does.
    if (height < 0) {
        height = -height;
        y -= height;
    }
    if (width < 0) {
        width = -width;
        x -= width;
    }

    BridgeShape shape;
    shape.kind = BridgeShapeKind::Rect;
    // Exact (non-truncated) center: unlike DrawEllipse, the SVG <rect> keeps x/y/width/height
    // untouched, so converting to Bridge's center+size form must not introduce new rounding.
    shape.center = BridgeVec{ x + width / 2.0, y + height / 2.0 };
    shape.size = ToVec(width, height);
    shape.radius = radius;

    ApplyStrokeFromPen(shape, currentPen);
    ApplyFillFromBrush(shape, currentBrush);

    this->AddShape(std::move(shape));
}

BridgeGlyphUse BridgeDeviceContext::MakeGlyphUse(const Glyph *glyph, const FontInfo *font, int x, int y)
{
    assert(glyph);
    assert(font);

    const Resources *resources = this->GetResources();
    std::string fontName = resources ? resources->GetGlyphFontName(
        static_cast<char32_t>(std::strtoul(glyph->GetCodeStr().c_str(), NULL, 16)), glyph) : "";
    if (fontName.empty() && resources) {
        const std::string currentFont = resources->GetCurrentFont();
        const std::string fallbackFont = resources->GetFallbackFont();
        if (font->GetSmuflFont() == SMUFL_FONT_FALLBACK) {
            fontName = fallbackFont;
        }
        else if (!currentFont.empty()) {
            fontName = currentFont;
        }
        else {
            fontName = fallbackFont;
        }
    }
    if (fontName.empty()) {
        fontName = font->GetFaceName();
    }

    std::string codepoint = glyph->GetCodeStr();
    std::transform(codepoint.begin(), codepoint.end(), codepoint.begin(), [](unsigned char c) {
        return static_cast<char>(std::toupper(c));
    });
    const std::string glyphId = fontName + ":" + codepoint;

    auto [glyphIt, inserted] = m_glyphs.try_emplace(glyphId);
    if (inserted) {
        BridgeGlyphDef &glyphDef = glyphIt->second;
        glyphDef.font = fontName;
        glyphDef.codepoint = codepoint;
        glyphDef.unitsPerEm = glyph->GetUnitsPerEm();
        glyphDef.horizAdvX = glyph->GetHorizAdvX();
        int bboxX, bboxY, bboxWidth, bboxHeight;
        glyph->GetBoundingBox(bboxX, bboxY, bboxWidth, bboxHeight);
        glyphDef.bbox[0] = bboxX;
        glyphDef.bbox[1] = bboxY;
        glyphDef.bbox[2] = bboxWidth;
        glyphDef.bbox[3] = bboxHeight;
        ParseGlyphXml(glyph->GetXML(), glyphDef.paths);
    }

    double scaleY = (double)font->GetPointSize() / glyph->GetUnitsPerEm() * DEFINITION_FACTOR;
    double scaleX = scaleY;
    if (font->GetWidthToHeightRatio() != 1.0f) scaleX *= font->GetWidthToHeightRatio();

    return BridgeGlyphUse{ glyphId, double(x), double(y), scaleX, scaleY };
}

int BridgeDeviceContext::GetGlyphAdvance(const Glyph *glyph, const FontInfo *font)
{
    assert(glyph);
    assert(font);

    // Exact same integer arithmetic as SvgDeviceContext::DrawMusicText, to keep advance
    // widths pixel-identical between the two outputs.
    if (glyph->GetHorizAdvX() > 0) {
        return glyph->GetHorizAdvX() * font->GetPointSize() / glyph->GetUnitsPerEm();
    }
    int gx, gy, w, h;
    glyph->GetBoundingBox(gx, gy, w, h);
    return w * font->GetPointSize() / glyph->GetUnitsPerEm();
}

void BridgeDeviceContext::DrawText(
    const std::string &text, const std::u32string &wtext, int x, int y, int width, int height)
{
    assert(!m_fontStack.empty());
    FontInfo *font = m_fontStack.top();

    // Mirrors SvgDeviceContext::DrawText L1163-1166: an explicit x/y without width/height moves
    // the pen without starting a new anchored chunk (e.g. DrawLyricString positioning a
    // syllable). The width/height-only case (invisible sylTextRect) is not visual and is
    // skipped entirely, without moving the pen, exactly like the SVG in that branch.
    const bool hasPosition = (x != 0) && (y != 0) && (x != VRV_UNSET) && (y != VRV_UNSET);
    const bool hasSize = (width != 0) && (height != 0) && (width != VRV_UNSET) && (height != VRV_UNSET);
    if (hasPosition && !hasSize) {
        m_textPenX = x;
        m_textPenY = y;
    }

    std::u32string chars = wtext;
    if (chars.empty() && !text.empty()) {
        chars.assign(text.begin(), text.end());
    }
    if (chars.empty()) return;

    const int letterSpacing = font->GetLetterSpacing();

    if (font->GetSmuflFont() != SMUFL_NONE) {
        const Resources *resources = this->GetResources();
        assert(resources);

        bool first = true;
        for (char32_t c : chars) {
            // Letter-spacing is a per-run CSS property in the SVG (set on the <tspan>), so it
            // is applied between characters of this call only, not carried over from a
            // previous DrawText call in the same chunk.
            if (!first && letterSpacing != 0) {
                m_textPenX += letterSpacing;
                m_textChunkWidth += letterSpacing;
            }
            first = false;

            const Glyph *glyph = resources->GetGlyph(c);
            if (!glyph) continue;

            m_textChunkGlyphUses.push_back(this->MakeGlyphUse(glyph, font, m_textPenX, m_textPenY));

            const int advance = this->GetGlyphAdvance(glyph, font);
            m_textPenX += advance;
            m_textChunkWidth += advance;
        }
    }
    else {
        // Edge case (found in the wild: Clair de Lune's "pp" before "con sordina", MusicXML
        // <words font-family="Leland Text"> literally embedding SMuFL PUA codepoints U+E520
        // twice instead of using a <dynam>): a run reaching here with font->GetSmuflFont() ==
        // SMUFL_NONE (e.g. inside a <dir>, via DrawDirString) can still consist entirely of
        // SMuFL private-use-area codepoints (>= U+E000) that the music font resources DO have
        // an outline for. Liberation Serif has no glyph there, so embedding it in the
        // common-text ty:5 layer below would render nothing. SvgDeviceContext doesn't
        // special-case this either (emits the same raw codepoints with
        // font-family="Times, serif") - `compare svg-to-png` happens to show *something* there
        // anyway only because it also calls fontdb's load_system_fonts(), so resvg's fallback
        // grabs whatever glyph an unrelated, unvendored, environment-specific system font
        // provides at that codepoint (confirmed not one of Leipzig/Bravura/Gootville/Leland,
        // Verovio's own vendored music fonts - all four agree this codepoint is
        // "dynamicPiano"/"p", not the hand-pointing icon `compare`'s reference PNG happened to
        // show on this machine); not reproducible, and no such fallback chain exists here
        // anyway. Draw the whole run as vector glyphs instead of silently dropping it, using
        // the exact same mechanism as the SMuFL branch above - consistent with what Verovio's
        // own glyph data says the codepoints mean, even where that no longer matches a
        // `compare` reference PNG that was itself never a reliable target for this specific
        // codepoint. The `c >= SMUFL_STARTING_CHAR (0xE000)` guard keeps this from ever
        // touching a run of plain spaces (Leipzig's glyph table happens to define U+0020, for
        // spacing between music symbols) or the literal flat/natural/sharp signs (U+266D-F,
        // also in that table) - only genuine, otherwise-unrenderable PUA codepoints qualify.
        const Resources *resources = this->GetResources();
        assert(resources);
        bool allGlyphsAvailable = !chars.empty();
        for (char32_t c : chars) {
            if (c < SMUFL_E000_brace || !resources->GetGlyph(c)) {
                allGlyphsAvailable = false;
                break;
            }
        }

        if (allGlyphsAvailable) {
            bool first = true;
            for (char32_t c : chars) {
                if (!first && letterSpacing != 0) {
                    m_textPenX += letterSpacing;
                    m_textChunkWidth += letterSpacing;
                }
                first = false;

                const Glyph *glyph = resources->GetGlyph(c);
                m_textChunkGlyphUses.push_back(this->MakeGlyphUse(glyph, font, m_textPenX, m_textPenY));

                const int advance = this->GetGlyphAdvance(glyph, font);
                m_textPenX += advance;
                m_textChunkWidth += advance;
            }
            return;
        }

        // Common (non-SMuFL) text: D01 (docs/plano/D01-texto-comum.md) - kept as a native
        // text run instead of a shape, so it needs only the anchor/alignment/font metadata,
        // not glyph outlines.
        assert(!m_brushStack.empty());
        const Brush &currentBrush = m_brushStack.top();

        BridgeTextRun run;
        run.text = chars;
        run.origin = Point(m_textPenX, m_textPenY);
        run.alignment = m_textAlignment;
        run.pointSize = font->GetPointSize();
        run.letterSpacing = letterSpacing;
        run.style = font->GetStyle();
        run.weight = font->GetWeight();
        run.color = currentBrush.HasColor() ? currentBrush.GetColor() : COLOR_NONE;

        TextExtend extend;
        this->GetTextExtent(chars, &extend, true);
        double x0 = run.origin.x;
        if (run.alignment == HORIZONTALALIGNMENT_center) {
            x0 -= extend.m_width / 2.0;
        }
        else if (run.alignment == HORIZONTALALIGNMENT_right) {
            x0 -= extend.m_width;
        }
        const double y0 = run.origin.y - extend.m_ascent;
        const double y1 = run.origin.y + extend.m_descent;
        const double x1 = x0 + extend.m_width;
        if ((extend.m_width > 0.0) && (y1 > y0)) {
            run.hasBBox = true;
            run.bbox[0] = x0;
            run.bbox[1] = y0;
            run.bbox[2] = x1;
            run.bbox[3] = y1;
        }
        this->AddTextRun(std::move(run));

        m_textPenX += extend.m_width;
        m_textChunkWidth += extend.m_width;
    }
}

void BridgeDeviceContext::DrawMusicText(const std::u32string &text, int x, int y, bool setSmuflGlyph)
{
    assert(!m_fontStack.empty());
    FontInfo *font = m_fontStack.top();

    const Resources *resources = this->GetResources();
    assert(resources);

    for (char32_t c : text) {
        const Glyph *glyph = resources->GetGlyph(c);
        if (!glyph) {
            continue;
        }

        this->AddGlyphUse(this->MakeGlyphUse(glyph, font, x, y));
        x += this->GetGlyphAdvance(glyph, font);
    }
}

void BridgeDeviceContext::DrawSpline(int n, Point points[]) {}

void BridgeDeviceContext::DrawGraphicUri(int x, int y, int width, int height, const std::string &uri) {}

namespace {

    // Returns the CSS value of `property` for an embedded <svg> element: an inline "style"
    // declaration takes precedence over the same-named presentation attribute, matching the CSS
    // cascade. Returns an empty string if neither specifies it (distinct from an explicit "none").
    std::string GetSvgProperty(const pugi::xml_node &node, const std::string &property)
    {
        pugi::xml_attribute style = node.attribute("style");
        if (style) {
            const std::string styleValue = style.value();
            std::size_t pos = 0;
            while (pos < styleValue.size()) {
                const std::size_t sep = styleValue.find(';', pos);
                const std::size_t declEnd = (sep == std::string::npos) ? styleValue.size() : sep;
                const std::size_t colon = styleValue.find(':', pos);
                if ((colon != std::string::npos) && (colon < declEnd)) {
                    std::string key = styleValue.substr(pos, colon - pos);
                    std::string value = styleValue.substr(colon + 1, declEnd - colon - 1);
                    auto trim = [](std::string &s) {
                        const std::size_t b = s.find_first_not_of(" \t\r\n");
                        const std::size_t e = s.find_last_not_of(" \t\r\n");
                        s = (b == std::string::npos) ? "" : s.substr(b, e - b + 1);
                    };
                    trim(key);
                    trim(value);
                    if (key == property) return value;
                }
                if (sep == std::string::npos) break;
                pos = sep + 1;
            }
        }

        pugi::xml_attribute attr = node.attribute(property.c_str());
        return attr ? attr.value() : "";
    }

    // Collects the <path> descendants of an embedded <svg> element, transparently descending
    // through bare <g> wrappers (no "transform" of their own) - the real-world shape of
    // data/footer.svg (the "MEI engraved with Verovio" logo that Doc::GenerateFooter() inserts
    // on every page), whose <path>s sit one <g> deep. MVP scope stops there: a <g transform=...>
    // and any element other than <path>/<g> is warned about once per tag and skipped, degrading
    // gracefully instead of aborting the page (same posture as A06/A10).
    void CollectSvgPaths(const pugi::xml_node &node, std::vector<pugi::xml_node> &paths)
    {
        static std::set<std::string> warnedElements;
        for (pugi::xml_node child : node.children()) {
            const std::string tag = child.name();
            if (tag == "path") {
                paths.push_back(child);
            }
            else if (tag == "g") {
                if (child.attribute("transform")) {
                    if (warnedElements.insert("g[transform]").second) {
                        LogWarning("BridgeDeviceContext::DrawSvgShape: embedded <svg>'s <g transform=\"...\"> is "
                                   "not supported, skipping its content.");
                    }
                    continue;
                }
                CollectSvgPaths(child, paths);
            }
            else if (warnedElements.insert(tag).second) {
                LogWarning(
                    "BridgeDeviceContext::DrawSvgShape: unsupported embedded <svg> element '<%s>' ignored.",
                    tag.c_str());
            }
        }
    }

} // namespace

void BridgeDeviceContext::DrawSvgShape(int x, int y, int width, int height, double scale, pugi::xml_node svg)
{
    std::vector<pugi::xml_node> pathNodes;
    CollectSvgPaths(svg, pathNodes);

    const double factor = scale * DEFINITION_FACTOR;

    for (const pugi::xml_node &pathNode : pathNodes) {
        pugi::xml_attribute dAttr = pathNode.attribute("d");
        if (!dAttr) {
            LogWarning("BridgeDeviceContext::DrawSvgShape: <path> without a 'd' attribute ignored.");
            continue;
        }

        std::vector<BridgeBezier> parsedPaths;
        if (!ParseSvgPathData(dAttr.value(), parsedPaths)) {
            continue;
        }

        BridgeShape shape;
        shape.kind = BridgeShapeKind::Path;
        shape.paths.reserve(parsedPaths.size());
        for (const BridgeBezier &srcPath : parsedPaths) {
            BridgeBezier path;
            path.closed = srcPath.closed;
            const std::size_t count = srcPath.v.size();
            path.v.reserve(count);
            path.i.reserve(count);
            path.o.reserve(count);
            for (std::size_t idx = 0; idx < count; ++idx) {
                path.v.push_back(BridgeVec{ x + factor * srcPath.v[idx].x, y + factor * srcPath.v[idx].y });
                path.i.push_back(BridgeVec{ factor * srcPath.i[idx].x, factor * srcPath.i[idx].y });
                path.o.push_back(BridgeVec{ factor * srcPath.o[idx].x, factor * srcPath.o[idx].y });
            }
            shape.paths.push_back(std::move(path));
        }

        // Fill: no global CSS rule targets "fill" in Verovio's stylesheet (SvgDeviceContext's
        // "#<id> path {stroke:currentColor}", see below, only ever sets stroke), so the path's
        // own attribute/style value - explicit, absent, or "none" - is respected as written.
        const std::string fillProperty = GetSvgProperty(pathNode, "fill");
        shape.hasFill = (fillProperty != "none");
        if (shape.hasFill) {
            shape.fillColor = ResolveColor(fillProperty, COLOR_NONE);
        }

        // Stroke: confirmed empirically against the real SVG output (a standalone resvg
        // cascade test, and the corpus footer) that Verovio's global "path {stroke:currentColor}"
        // rule always overrides a <path>'s own "stroke" attribute or style, even an explicit
        // "stroke: none" - CSS presentation attributes never outrank an author stylesheet rule,
        // however low its specificity. So every embedded <path> ends up stroked with the
        // inherited color regardless of what it says, exactly like every other primitive in the
        // exporter (ApplyStrokeFromPen above) - only "stroke-width" still comes from the
        // attribute, since no stylesheet rule sets that property.
        shape.hasStroke = true;
        pugi::xml_attribute strokeWidthAttr = pathNode.attribute("stroke-width");
        shape.strokeWidth = (strokeWidthAttr ? strokeWidthAttr.as_double(1.0) : 1.0) * factor;

        this->AddShape(std::move(shape));
    }
}

void BridgeDeviceContext::DrawBackgroundImage(int x, int y) {}

void BridgeDeviceContext::StartText(int x, int y, data_HORIZONTALALIGNMENT alignment)
{
    m_textPenX = x;
    m_textPenY = y;
    m_textAlignment = alignment;
    m_textChunkGlyphUses.clear();
    m_textChunkWidth = 0.0;
}

void BridgeDeviceContext::EndText()
{
    this->FinalizeTextChunk();
}

void BridgeDeviceContext::MoveTextTo(int x, int y, data_HORIZONTALALIGNMENT alignment)
{
    // In the SVG, an absolute x/y starts a new anchored text chunk (finalize the pending one
    // before moving the pen). An HORIZONTALALIGNMENT_NONE here (e.g. explicit repositioning
    // after an <lb/>) means the SVG only sets x/y and keeps the current text-anchor, so keep
    // the current alignment rather than resetting it.
    this->FinalizeTextChunk();
    m_textPenX = x;
    m_textPenY = y;
    if (alignment != HORIZONTALALIGNMENT_NONE) {
        m_textAlignment = alignment;
    }
}

void BridgeDeviceContext::MoveTextVerticallyTo(int y)
{
    m_textPenY = y;
}

void BridgeDeviceContext::FinalizeTextChunk()
{
    if (m_textChunkGlyphUses.empty()) {
        m_textChunkWidth = 0.0;
        return;
    }

    double offset = 0.0;
    if (m_textAlignment == HORIZONTALALIGNMENT_center) {
        offset = -m_textChunkWidth / 2.0;
    }
    else if (m_textAlignment == HORIZONTALALIGNMENT_right) {
        offset = -m_textChunkWidth;
    }

    for (BridgeGlyphUse &use : m_textChunkGlyphUses) {
        use.x += offset;
        this->AddGlyphUse(std::move(use));
    }

    m_textChunkGlyphUses.clear();
    m_textChunkWidth = 0.0;
}

void BridgeDeviceContext::StartGraphic(
    Object *object, const std::string &gClass, const std::string &gId, GraphicID graphicID, bool prepend)
{
    assert(!m_nodeStack.empty());

    std::unique_ptr<BridgeNode> node = std::make_unique<BridgeNode>();
    node->id = (graphicID == PRIMARY) ? gId : "";
    node->className = object->GetClassName();
    if (!gClass.empty()) {
        node->className.append(" " + gClass);
    }

    if (object->HasAttClass(ATT_COLOR)) {
        AttColor *att = dynamic_cast<AttColor *>(object);
        assert(att);
        if (att->HasColor()) {
            node->colorCss = att->GetColor();
        }
    }

    if (object->HasAttClass(ATT_VISIBILITY)) {
        AttVisibility *att = dynamic_cast<AttVisibility *>(object);
        assert(att);
        if (att->HasVisible() && (att->GetVisible() == BOOLEAN_false)) {
            node->hidden = true;
        }
    }

    BridgeNode *current = m_nodeStack.back();
    BridgeNode *added = node.get();

    BridgeChild child;
    child.group = std::move(node);

    if (prepend) {
        current->children.insert(current->children.begin(), std::move(child));
    }
    else {
        current->children.push_back(std::move(child));
    }

    m_nodeStack.push_back(added);

    if (!added->id.empty()) {
        m_idMap[added->id] = added;
    }
}

void BridgeDeviceContext::EndGraphic(Object *object, View *view)
{
    assert(m_nodeStack.size() > 1);
    BridgeNode *node = m_nodeStack.back();
    m_nodeStack.pop_back();
    CalculateNodeBBox(*node, m_glyphs, {});
}

void BridgeDeviceContext::StartCustomGraphic(const std::string &name, std::string gClass, std::string gId)
{
    assert(!m_nodeStack.empty());

    std::unique_ptr<BridgeNode> node = std::make_unique<BridgeNode>();
    node->id = gId;
    node->className = name;
    if (!gClass.empty()) {
        node->className.append(" " + gClass);
    }

    BridgeNode *current = m_nodeStack.back();
    BridgeNode *added = node.get();

    BridgeChild child;
    child.group = std::move(node);
    current->children.push_back(std::move(child));

    m_nodeStack.push_back(added);

    if (!added->id.empty()) {
        m_idMap[added->id] = added;
    }
}

void BridgeDeviceContext::EndCustomGraphic()
{
    assert(m_nodeStack.size() > 1);
    BridgeNode *node = m_nodeStack.back();
    m_nodeStack.pop_back();
    CalculateNodeBBox(*node, m_glyphs, {});
}

void BridgeDeviceContext::SetCustomGraphicColor(const std::string &color)
{
    assert(!m_nodeStack.empty());
    m_nodeStack.back()->colorCss = color;
}

void BridgeDeviceContext::ResumeGraphic(Object *object, std::string gId)
{
    assert(!m_nodeStack.empty());

    std::map<std::string, BridgeNode *>::iterator it = m_idMap.find(gId);
    if (it != m_idMap.end()) {
        m_nodeStack.push_back(it->second);
    }
    else {
        m_nodeStack.push_back(m_nodeStack.back());
    }
}

void BridgeDeviceContext::EndResumedGraphic(Object *object, View *view)
{
    assert(m_nodeStack.size() > 1);
    BridgeNode *node = m_nodeStack.back();
    m_nodeStack.pop_back();
    CalculateNodeBBox(*node, m_glyphs, {});
}

void BridgeDeviceContext::RotateGraphic(Point const &orig, double angle)
{
    assert(!m_nodeStack.empty());

    BridgeNode *node = m_nodeStack.back();
    if (node->hasRotation) {
        return;
    }
    node->hasRotation = true;
    node->rotation = angle;
    node->rotationOrigin = orig;
}

void BridgeDeviceContext::StartPage()
{
    BridgePage page;
    page.root = std::make_unique<BridgeNode>();
    page.width = this->GetWidth();
    page.height = this->GetHeight();
    page.contentHeight = this->GetContentHeight();
    std::pair<int, int> baseSize = this->GetBaseSize();
    page.baseWidth = baseSize.first;
    page.baseHeight = baseSize.second;
    page.userScaleX = this->GetUserScaleX();
    page.userScaleY = this->GetUserScaleY();
    page.viewBoxFactor = this->GetViewBoxFactor();
    page.originX = m_originX;
    page.originY = m_originY;

    m_pages.push_back(std::move(page));
    m_idMap.clear();
    m_nodeStack.clear();
    m_nodeStack.push_back(m_pages.back().root.get());
}

void BridgeDeviceContext::EndPage()
{
    assert(m_nodeStack.size() == 1);
    BridgePage &page = m_pages.back();
    CalculateNodeBBox(*page.root, m_glyphs, {});
    int nodePath = -1;
    BuildIndex(*page.root, nodePath, page.index);
    m_nodeStack.clear();
}

void BridgeDeviceContext::AddGlyphUse(BridgeGlyphUse &&use)
{
    assert(!m_nodeStack.empty());

    BridgeNode *node = m_nodeStack.back();

    std::vector<BridgeChild>::iterator firstGroup = std::find_if(node->children.begin(), node->children.end(),
        [](const BridgeChild &child) { return (child.group != NULL); });

    BridgeChild child;
    child.glyphUse = std::move(use);

    if (firstGroup != node->children.end()) {
        node->children.insert(firstGroup, std::move(child));
    }
    else if (m_pushBack) {
        node->children.insert(node->children.begin(), std::move(child));
    }
    else {
        node->children.push_back(std::move(child));
    }
}

void BridgeDeviceContext::AddShape(BridgeShape &&shape)
{
    assert(!m_nodeStack.empty());

    BridgeNode *node = m_nodeStack.back();

    std::vector<BridgeChild>::iterator firstGroup = std::find_if(node->children.begin(), node->children.end(),
        [](const BridgeChild &child) { return (child.group != NULL); });

    BridgeChild child;
    child.shape = std::move(shape);

    if (firstGroup != node->children.end()) {
        node->children.insert(firstGroup, std::move(child));
    }
    else if (m_pushBack) {
        node->children.insert(node->children.begin(), std::move(child));
    }
    else {
        node->children.push_back(std::move(child));
    }
}

void BridgeDeviceContext::AddTextRun(BridgeTextRun &&run)
{
    assert(!m_nodeStack.empty());

    BridgeChild child;
    child.text = std::move(run);
    m_nodeStack.back()->children.push_back(std::move(child));
}

} // namespace vrv
