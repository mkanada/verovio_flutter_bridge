/////////////////////////////////////////////////////////////////////////////
// Name:        expansionmap.h
// Author:      Werner Goebl
// Created:     2019
// Copyright (c) Authors and others. All rights reserved.
/////////////////////////////////////////////////////////////////////////////

#ifndef __VRV_EXPANSION_MAP_H__
#define __VRV_EXPANSION_MAP_H__

#include <map>

//----------------------------------------------------------------------------

#include "expansion.h"
#include "options.h"

namespace vrv {

class Ending;
class Score;
class Section;

class ExpansionMap {

public:
    /**
     * @name Constructors, destructors, reset methods
     * Reset method resets all attribute classes
     */
    ///@{
    ExpansionMap();
    virtual ~ExpansionMap();
    ///@}

    /*
     * Clear the content of the expansion map.
     */
    virtual void Reset();

    /**
     * Check if m_expansionMap has been filled
     */
    bool HasExpansionMap();

    /**
     * Expand expansion recursively
     */
    Object *Expand(Expansion *expansion, xsdAnyURI_List &existingList, Object *prevSection,
        xsdAnyURI_List &deletionList, bool deleteList);

    std::vector<std::string> GetExpansionIDsForElement(const std::string &xmlId);

    /**
     * Write the currentexpansionMap to a JSON string
     */
    void ToJson(std::string &output);

    /**
     * Generate an expan for the score analysing the repeats and endings
     */
    void GenerateExpansionFor(Score *score);

    /**
     * @name Setter and getter for the generating attempt flag
     */
    ///@{
    void SetProcessed(bool isProcessed) { m_isProcessed = isProcessed; }
    bool IsProcessed() { return m_isProcessed; }
    ///@}

    //----------------//
    // Static methods //
    //----------------//

    /**
     * @name Methods to check if a measure yields a repeat start or end
     */
    ///@{
    static bool IsRepeatStart(Measure *measure);
    static bool IsRepeatEnd(Measure *measure);
    static bool IsNextRepeatStart(Measure *measure);
    static bool IsPreviousRepeatEnd(Measure *measure);
    ///@}

private:
    bool UpdateIDs(Object *object);

    void GetIDList(Object *object, std::vector<std::string> &idList);

    void GeneratePredictableIDs(Object *source, Object *target);

    /** Ads an id string to an original/notated id */
    bool AddExpandedIDToExpansionMap(const std::string &origXmlId, std::string newXmlId);

    /**
     * Extract the items in [first, last] (measures and/or endings, possibly from different
     * <section> elements once GenerateExpansionFor started reading across section boundaries -
     * E04a) into a new <section>, inserted right before the current position of *first, and
     * return its xml:id. Mirrors what a repeated span becomes: a citable child that Expand() can
     * place once and clone for later passes.
     */
    std::string CreateSection(const ListOfObjects::iterator &first, const ListOfObjects::iterator &last);

    /**
     * Whether any measure directly inside `ending` has a repeat end on its right (E04a): the
     * signal that the ending group is the "casa 1 [, casa 2, ...]" of a repeat, and not just a
     * plain first/second-ending pair played straight through.
     */
    static bool EndingHasRepeatEnd(Ending *ending);

public:
    /** The expansion map indicates which xmlId has been repeated (expanded) elsewhere */
    std::map<std::string, std::vector<std::string>> m_map;

private:
    /** A flag indicating that the generation processed has been run even if the expansion map is empty  */
    bool m_isProcessed;
};

} // namespace vrv

#endif /* expansionmap_h */
