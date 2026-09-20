/////////////////////////////////////////////////////////////////////////////
// Name:        bridgedevicecontext.h
// Author:      Verovio Team
// Created:     2026
// Copyright (c) Authors and others. All rights reserved.
/////////////////////////////////////////////////////////////////////////////

#ifndef __VRV_BRIDGE_DC_H__
#define __VRV_BRIDGE_DC_H__

#include <map>
#include <vector>

//----------------------------------------------------------------------------

#include "devicecontext.h"
#include "bridgegeometry.h"

namespace vrv {

//----------------------------------------------------------------------------
// BridgeDeviceContext
//----------------------------------------------------------------------------

/**
 * This class implements a drawing context for generating the intermediate scene.
 * It is fed by the same View used for drawing SVG in order to guarantee
 * visual parity with the SVG output.
 */
class BridgeDeviceContext : public DeviceContext {
public:
    /**
     * @name Constructors, destructors, and other standard methods
     */
    ///@{
    BridgeDeviceContext();
    virtual ~BridgeDeviceContext();
    ///@}

    /**
     * @name Setters
     */
    ///@{
    void SetBackground(int color, int style = PEN_SOLID) override;
    void SetBackgroundImage(void *image, double opacity = 1.0) override;
    void SetBackgroundMode(int mode) override;
    void SetTextForeground(int color) override;
    void SetTextBackground(int color) override;
    void SetLogicalOrigin(int x, int y) override;
    ///@}

    /**
     * @name Getters
     */
    ///@{
    Point GetLogicalOrigin() override;
    ///@}

    /**
     * @name Drawing methods
     */
    ///@{
    void DrawQuadBezierPath(Point bezier[3]) override;
    void DrawCubicBezierPath(Point bezier[4]) override;
    void DrawCubicBezierPathFilled(Point bezier1[4], Point bezier2[4]) override;
    void DrawBentParallelogramFilled(Point side[4], int height) override;
    void DrawCircle(int x, int y, int radius) override;
    void DrawEllipse(int x, int y, int width, int height) override;
    void DrawEllipticArc(int x, int y, int width, int height, double start, double end) override;
    void DrawLine(int x1, int y1, int x2, int y2) override;
    void DrawPolyline(int n, Point points[], bool close = false) override;
    void DrawPolygon(int n, Point points[]) override;
    void DrawRectangle(int x, int y, int width, int height) override;
    void DrawRotatedText(const std::string &text, int x, int y, double angle) override;
    void DrawRoundedRectangle(int x, int y, int width, int height, int radius) override;
    void DrawText(const std::string &text, const std::u32string &wtext = U"", int x = VRV_UNSET, int y = VRV_UNSET,
        int width = VRV_UNSET, int height = VRV_UNSET) override;
    void DrawMusicText(const std::u32string &text, int x, int y, bool setSmuflGlyph = false) override;
    void DrawSpline(int n, Point points[]) override;
    void DrawGraphicUri(int x, int y, int width, int height, const std::string &uri) override;
    void DrawSvgShape(int x, int y, int width, int height, double scale, pugi::xml_node svg) override;
    void DrawBackgroundImage(int x = 0, int y = 0) override;
    ///@}

    /**
     * @name Method for starting and ending a text
     */
    ///@{
    void StartText(int x, int y, data_HORIZONTALALIGNMENT alignment = HORIZONTALALIGNMENT_left) override;
    void EndText() override;

    /**
     * @name Move a text to the specified position, for example when starting a new line.
     */
    ///@{
    void MoveTextTo(int x, int y, data_HORIZONTALALIGNMENT alignment) override;
    void MoveTextVerticallyTo(int y) override;
    ///@}

    /**
     * Indicate if offset should be applied
     */
    bool ApplyOffset() override { return true; }

    /**
     * @name Method for starting and ending a graphic
     */
    ///@{
    void StartGraphic(Object *object, const std::string &gClass, const std::string &gId, GraphicID graphicID = PRIMARY,
        bool prepend = false) override;
    void EndGraphic(Object *object, View *view) override;
    ///@}

    /**
     * @name Method for starting and ending a graphic custom graphic that do not correspond to an Object
     */
    ///@{
    void StartCustomGraphic(const std::string &name, std::string gClass = "", std::string gId = "") override;
    void EndCustomGraphic() override;
    ///@}

    /**
     * Method for changing the color of a custom graphic
     */
    void SetCustomGraphicColor(const std::string &color) override;

    /**
     * @name Methods for re-starting and ending a graphic for objects drawn in separate steps
     */
    ///@{
    void ResumeGraphic(Object *object, std::string gId) override;
    void EndResumedGraphic(Object *object, View *view) override;
    ///@}

    /**
     * @name Method for rotating a graphic (clockwise).
     */
    ///@{
    void RotateGraphic(Point const &orig, double angle) override;
    ///@}

    /**
     * @name Method for starting and ending page
     */
    ///@{
    void StartPage() override;
    void EndPage() override;
    ///@}

    /**
     * Accessor to the pages built during drawing
     */
    const std::vector<BridgePage> &GetPages() const { return m_pages; }
    const std::map<std::string, BridgeGlyphDef> &GetGlyphs() const { return m_glyphs; }

public:
    //
private:
    /**
     * Insert a glyph use into the current node, preserving the same paint-order rules as shapes.
     */
    void AddGlyphUse(BridgeGlyphUse &&use);

    /**
     * Insert a shape into the current node, replicating SvgDeviceContext::AddChild:
     * before the first child that is a subgroup, otherwise at the front (m_pushBack)
     * or at the back.
     */
    void AddShape(BridgeShape &&shape);

    /**
     * Insert a common text run into the current node, mirroring AddShape (D01, see
     * docs/plano/D01-texto-comum.md) - simple append, since text runs are serialized as
     * independent Bridge scene children and do not participate in the shapes paint-order search.
     */
    void AddTextRun(BridgeTextRun &&run);

    /**
     * Build a glyph use for one glyph, positioned at (x, y) and scaled per the current font,
     * while registering its outline once in the glyph dictionary.
     */
    BridgeGlyphUse MakeGlyphUse(const Glyph *glyph, const FontInfo *font, int x, int y);

    /**
     * Horizontal advance for one glyph, replicating the exact integer arithmetic of
     * SvgDeviceContext::DrawMusicText so glyph spacing stays pixel-identical to the SVG.
     */
    int GetGlyphAdvance(const Glyph *glyph, const FontInfo *font);

    /**
     * Apply the pending text chunk's alignment offset (0 / -width/2 / -width) and insert its
     * pending SMuFL glyph uses and common-text runs into the current node. A chunk made of a
     * single common-text run and no glyph uses is the exception: it is left for the renderer to
     * align against its own font-shaping measurement (see the comment in the .cpp).
     */
    void FinalizeTextChunk();

private:
    int m_originX = 0;
    int m_originY = 0;

    std::vector<BridgePage> m_pages;
    std::vector<BridgeNode *> m_nodeStack;
    std::map<std::string, BridgeNode *> m_idMap;

    /**
     * Cache of parsed glyph outlines (in glyph units), keyed by the exported glyph id.
     */
    std::map<std::string, BridgeGlyphDef> m_glyphs;

    /**
     * State for the text chunk model described in docs/plano/A10-texto-smufl.md: the pen
     * position, the alignment of the current anchored chunk, its accumulated width across every
     * DrawText call in the chunk - whether it produced SMuFL glyph uses or a common-text run
     * (for the alignment offset applied on finalization), and the chunk's pending pieces of
     * both kinds. A chunk can mix the two (or hold several common-text runs, e.g. the
     * autogenerated page number "– N –") exactly like a multi-<tspan> SVG text-anchor chunk.
     */
    int m_textPenX = 0;
    int m_textPenY = 0;
    data_HORIZONTALALIGNMENT m_textAlignment = HORIZONTALALIGNMENT_left;
    double m_textChunkWidth = 0.0;
    std::vector<BridgeGlyphUse> m_textChunkGlyphUses;
    std::vector<BridgeTextRun> m_textChunkTextRuns;
};

} // namespace vrv

#endif // __VRV_BRIDGE_DC_H__
