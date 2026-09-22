/////////////////////////////////////////////////////////////////////////////
// Name:        expansionmap.cpp
// Author:      Werner Goebl
// Created:     2019
// Copyright (c) Authors and others. All rights reserved.
/////////////////////////////////////////////////////////////////////////////

#include "expansionmap.h"

//----------------------------------------------------------------------------

#include <cassert>
#include <iostream>

//----------------------------------------------------------------------------

#include "editorial.h"
#include "ending.h"
#include "expansion.h"
#include "lem.h"
#include "linkinginterface.h"
#include "measure.h"
#include "plistinterface.h"
#include "rdg.h"
#include "score.h"
#include "section.h"
#include "timeinterface.h"
#include "vrv.h"

namespace vrv {

//----------------------------------------------------------------------------
// ExpansionMap
//----------------------------------------------------------------------------

ExpansionMap::ExpansionMap()
{
    this->Reset();
}

ExpansionMap::~ExpansionMap() {}

void ExpansionMap::Reset()
{
    m_map.clear();
    m_isProcessed = false;
}

Object *ExpansionMap::Expand(Expansion *expansion, xsdAnyURI_List &existingList, Object *prevSect,
    xsdAnyURI_List &deletionList, bool deleteList = false)
{
    assert(expansion);
    Object *parent = expansion->GetParent();
    assert(parent);

    xsdAnyURI_List expansionPlist = expansion->GetPlist();
    if (expansionPlist.empty()) {
        LogWarning("ExpansionMap::Expand: Expansion element %s has empty @plist. Nothing expanded.",
            expansion->GetID().c_str());
        return prevSect;
    }

    assert(prevSect);
    assert(prevSect->GetParent());

    Object *insertHere = nullptr; // cloned parent container

    // If expansion parent already exists, create a new empty such element
    if (std::find(existingList.begin(), existingList.end(), parent->GetID()) != existingList.end()) {
        Object *newContainer;
        // check type of expansion parent
        if (parent->Is(SECTION)) {
            newContainer = static_cast<Object *>(new Section());
        }
        else if (parent->Is(ENDING)) {
            newContainer = static_cast<Object *>(new Ending());
        }
        else if (parent->Is(LEM)) {
            newContainer = static_cast<Object *>(new Lem());
        }
        else if (parent->Is(RDG)) {
            newContainer = static_cast<Object *>(new Rdg());
        }
        else {
            LogWarning(
                "ExpansionMap::Expand: Expansion element %s has unsupported parent type.", expansion->GetID().c_str());
            return prevSect;
        }

        assert(parent->GetParent());
        Object *referenceChild = parent->GetDirectChild(parent->GetParent(), prevSect);
        assert(referenceChild);
        parent->GetParent()->InsertAfter(referenceChild, newContainer);
        GeneratePredictableIDs(parent, newContainer);
        LogDebug("Creating new container <%s> for expansion element %s", newContainer->GetClassName().c_str(),
            newContainer->GetID().c_str());

        insertHere = newContainer;
    }
    else if (std::find(existingList.begin(), existingList.end(), parent->GetID()) == existingList.end()) {
        existingList.push_back(parent->GetID());
    }

    // find and add all relevant (and new) expansion sibling ids to deletionList
    for (Object *siblings : parent->GetChildren()) {
        if (siblings->IsAnyOf(std::array{ SECTION, ENDING, LEM, RDG })
            && std::count(deletionList.begin(), deletionList.end(), siblings->GetID()) == 0) {
            deletionList.push_back(siblings->GetID());
        }
    }

    // iterate over expansion plist
    for (std::string id : expansionPlist) {
        LogDebug("Looking for element in @plist: %s", id.c_str());
        if (id.rfind("#", 0) == 0) id = id.substr(1, id.size() - 1); // remove leading hash from id
        Object *currSect = parent->FindDescendantByID(id); // find section pointer for id string
        // E04a: GenerateExpansionFor can now build a repeat out of measures that started in a
        // *different* <section> than the one the expansion itself lives in (several consecutive
        // <section> elements, the pattern the MEI corpus converter produces) - the new child
        // section created for such a repeat is a descendant of that other section, not of
        // `parent`. Widen the search to the whole score before giving up; this is a pure
        // fallback (only tried when the direct lookup fails), so a plist entirely inside `parent`
        // - every case before E04a - resolves exactly as before.
        if (currSect == NULL) {
            Object *scoreAncestor = parent->GetFirstAncestor(SCORE);
            if (scoreAncestor) currSect = scoreAncestor->FindDescendantByID(id);
        }
        if (currSect == NULL) {
            // Warn about referenced element not found and continue
            LogWarning("ExpansionMap::Expand: Element referenced in @plist not found: %s", id.c_str());
            continue;
        }
        if (currSect->Is(EXPANSION)) { // if id is itself an expansion, resolve it recursively
            Expansion *currExpansion = vrv_cast<Expansion *>(currSect);
            assert(currExpansion);
            prevSect = this->Expand(currExpansion, existingList, prevSect, deletionList);
        }
        else {
            // id already in existingList or currSect is not in expansion parent, clone object, update ids, insert it
            if (std::find(existingList.begin(), existingList.end(), id) != existingList.end()
                || (insertHere != NULL && currSect->GetParent() != insertHere)) {

                // clone current section/ending/rdg/lem and rename it, adding -"rend2" for the first repetition etc.
                Object *clonedObject = currSect->Clone();
                clonedObject->CloneReset();
                this->GeneratePredictableIDs(currSect, clonedObject);

                // get IDs of old and new sections and add them to m_map
                std::vector<std::string> oldIds;
                oldIds.push_back(currSect->GetID());
                this->GetIDList(currSect, oldIds);
                std::vector<std::string> clonedIds;
                clonedIds.push_back(clonedObject->GetID());
                this->GetIDList(clonedObject, clonedIds);
                for (int i = 0; (i < (int)oldIds.size()) && (i < (int)clonedIds.size()); ++i) {
                    this->AddExpandedIDToExpansionMap(oldIds.at(i), clonedIds.at(i));
                }

                // go through cloned objects, find TimePointing/SpanningInterface, PListInterface, LinkingInterface
                this->UpdateIDs(clonedObject);

                LogDebug("Cloning element in @plist: %s", clonedObject->GetID().c_str());

                if (insertHere != NULL) {
                    insertHere->AddChild(clonedObject); // add to new container, if it exists
                }
                else {
                    prevSect->GetParent()->InsertAfter(prevSect, clonedObject); // or add after previous section
                }

                prevSect = clonedObject;
                existingList.push_back(clonedObject->GetID());
            }
            else { // add to existingList, remember previous element, re-order if necessary

                bool moveCurrentElement = false;
                int prevIdx = prevSect->GetIdx();
                int childCount = prevSect->GetParent()->GetChildCount();
                int currIdx = currSect->GetIdx();

                // check re-order when within same parent
                if (currSect->GetParent()->GetID() == prevSect->GetParent()->GetID()) {
                    // If prevSect has a next element and if it is different than the currSect or has no next element,
                    // move it to after the currSect.
                    if (prevIdx < childCount - 1) {
                        Object *nextElement = prevSect->GetParent()->GetChild(prevIdx + 1);
                        assert(nextElement);
                        if (nextElement->IsAnyOf(std::array{ SECTION, ENDING, LEM, RDG }) && nextElement != currSect) {
                            moveCurrentElement = true;
                        }
                    }
                    else {
                        moveCurrentElement = true;
                    }
                }

                // move prevSect to after currSect
                if (moveCurrentElement && currIdx < prevIdx && prevIdx < childCount) {
                    LogDebug(
                        "Re-ordering element %s to after %s", currSect->GetID().c_str(), prevSect->GetID().c_str());
                    currSect->GetParent()->RotateChildren(currIdx, currIdx + 1, prevIdx + 1);
                }
                else {
                    LogDebug("Leaving existing element %s", currSect->GetID().c_str());
                }

                prevSect = currSect;
                existingList.push_back(id);
            }
        }
    }

    // at the very end, remove unused sections from structure if not in existingList
    if (deleteList) {
        for (std::string del : deletionList) {
            long cnt = std::count(existingList.begin(), existingList.end(), del);
            if (cnt == 0) {
                Object *currSect = parent->FindDescendantByID(del); // find section pointer for id string
                assert(currSect);

                int idx = currSect->GetIdx();
                LogDebug("ExpansionMap::Expand: Removing unused section/ending/rdg/lem with id %s", del.c_str());
                currSect->GetParent()->DetachChild(idx);
            }
        }
    }

    return prevSect;
}

bool ExpansionMap::UpdateIDs(Object *object)
{
    for (Object *o : object->GetChildren()) {
        o->IsExpansion(true);
        if (o->HasInterface(INTERFACE_TIME_POINT)) {
            TimePointInterface *interface = o->GetTimePointInterface();
            assert(interface);
            // @startid
            std::string oldStartId = interface->GetStartid();
            if (oldStartId.rfind("#", 0) == 0) oldStartId = oldStartId.substr(1, oldStartId.size() - 1);
            std::string newStartId = this->GetExpansionIDsForElement(oldStartId).back();
            if (!newStartId.empty()) interface->SetStartid("#" + newStartId);
        }
        if (o->HasInterface(INTERFACE_TIME_SPANNING)) {
            TimeSpanningInterface *interface = o->GetTimeSpanningInterface();
            assert(interface);
            // @startid
            std::string oldStartId = interface->GetStartid();
            if (oldStartId.rfind("#", 0) == 0) oldStartId = oldStartId.substr(1, oldStartId.size() - 1);
            std::string newStartId = this->GetExpansionIDsForElement(oldStartId).back();
            if (!newStartId.empty()) interface->SetStartid("#" + newStartId);
            // @endid
            oldStartId = interface->GetEndid();
            if (oldStartId.rfind("#", 0) == 0) oldStartId = oldStartId.substr(1, oldStartId.size() - 1);
            std::string newEndId = this->GetExpansionIDsForElement(oldStartId).back();
            if (!newEndId.empty()) interface->SetEndid("#" + newEndId);
        }
        if (o->HasInterface(INTERFACE_PLIST)) {
            PlistInterface *interface = o->GetPlistInterface(); // @plist
            assert(interface);
            xsdAnyURI_List oldList = interface->GetPlist();
            xsdAnyURI_List newList;
            for (std::string oldRefString : oldList) {
                if (oldRefString.rfind("#", 0) == 0) oldRefString = oldRefString.substr(1, oldRefString.size() - 1);
                newList.push_back("#" + this->GetExpansionIDsForElement(oldRefString).back());
            }
            interface->SetPlist(newList);
        }
        else if (o->HasInterface(INTERFACE_LINKING)) {
            LinkingInterface *interface = o->GetLinkingInterface();
            assert(interface);
            // @sameas
            std::string oldIdString = interface->GetSameas();
            if (oldIdString.rfind("#", 0) == 0) oldIdString = oldIdString.substr(1, oldIdString.size() - 1);
            std::string newIdString = this->GetExpansionIDsForElement(oldIdString).back();
            if (!newIdString.empty()) interface->SetSameas("#" + newIdString);
            // @next
            oldIdString = interface->GetNext();
            if (oldIdString.rfind("#", 0) == 0) oldIdString = oldIdString.substr(1, oldIdString.size() - 1);
            newIdString = this->GetExpansionIDsForElement(oldIdString).back();
            if (!newIdString.empty()) interface->SetNext("#" + newIdString);
            // @prev
            oldIdString = interface->GetPrev();
            if (oldIdString.rfind("#", 0) == 0) oldIdString = oldIdString.substr(1, oldIdString.size() - 1);
            newIdString = this->GetExpansionIDsForElement(oldIdString).back();
            if (!newIdString.empty()) interface->SetPrev("#" + newIdString);
            // @copyof
            oldIdString = interface->GetCopyof();
            if (oldIdString.rfind("#", 0) == 0) oldIdString = oldIdString.substr(1, oldIdString.size() - 1);
            newIdString = this->GetExpansionIDsForElement(oldIdString).back();
            if (!newIdString.empty()) interface->SetCopyof("#" + newIdString);
            // @synch
            oldIdString = interface->GetSynch();
            if (oldIdString.rfind("#", 0) == 0) oldIdString = oldIdString.substr(1, oldIdString.size() - 1);
            newIdString = this->GetExpansionIDsForElement(oldIdString).back();
            if (!newIdString.empty()) interface->SetSynch("#" + newIdString);
            // @corresp is already handle by the Object::Clone and LinkingInterface::AddBackLink
        }
        this->UpdateIDs(o);
    }
    return true;
}

bool ExpansionMap::AddExpandedIDToExpansionMap(const std::string &origXmlId, std::string newXmlId)
{
    auto list = m_map.find(origXmlId);
    if (list != m_map.end()) {
        list->second.push_back(newXmlId); // add to existing key
        for (std::string s : list->second) {
            if (s != list->second.front() && s != list->second.back()) {
                m_map.at(s).push_back(newXmlId); // add to middle keys
            }
        }
        m_map.insert({ newXmlId, m_map.at(origXmlId) }); // add new as key
    }
    else {
        std::vector<std::string> s;
        s.push_back(origXmlId);
        s.push_back(newXmlId);
        m_map.insert({ origXmlId, s });
        m_map.insert({ newXmlId, s });
    }
    return true;
}

std::vector<std::string> ExpansionMap::GetExpansionIDsForElement(const std::string &xmlId)
{
    if (m_map.contains(xmlId)) {
        return m_map.at(xmlId);
    }
    else {
        std::vector<std::string> ids;
        ids.push_back(xmlId.c_str());
        return ids;
    }
}

bool ExpansionMap::HasExpansionMap()
{
    return (m_map.empty()) ? false : true;
}

void ExpansionMap::GetIDList(Object *object, std::vector<std::string> &idList)
{
    for (Object *o : object->GetChildren()) {
        idList.push_back(o->GetID());
        this->GetIDList(o, idList);
    }
}

void ExpansionMap::GeneratePredictableIDs(Object *source, Object *target)
{
    target->SetID(
        source->GetID() + "-rend" + std::to_string(this->GetExpansionIDsForElement(source->GetID()).size() + 1));

    ArrayOfObjects sourceObjects = source->GetChildren();
    ArrayOfObjects targetObjects = target->GetChildren();
    if (sourceObjects.size() <= 0 || sourceObjects.size() != targetObjects.size()) return;

    unsigned i = 0;
    for (Object *s : sourceObjects) {
        this->GeneratePredictableIDs(s, targetObjects.at(i++));
    }
}

void ExpansionMap::ToJson(std::string &output)
{
    jsonxx::Object expansionmap;
    for (auto &[id, ids] : m_map) {
        jsonxx::Array expandedIds;
        for (auto i : ids) expandedIds << i;
        expansionmap << id << expandedIds;
        ;
    }
    output = expansionmap.json();
}

void ExpansionMap::GenerateExpansionFor(Score *score)
{
    m_isProcessed = true;

    if (score->HasEditorialContent()) {
        LogWarning("An expansion cannot be generated with editorial content");
        return;
    }

    // E04a: several consecutive <section> elements (the pattern produced by the converter that
    // made the MEI corpus - each ritornello section of its own) used to make GenerateExpansionFor
    // bail out entirely. We now walk measures and <ending> groups in document order *across*
    // section boundaries, so a repeat that starts in one <section> and ends in the next (or
    // starts exactly where a new one begins, as in the corpus) is still found. Nothing here
    // touches how many <section> elements exist in the drawn document - CreateSection() below
    // only ever adds a new child section, moving existing measures/endings into it.
    ListOfObjects sectionChildren = score->FindAllDescendantsByType(SECTION);
    if (sectionChildren.empty()) return;
    std::vector<Section *> sections;
    for (Object *object : sectionChildren) sections.push_back(vrv_cast<Section *>(object));

    // Flatten the direct measure/ending children of every <section>, in document order, into one
    // list with stable iterators (CreateSection mutates the tree as we go; a std::list keeps
    // `first`/`last`/`groupStart` valid across that).
    ListOfObjects items;
    for (Section *section : sections) {
        for (Object *child : section->GetChildrenForModification()) {
            if (child->Is(MEASURE) || child->Is(ENDING)) items.push_back(child);
        }
    }
    if (items.empty()) return;

    Expansion *expansion = new Expansion();

    ListOfObjects::iterator first = items.begin();
    ListOfObjects::iterator last = items.begin();

    bool isStartFromPrevious = false;

    for (auto current = items.begin(); current != items.end();) {
        if ((*current)->Is(ENDING)) {
            // Gather the consecutive run of <ending> siblings (casa 1, casa 2, ...): a group,
            // not individual measures, because only entire endings are ever cited in the plist
            // (E04a; a repeat ending on some *other* note inside an ending, or more than one
            // casa in a single <ending>, is out of scope - see E04a "Fora de escopo").
            std::vector<Ending *> endings;
            while (current != items.end() && (*current)->Is(ENDING)) {
                endings.push_back(vrv_cast<Ending *>(*current));
                ++current;
            }
            if (!endings.empty() && ExpansionMap::EndingHasRepeatEnd(endings.front())) {
                // The shared material before the endings repeats once per casa: [shared, casa 1,
                // shared, casa 2, ..., casa N] - Expand() places the first ref of a given id as-is
                // and clones every later one, so this alternation is what turns into "play the
                // shared part, casa 1, the shared part again, casa 2" without a second CreateSection
                // call or any bookkeeping of which pass we are on.
                std::string sharedRef = "#" + this->CreateSection(first, last);
                for (size_t i = 0; i < endings.size(); ++i) {
                    expansion->GetPlistInterface()->AddRefAllowDuplicate(sharedRef);
                    expansion->GetPlistInterface()->AddRefAllowDuplicate("#" + endings.at(i)->GetID());
                }
            }
            // Either way, whatever comes after this ending group starts a fresh span (a repeat
            // cannot itself begin inside an ending in the corpus - out of scope otherwise).
            first = current;
            last = current;
            continue;
        }

        Measure *measure = vrv_cast<Measure *>(*current);
        // The current measure has a repeat end on its left
        if (ExpansionMap::IsPreviousRepeatEnd(measure)) {
            std::string ref = "#" + this->CreateSection(first, last);
            expansion->GetPlistInterface()->AddRefAllowDuplicate(ref);
            expansion->GetPlistInterface()->AddRefAllowDuplicate(ref);
        }
        if (isStartFromPrevious || ExpansionMap::IsRepeatStart(measure)) {
            first = current;
        }
        // The current measure has a repeat start on its right
        isStartFromPrevious = ExpansionMap::IsNextRepeatStart(measure);
        last = current;
        if (ExpansionMap::IsRepeatEnd(measure)) {
            std::string ref = "#" + this->CreateSection(first, last);
            expansion->GetPlistInterface()->AddRefAllowDuplicate(ref);
            expansion->GetPlistInterface()->AddRefAllowDuplicate(ref);
        }
        ++current;
    }

    if (expansion->GetPlist().empty()) {
        delete expansion;
    }
    else {
        // Same convention as before E04a (single section): the expansion lives at the very start
        // of the first <section>, regardless of which section(s) the repeated spans came from.
        sections.front()->InsertChild(expansion, 0);
    }
}

std::string ExpansionMap::CreateSection(const ListOfObjects::iterator &first, const ListOfObjects::iterator &last)
{
    Object *anchorParent = (*first)->GetParent();
    assert(anchorParent);
    Section *subSection = new Section();
    anchorParent->InsertBefore(*first, subSection);
    for (auto current = first; current != std::next(last); current++) {
        Object *parent = (*current)->GetParent();
        assert(parent);
        parent->DetachChild((*current)->GetIdx());
        subSection->AddChild(*current);
    }
    return subSection->GetID();
}

bool ExpansionMap::EndingHasRepeatEnd(Ending *ending)
{
    for (Object *child : ending->GetChildren()) {
        if (child->Is(MEASURE) && ExpansionMap::IsRepeatEnd(vrv_cast<Measure *>(child))) return true;
    }
    return false;
}

//----------------------------------------------------------------------------
// Static methods
//----------------------------------------------------------------------------

bool ExpansionMap::IsRepeatStart(Measure *measure)
{
    static const std::vector<data_BARRENDITION> match{ BARRENDITION_rptboth, BARRENDITION_rptstart };

    if (!measure->HasLeft()) return false;

    return (std::find(match.begin(), match.end(), measure->GetLeft()) != match.end());
}

bool ExpansionMap::IsRepeatEnd(Measure *measure)
{
    static const std::vector<data_BARRENDITION> match{ BARRENDITION_rptboth, BARRENDITION_rptend };

    if (!measure->HasRight()) return false;

    return (std::find(match.begin(), match.end(), measure->GetRight()) != match.end());
}

bool ExpansionMap::IsNextRepeatStart(Measure *measure)
{
    static const std::vector<data_BARRENDITION> match{ BARRENDITION_rptboth, BARRENDITION_rptstart };

    if (!measure->HasRight()) return false;

    return (std::find(match.begin(), match.end(), measure->GetRight()) != match.end());
}

bool ExpansionMap::IsPreviousRepeatEnd(Measure *measure)
{
    static const std::vector<data_BARRENDITION> match{ BARRENDITION_rptboth, BARRENDITION_rptend };

    if (!measure->HasLeft()) return false;

    return (std::find(match.begin(), match.end(), measure->GetLeft()) != match.end());
}

} // namespace vrv
