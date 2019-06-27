import xml.etree.ElementTree as ET
import bcf.util
from typing import List
from enum import Enum
from uuid import UUID
from datetime import date
from xmlschema import XMLSchema
from bcf.modification import (ModificationDate, ModificationAuthor,
        ModificationType)
from bcf.uri import Uri
from bcf.project import (Attribute, SimpleElement, SimpleList,
        searchListObject)
from bcf.project import DEBUG
from interfaces.hierarchy import Hierarchy
from interfaces.identifiable import XMLIdentifiable, Identifiable
from interfaces.state import State
from interfaces.xmlname import XMLName


class DocumentReference(Hierarchy, State, XMLName, Identifiable):
    def __init__(self,
                guid: UUID = None,
                external: bool = False,
                reference: Uri = None,
                description: str = "",
                containingElement = None,
                state: State.States = State.States.ORIGINAL):

        """ Initialization function for DocumentReference """

        Hierarchy.__init__(self, containingElement)
        State.__init__(self, state)
        XMLName.__init__(self)
        Identifiable.__init__(self)
        self._guid = Attribute(guid, "Guid", UUID(int=0), self)
        self._external = Attribute(external, "isExternal", False, self)
        self._reference = SimpleElement(reference, "ReferencedDocument",
                None, self)
        self._description = SimpleElement(description, "Description",
                "", self)


    @property
    def guid(self):
        return self._guid.value

    @guid.setter
    def guid(self, newVal):
        if isinstance(newVal, str):
            self._guid.value = UUID(newVal)
        elif isinstance(newVal, UUID):
            self._guid.value = newVal

    @property
    def external(self):
        return self._external.value

    @external.setter
    def external(self, newVal):
        self._external.value = newVal

    @property
    def reference(self):
        return self._reference.value

    @reference.setter
    def reference(self, newVal):
        self._reference.value = newVal

    @property
    def description(self):
        return self._description.value

    @description.setter
    def description(self, newVal):
        self._description.value = newVal

    def __eq__(self, other):

        """
        Returns true if every variable member of both classes are the same
        """

        if type(self) != type(other):
            return False

        return (self.guid == other.guid and
                self.external == other.external and
                self.reference == other.reference and
                self.description == other.description)


    def __str__(self):
        str_ret = ("DocumentReference(guid={}, external={}, reference={},"\
            " description={})").format(self.guid, self.external, self.reference,
                self.description)

        return str_ret


    def getEtElement(self, elem):

        """
        Convert the contents of the object to an xml.etree.ElementTree.Element
        representation. `element` is the object of type xml.e...Tree.Element
        which shall be modified and returned.
        """

        elem.tag = self.xmlName

        # guid is optional in DocumentReference
        defaultValue = self._guid.defaultValue
        if self.guid != defaultValue:
            elem.attrib["Guid"] = str(self.guid)

        defaultValue = self._external.defaultValue
        if self.external != defaultValue:
            elem.attrib["isExternal"] = str(self.external).lower()

        defaultValue = self._reference.defaultValue
        if str(self.reference) != defaultValue:
            refElem = ET.SubElement(elem, "ReferencedDocument")
            refElem.text = str(self.reference)

        defaultValue = self._description.defaultValue
        if self.description != defaultValue:
            descElem = ET.SubElement(elem, "Description")
            descElem.text = self.description

        return elem


    def getStateList(self):

        stateList = list()
        if not self.isOriginal():
            stateList.append((self.state, self))

        stateList += self._guid.getStateList()
        stateList += self._external.getStateList()
        stateList += self._reference.getStateList()
        stateList += self._description.getStateList()

        return stateList


    def searchObject(self, object):

        if not issubclass(type(object), Identifiable):
            return None

        id = object.id
        if self.id == id:
            return self

        members = [ self._guid, self._external, self._reference,
                self._description ]
        searchResult = searchListObject(object, members)
        return searchResult


class BimSnippet(Hierarchy, State, XMLName, Identifiable):
    def __init__(self,
            type: str = "",
            external: bool = False,
            reference: Uri = None,
            schema: Uri = None,
            containingElement = None,
            state: State.States = State.States.ORIGINAL):

        """ Initialization function for BimSnippet """

        Hierarchy.__init__(self, containingElement)
        State.__init__(self, state)
        XMLName.__init__(self)
        Identifiable.__init__(self)
        self._type = Attribute(type, "SnippetType", "", self)
        self._external = Attribute(external, "isExternal", False, self)
        self._reference = SimpleElement(reference, "Reference", None, self)
        self._schema = SimpleElement(schema, "ReferenceSchema", None, self)


    @property
    def type(self):
        return self._type.value

    @type.setter
    def type(self, newVal):
        self._type.value = newVal

    @property
    def external(self):
        return self._external.value

    @external.setter
    def external(self, newVal):
        self._external.value = newVal

    @property
    def reference(self):
        return self._reference.value

    @reference.setter
    def reference(self, newVal):
        self._reference.value = newVal

    @property
    def schema(self):
        return self._schema.value

    @schema.setter
    def schema(self, newVal):
        self._schema.value = newVal

    def __eq__(self, other):

        """
        Returns true if every variable member of both classes are the same
        """

        if type(self) != type(other):
            return False

        return (self.type == other.type and
                self.external == other.external and
                self.reference == other.reference and
                self.schema == other.schema)

    def __str__(self):

        ret_str = ("BimSnippet(type='{}', isExternal='{}, reference='{}',"\
                " referenceSchema='{}'").format(self.type, self.external,
                        self.reference, self.schema)
        return ret_str


    def getEtElement(self, elem):

        """
        Convert the contents of the object to an xml.etree.ElementTree.Element
        representation. `element` is the object of type xml.e...Tree.Element
        which shall be modified and returned.
        """

        elem.tag = "BimSnippet"
        elem.attrib["SnippetType"] = str(self.type)
        elem.attrib["isExternal"] = str(self.external).lower()

        defaultValue = self._reference.defaultValue
        if self.reference != defaultValue:
            refElem = ET.SubElement(elem, "Reference")
            refElem.text = str(self.reference)

        defaultValue = self._schema.defaultValue
        if self.schema != defaultValue:
            schemaElem = ET.SubElement(elem, "ReferenceSchema")
            schemaElem.text = str(self.schema)

        return elem


    def getStateList(self):

        stateList = list()
        if not self.isOriginal():
            stateList.append((self.state, self))

        stateList += self._type.getStateList()
        stateList += self._external.getStateList()
        stateList += self._reference.getStateList()
        stateList += self._schema.getStateList()

        return stateList


    def searchObject(self, object):

        if not issubclass(type(object), Identifiable):
            return None

        id = object.id
        if self.id == id:
            return self

        members = [ self._type, self._external, self._reference, self._schema ]
        searchResult = searchListObject(object, members)

        return searchResult


class Topic(Hierarchy, XMLIdentifiable, State, XMLName, Identifiable):

    """ Topic contains all metadata about one ... topic """

    def __init__(self,
            id: UUID,
            title: str,
            date: ModificationDate,
            author: ModificationAuthor,
            type: str = "",
            status: str = "",
            referenceLinks: List[str] = list(),
            docRefs: List[DocumentReference] = list(),
            priority: str = "",
            index: int = 0,
            labels: List[str] = list(),
            modDate: ModificationDate = None,
            modAuthor: ModificationAuthor = "",
            dueDate: date = None,
            assignee: str = "",
            description: str = "",
            stage: str = "",
            relatedTopics: List[UUID] = [],
            bimSnippet: BimSnippet = None,
            containingElement = None,
            state: State.States = State.States.ORIGINAL):

        """ Initialisation function of Topic """

        Hierarchy.__init__(self, containingElement)
        XMLIdentifiable.__init__(self, id)
        State.__init__(self, state)
        XMLName.__init__(self)
        Identifiable.__init__(self)
        self._title = SimpleElement(title, "Title", "", self)
        self._date = ModificationDate(date, self)
        self._author = ModificationAuthor(author, self)
        self._type = Attribute(type, "TopicType", "", self)
        self._status = Attribute(status, "TopicStatus", "", self)
        self.referenceLinks = SimpleList(referenceLinks, "ReferenceLink",
                "", self)
        self.docRefs = docRefs
        self._priority = SimpleElement(priority, "Priority", "", self)
        self._index = SimpleElement(index, "Index", -1, self)
        self.labels = SimpleList(labels, "Labels", "", self)
        self._modDate = ModificationDate(modDate, self,
                ModificationType.MODIFICATION)
        self._modAuthor = ModificationAuthor(modAuthor, self,
                ModificationType.MODIFICATION)
        self._dueDate = SimpleElement(dueDate, "DueDate", None, self)
        self._assignee = SimpleElement(assignee, "AssignedTo", "", self)
        self._description = SimpleElement(description, "Description",
                "", self)
        self._stage = SimpleElement(stage, "Stage", "", self)
        self.relatedTopics = SimpleList(relatedTopics, "RelatedTopic",
                UUID(int=0), self)
        self.bimSnippet = bimSnippet

        # set containingObjecf for all document references
        for docRef in self.docRefs:
            docRef.containingObject = self

        if self.bimSnippet is not None:
            self.bimSnippet.containingObject = self


    @property
    def date(self):
        return self._date.value

    @date.setter
    def date(self, newVal):
        self._date.date = newVal

    @property
    def author(self):
        return self._author.value

    @author.setter
    def author(self, newVal):
        self._author.author = newVal

    @property
    def modDate(self):
        return self._modDate.value

    @modDate.setter
    def modDate(self, newVal):
        self._modDate.date = newVal

    @property
    def modAuthor(self):
        return self._modAuthor.value

    @modAuthor.setter
    def modAuthor(self, newVal):
        self._modAuthor.author = newVal

    @property
    def stage(self):
        return self._stage.value

    @stage.setter
    def stage(self, newVal):
        self._stage.value = newVal

    @property
    def description(self):
        return self._description.value

    @description.setter
    def description(self, newVal):
        self._description.value = newVal

    @property
    def assignee(self):
        return self._assignee.value

    @assignee.setter
    def assignee(self, newVal):
        self._assignee.value = newVal

    @property
    def dueDate(self):
        return self._dueDate.value

    @dueDate.setter
    def dueDate(self, newVal):
        self._dueDate.value = newVal

    @property
    def index(self):
        return self._index.value

    @index.setter
    def index(self, newVal):
        self._index.value = newVal

    @property
    def priority(self):
        return self._priority.value

    @priority.setter
    def priority(self, newVal):
        self._priority.value = newVal

    @property
    def status(self):
        return self._status.value

    @status.setter
    def status(self, newVal):
        self._status.value = newVal

    @property
    def type(self):
        return self._type.value

    @type.setter
    def type(self, newVal):
        self._type.value = newVal

    @property
    def title(self):
        return self._title.value

    @title.setter
    def title(self, newVal):
        self._title.value = newVal


    def __checkNone(self, this, that):

        equal = False
        if this and that:
            equal = this == that
        elif (this is None and that is None):
            equal = True
        return equal


    def __printEquality(self, equal, name):

        if not equal:
            print("{} is not equal".format(name))


    def __eq__(self, other):

        """
        Returns true if every variable member of both classes are the same
        """

        if type(self) != type(other):
            return False

        self.__printEquality(self.xmlId == other.xmlId, "id")
        self.__printEquality(self.title == other.title, "title")
        self.__printEquality(self.date == other.date, "date")
        self.__printEquality(self.author == other.author, "author")
        self.__printEquality(self.type == other.type, "type")
        self.__printEquality(self.status == other.status, "status")
        self.__printEquality(self.docRefs == other.docRefs, "docRefs")
        self.__printEquality(self.priority == other.priority, "priority")
        self.__printEquality(self.index == other.index, "index")
        self.__printEquality(self.labels == other.labels, "labels")
        self.__printEquality(self.assignee == other.assignee, "assignee")
        self.__printEquality(self.description == other.description, "description")
        self.__printEquality(self.stage == other.stage, "stage")
        self.__printEquality(self.relatedTopics == other.relatedTopics,
                "relatedTopics")
        self.__printEquality(self.modDate == other.modDate, "ModificationDate")
        self.__printEquality(self.modAuthor == other.modAuthor, "ModificationAuthor")
        self.__printEquality(self.__checkNone(self.dueDate,
            other.dueDate), "dueDate")
        self.__printEquality(self.__checkNone(self.bimSnippet,
            other.bimSnippet), "bimSnippet")

        return (self.xmlId == other.xmlId and
                self.title == other.title and
                self.__checkNone(self.date, other.date) and
                self.author == other.author and
                self.type == other.type and
                self.status == other.status and
                self.docRefs == other.docRefs and
                self.priority == other.priority and
                self.index == other.index and
                self.labels == other.labels and
                self.__checkNone(self.modDate, other.modDate) and
                self.modAuthor, other.modAuthor and
                self.__checkNone(self.dueDate, other.dueDate) and
                self.assignee == other.assignee and
                self.description == other.description and
                self.stage == other.stage and
                self.relatedTopics == other.relatedTopics and
                self.bimSnippet == other.bimSnippet)

    def __str__(self):
        import pprint
        doc_ref_str = "None"
        if self.docRefs:
            doc_ref_str = "["
            for doc_ref in self.docRefs:
                doc_ref_str += str(doc_ref)
            doc_ref_str += "]"

        str_ret = """---- Topic ----
    ID: {},
    Title: {},
    Date: {},
    Author: {},
    Type: {},
    Status: {},
    Priority: {},
    Index: {},
    ModificationDate: {},
    ModificationAuthor: {},
    DueDate: {},
    AssignedTo: {},
    Description: {},
    Stage: {},
    RelatedTopics: {},
    Labels: {},
    DocumentReferences: {}""".format(self.xmlId, self.title, str(self.date),
            self.author,
            self.type, self.status, self.priority, self.index,
            str(self.modDate), self.modAuthor, self.dueDate,
            self.assignee, self.description, self.stage, self.relatedTopics,
            self.labels, doc_ref_str)
        return str_ret


    def _createSimpleNode(self, parentNode: ET.Element,
            classMember: SimpleElement):

        """
        Create a simple xml node with the content of `classMember`.
        """

        newNode = None
        dflValue = classMember.defaultValue
        if classMember.value != dflValue:
            newNode = ET.SubElement(parentNode, classMember.xmlName)
            newNode = classMember.getEtElement(newNode)

        return newNode


    def getEtElement(self, elem):

        """
        Convert the contents of the object to an xml.etree.ElementTree.Element
        representation. `element` is the object of type xml.e...Tree.Element
        which shall be modified and returned.
        """

        elem.tag = self.xmlName
        elem.attrib["Guid"] = str(self.xmlId)

        defaultValue = self._type.defaultValue
        if self.type != defaultValue:
            elem.attrib["type"] = self.type

        defaultValue = self._status.defaultValue
        if self.status != defaultValue:
            elem.attrib["status"] = self.status

        for refLink in self.referenceLinks:
            refLinkElem = self._createSimpleNode(elem, refLink)

        titleElem = ET.SubElement(elem, "Title")
        titleElem = self._title.getEtElement(titleElem)

        prioElem = self._createSimpleNode(elem, self._priority)
        idxElem = self._createSimpleNode(elem, self._index)

        for lbl in self.labels:
            lblElem = self._createSimpleNode(elem, lbl)

        dateElem = ET.SubElement(elem, "Date")
        dateElem = self._date.getEtElement(dateElem)

        authorElem = ET.SubElement(elem, "Author")
        authorElem = self._author.getEtElement(authorElem)

        if self.modDate is not None:
            modDateElem = self._createSimpleNode(elem,
                    self._modDate)
            modAuthorElem = self._createSimpleNode(elem,
                    self._modAuthor)

        dueDateElem = self._createSimpleNode(elem, self._dueDate)
        assigneeElem = self._createSimpleNode(elem, self._assignee)
        stageElem = self._createSimpleNode(elem, self._stage)
        descElem = self._createSimpleNode(elem, self._description)

        if self.bimSnippet is not None:
            bimSnippetElem = ET.SubElement(elem, self.bimSnippet.xmlName)
            bimSnippetElem = self.bimSnippet.getEtElement(bimSnippetElem)

        for docRef in self.docRefs:
            docRefElem = ET.SubElement(elem, docRef.xmlName)
            docRefElem = docRef.getEtElement(docRefElem)

        for relTopic in self.relatedTopics:
            relTopicElem = self._createSimpleNode(elem, relTopic)

        return elem


    def getStateList(self):

        stateList = list()
        if not self.isOriginal():
            stateList.append((self.state, self))

        stateList += self._title.getStateList()
        stateList += self.creation.getStateList()
        stateList += self._type.getStateList()
        stateList += self._status.getStateList()
        stateList += self.referenceLinks.getStateList() #TODO: better solution with simple list. Objects in simple list are not inherited from State
        for ref in self.refs:
            stateList += ref.getStateList()

        stateList += self._priority.getStateList()
        stateList += self._index.getStateList()
        stateList += self.labels.getStateList() #TODO: better solution with simple list. Objects in simple list are not inherited from State
        if self.lastModification is not None:
            stateList += self.lastModification.getStateList()

        stateList += self._dueDate.getStateList()
        stateList += self._assignee.getStateList()
        stateList += self._description.getStateList()
        stateList += self._stage.getStateList()
        stateList += self.relatedTopics.getStateList() #TODO: better solution with simple list. Objects in simple list are not inherited from State
        if self.bimSnippet is not None:
            stateList += self.bimSnippet.getStateList()

        if DEBUG:
            print("Topic.getStateList(): returning {}".format(stateList))
        return stateList


    def searchObject(self, object):

        if not issubclass(type(object), Identifiable):
            return None

        id = object.id
        if self.id == id:
            return self

        members = [ self._title, self._date, self._author, self._type,
                self._status, self._priority, self._index, self._modDate,
                self._modAuthor, self._dueDate, self._assignee,
                self._description, self._stage, self.bimSnippet ]
        searchResult = searchListObject(object, members)
        if searchResult is not None:
            return searchResult

        searchResult = searchListObject(object, self.referenceLinks)
        if searchResult is not None:
            return searchResult

        searchResult = searchListObject(object, self.docRefs)
        if searchResult is not None:
            return searchResult

        searchResult = searchListObject(object, self.labels)
        if searchResult is not None:
            return searchResult

        searchResult = searchListObject(object, self.relatedTopics)
        if searchResult is not None:
            return searchResult

        return None
