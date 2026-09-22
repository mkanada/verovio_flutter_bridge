/////////////////////////////////////////////////////////////////////////////
// Name:        bridgealternates.h
// Author:      Verovio Team
// Created:     2026
// Copyright (c) Authors and others. All rights reserved.
/////////////////////////////////////////////////////////////////////////////

#ifndef __VRV_BRIDGE_ALTERNATES_H__
#define __VRV_BRIDGE_ALTERNATES_H__

#include <map>
#include <set>
#include <string>
#include <vector>

namespace vrv {

//----------------------------------------------------------------------------
// BridgeAlternates
//----------------------------------------------------------------------------

/**
 * Pure, Doc-independent computation of the repeat arrival points that need an alternate page
 * sequence (docs/formato/especificacao-v1.md §2.5, the normative existence rule written in P02a).
 * Kept free of any Verovio object so it is directly unit-testable (P02b).
 */
class BridgeAlternates {
public:
    /**
     * Finds the arrival points: an occurrence whose measure is not the document-order successor
     * of the previous occurrence's measure (a "jump" - the same definition as score_bridge's
     * ScoreTimeline._build/isJump), excluding a jump target that is already the first measure of
     * some normal page (there the normal page already serves).
     *
     * @param executionOrder Measure ids, already resolved to the notated id (§2.4's `-rendN`
     *     suffix rule already applied by the caller), one per occurrence, in execution order.
     * @param docOrder Measure id -> 0-based position in document order.
     * @param firstOfNormalPage Measure ids that are the first measure of some normal page.
     * @return Arrival points, without repetition, in document order.
     */
    static std::vector<std::string> FindAlternateStarts(const std::vector<std::string> &executionOrder,
        const std::map<std::string, int> &docOrder, const std::set<std::string> &firstOfNormalPage);
};

} // namespace vrv

#endif // __VRV_BRIDGE_ALTERNATES_H__
