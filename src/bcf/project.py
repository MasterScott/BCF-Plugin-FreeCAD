from uuid import UUID
from bcf.uri import Uri
from interfaces.hierarchy import Hierarchy
from interfaces.state import State
from interfaces.xmlname import XMLName
from interfaces.identifiable import Identifiable


class SimpleElement(XMLName, Hierarchy):

    """
    Used for representing elements that are defined to be simple elements
    in the corresponding xsd file
    """

    def __init__(self, value, xmlName, containingElement):
        XMLName.__init__(self, xmlName)
        Hierarchy.__init__(self, containingElement)
        self.value = value


    def __eq__(self, other):
        if type(self) != type(other):
            return False

        # None != None is assumed
        if self is None or other is None:
            return False

        return (self.value == other.value and
                self.xmlName == other.xmlName)


    def __str__(self):
        return "{}: {}".format(self.xmlName, self.value)


class SimpleList(list, Hierarchy, XMLName):

    """
    Used for lists that contain just simple types. For example the `Labels`
    element in Topic is translated to a list in this data model. Every `Label`
    element just contains a string (and therefore is a simple type).
    """

    def __init__(self, data=[], xmlName = "", containingElement = None):

        list.__init__(self, data)
        Hierarchy.__init__(self, containingElement)
        XMLName.__init__(self, xmlName)

    def __eq__(self, other):

        return (list.__eq__(self, other) and
                XMLName.__eq__(self, other))


class Attribute(XMLName, Hierarchy):

    """
    Analogously to `SimpleElement` this class is used to represent attributes.
    """

    def __init__(self, value, xmlName, containingElement):
        XMLName.__init__(self, xmlName)
        Hierarchy.__init__(self, containingElement)
        self.value = value


class Project(Hierarchy, State, XMLName, Identifiable):
    def __init__(self,
            uuid: UUID,
            name: str = "",
            extSchemaSrc: Uri = None,
            state: State.States = State.States.ORIGINAL):

        """ Initialisation function of Project """

        Hierarchy.__init__(self, None) # Project is the topmost element
        State.__init__(self, state)
        XMLName.__init__(self)
        Identifiable.__init__(self, uuid)
        self._name = SimpleElement(name, "Name", self)
        self._extSchemaSrc = SimpleElement(extSchemaSrc, "ExtensionSchema", self)
        self.topicList = list()

    @property
    def name(self):
        return self._name.value

    @name.setter
    def name(self, newVal):
        self._name.value = newVal

    @property
    def extSchemaSrc(self):
        return self._extSchemaSrc.value

    @extSchemaSrc.setter
    def extSchemaSrc(self, newVal):
        self._extSchemaSrc.value = newVal

    def __eq__(self, other):

        """
        Returns true if every variable member of both classes are the same
        """

        if type(self) != type(other):
            return False

        return self.id == other.id \
            and self.name == other.name \
            and self.extSchemaSrc == other.extSchemaSrc \
            and self.topicList == other.topicList


    def __str__(self):

        ret_str = """Project(
id='{}',
name='{}',
extSchemaSrc='{}',
topicList='{}')""".format(str(self.id),
                str(self.name),
                str(self.extSchemaSrc),
                self.topicList)
        return ret_str
