/////////////////////////////////////////////////////////////////////////////
// Name:        harm.h
// Author:      Laurent Pugin
// Created:     2016
// Copyright (c) Authors and others. All rights reserved.
/////////////////////////////////////////////////////////////////////////////

#ifndef __VRV_HARM_H__
#define __VRV_HARM_H__

#include <memory>
#include <string>
#include <utility>
#include <vector>

#include "controlelement.h"
#include "textdirinterface.h"
#include "timeinterface.h"
#include "transposition.h"

namespace vrv {

class TextElement;

//----------------------------------------------------------------------------
// HarmData
//----------------------------------------------------------------------------

// One <degree> of a MusicXML <harmony>. `type` is "add", "alter" or "subtract".
struct HarmDegree {
    int value = 0;
    int alter = 0;
    std::string type;
};

// The structure of a MusicXML <harmony> (D-MUSICA-CIFRA, docs/plano/M00-dados-musicais-para-o-aprendizado.md).
// Only MusicXmlInput::ReadMusicXmlHarmony sets it; the drawn text does not read it, so the MEI export does
// not change. "" means absent (for the strings) and 0 means absent (for the alterations).
struct HarmData {
    std::string root; // root-step
    int rootAlter = 0; // root-alter, in semitones
    std::string kind; // text of <kind>
    std::string kindText; // kind/@text
    std::string bass; // bass-step
    int bassAlter = 0; // bass-alter
    std::vector<HarmDegree> degrees;
    std::string numeralRoot; // numeral-root (its @text, if any, else its text); only when there is no root
    int numeralAlter = 0; // numeral-alter
};

//----------------------------------------------------------------------------
// Harm (harmony)
//----------------------------------------------------------------------------

/**
 * This class models the MEI <harm> element.
 */
class Harm : public ControlElement,
             public TextListInterface,
             public TextDirInterface,
             public TimeSpanningInterface,
             public AttLang,
             public AttNNumberLike {
public:
    /**
     * @name Constructors, destructors, and other standard methods
     * Reset method reset all attribute classes
     */
    ///@{
    Harm();
    virtual ~Harm();
    Object *Clone() const override { return new Harm(*this); }
    void Reset() override;
    std::string GetClassName() const override { return "harm"; }
    ///@}

    /**
     * @name Getter to interfaces
     */
    ///@{
    TextDirInterface *GetTextDirInterface() override { return vrv_cast<TextDirInterface *>(this); }
    const TextDirInterface *GetTextDirInterface() const override { return vrv_cast<const TextDirInterface *>(this); }
    TimePointInterface *GetTimePointInterface() override { return vrv_cast<TimePointInterface *>(this); }
    const TimePointInterface *GetTimePointInterface() const override
    {
        return vrv_cast<const TimePointInterface *>(this);
    }
    TimeSpanningInterface *GetTimeSpanningInterface() override { return vrv_cast<TimeSpanningInterface *>(this); }
    const TimeSpanningInterface *GetTimeSpanningInterface() const override
    {
        return vrv_cast<const TimeSpanningInterface *>(this);
    }
    ///@}

    /**
     * Add an element (text, rend. etc.) to a harm.
     * Only supported elements will be actually added to the child list.
     */
    bool IsSupportedChild(ClassId classId) override;

    /**
     * Transposition related. The int tracks where we have iterated through the string.
     */
    bool GetRootPitch(TransPitch &pitch, unsigned int &pos) const;
    void SetRootPitch(const TransPitch &pitch, unsigned int endPos);
    bool GetBassPitch(TransPitch &pitch) const;
    void SetBassPitch(const TransPitch &pitch);

    /**
     * The MusicXML structure of the harmony, or NULL (a MEI harm, or a figured bass line).
     * Shared between copies: Clone() is a shallow copy.
     */
    const HarmData *GetHarmData() const { return m_harmData.get(); }
    void SetHarmData(std::shared_ptr<const HarmData> harmData) { m_harmData = std::move(harmData); }

    //----------//
    // Functors //
    //----------//

    /**
     * Interface for class functor visitation
     */
    ///@{
    FunctorCode Accept(Functor &functor) override;
    FunctorCode Accept(ConstFunctor &functor) const override;
    FunctorCode AcceptEnd(Functor &functor) override;
    FunctorCode AcceptEnd(ConstFunctor &functor) const override;
    ///@}

protected:
    //
private:
    //
public:
    //
private:
    std::shared_ptr<const HarmData> m_harmData;
};

} // namespace vrv

#endif
