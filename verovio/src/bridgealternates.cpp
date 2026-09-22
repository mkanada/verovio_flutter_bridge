/////////////////////////////////////////////////////////////////////////////
// Name:        bridgealternates.cpp
// Author:      Verovio Team
// Created:     2026
// Copyright (c) Authors and others. All rights reserved.
/////////////////////////////////////////////////////////////////////////////

#include "bridgealternates.h"

//----------------------------------------------------------------------------

#include <algorithm>
#include <cassert>
#include <unordered_set>

namespace vrv {

//----------------------------------------------------------------------------
// BridgeAlternates
//----------------------------------------------------------------------------

std::vector<std::string> BridgeAlternates::FindAlternateStarts(const std::vector<std::string> &executionOrder,
    const std::map<std::string, int> &docOrder, const std::set<std::string> &firstOfNormalPage)
{
    std::vector<std::string> starts;
    std::unordered_set<std::string> seen;

    for (std::size_t i = 1; i < executionOrder.size(); ++i) {
        const std::string &previous = executionOrder[i - 1];
        const std::string &current = executionOrder[i];

        const auto previousIt = docOrder.find(previous);
        const auto currentIt = docOrder.find(current);
        // Both ids come from the caller already resolved against docOrder's own domain (§2.4's
        // suffix rule); a lookup miss means the caller broke that contract.
        assert(previousIt != docOrder.end() && currentIt != docOrder.end());
        if (previousIt == docOrder.end() || currentIt == docOrder.end()) continue;

        const bool isJump = (currentIt->second != previousIt->second + 1);
        if (!isJump) continue;
        if (firstOfNormalPage.count(current)) continue;
        if (!seen.insert(current).second) continue;

        starts.push_back(current);
    }

    std::sort(starts.begin(), starts.end(),
        [&docOrder](const std::string &a, const std::string &b) { return docOrder.at(a) < docOrder.at(b); });
    return starts;
}

} // namespace vrv
