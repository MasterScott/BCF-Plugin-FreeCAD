"""
Copyright (C) 2019 PODEST Patrick

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
"""

"""
Author: Patrick Podest
Date: 2019-08-16
Github: @podestplatz

**** Description ****
This file provides a lightweight implementation of vectors which is used to
represent Lines, Points, Directions and a ClippingPlane.
"""

import xml.etree.ElementTree as ET
from copy import deepcopy
from bcfplugin.rdwr.interfaces.hierarchy import Hierarchy
from bcfplugin.rdwr.interfaces.state import State
from bcfplugin.rdwr.interfaces.xmlname import XMLName


class ThreeDVector(Hierarchy, State, XMLName):

    """
    General representation of a three dimensional vector which can be
    specialised to a point or a direction vector
    """

    def __init__(self,
            x: float,
            y: float,
            z: float,
            containingElement = None,
            state: State.States = State.States.ORIGINAL,
            xmlName: str = ""):

        Hierarchy.__init__(self, containingElement)
        State.__init__(self, state)
        XMLName.__init__(self, xmlName)
        self.x = x
        self.y = y
        self.z = z


    def __deepcopy__(self, memo):

        """ Create a deepcopy of the object without copying `containingObject`
        """

        cpy = ThreeDVector(deepcopy(self.x, memo), deepcopy(self.y, memo),
                deepcopy(self.z, memo))
        cpy.state = self.state
        return cpy


    def __eq__(self, other):

        """
        Returns true if every variable member of both classes are the same
        """

        return self.x == other.x and self.y == other.y and self.z == other.z


    def getEtElement(self, elem):

        """
        Convert the contents of the object to an xml.etree.ElementTree.Element
        representation. `element` is the object of type xml.e...Tree.Element
        which shall be modified and returned.
        """

        elem.tag = self.xmlName

        xElem = ET.SubElement(elem, "X")
        xElem.text = str(self.x)

        yElem = ET.SubElement(elem, "Y")
        yElem.text = str(self.y)

        zElem = ET.SubElement(elem, "Z")
        zElem.text = str(self.z)

        return elem


class Point(ThreeDVector):

    """ Represents the XML type visinfo.xsd:Point.

    Therefore it represents a point in the three dimensional space
    """

    def __init__(self,
            x: float,
            y: float,
            z: float,
            containingElement = None,
            state: State.States = State.States.ORIGINAL):

        ThreeDVector.__init__(self, x, y, z, containingElement,
                state, self.__class__.__name__)


    def __deepcopy__(self, memo):

        """ Create a deepcopy of the object without copying `containingObject`
        """

        cpy = Point(deepcopy(self.x, memo), deepcopy(self.y, memo),
                deepcopy(self.z, memo))
        cpy.state = self.state
        return cpy


    def getEtElement(self, elem):

        """
        Convert the contents of the object to an xml.etree.ElementTree.Element
        representation. `element` is the object of type xml.e...Tree.Element
        which shall be modified and returned.
        """

        return ThreeDVector.getEtElement(self, elem)


class Direction(ThreeDVector, XMLName):

    """ Represents the XML type visinfo.xsd:Direction.

    Therefore it represents a vector in the three dimensional space
    """

    def __init__(self,
            x: float,
            y: float,
            z: float,
            containingElement = None,
            state: State.States = State.States.ORIGINAL):

        ThreeDVector.__init__(self, x, y, z, containingElement, state)
        XMLName.__init__(self)


    def __deepcopy__(self, memo):

        """ Create a deepcopy of the object without copying `containingObject`
        """

        cpy = Direction(deepcopy(self.x, memo), deepcopy(self.y, memo),
                deepcopy(self.z, memo))
        cpy.state = self.state
        return cpy


    def getEtElement(self, elem):

        """ Convert the contents of the object to an xml.etree.ElementTree.Element
        representation.

        `element` is the object of type xml.e...Tree.Element which shall be
        modified and returned.
        """

        return ThreeDVector.getEtElement(self, elem)


class Line(Hierarchy, State, XMLName):

    """ Represents the XML type visinfo.xsd:Line.

    Represents a line that goes throught the three dimensional space.
    """

    def __init__(self,
            start: Point,
            end: Point,
            containingElement = None,
            state: State.States = State.States.ORIGINAL):

        Hierarchy.__init__(self, containingElement)
        State.__init__(self, state)
        XMLName.__init__(self)
        self.start = start
        self.end = end

        # set containingObject of complex members
        if self.start is not None:
            self.start.containingObject = self
        if self.end is not None:
            self.end.containingObject = self


    def __deepcopy__(self, memo):

        """ Create a deepcopy of the object without copying `containingObject`
        """

        cpystart = deepcopy(self.start, memo)
        cpyend = deepcopy(self.end, memo)

        cpy = Line(cpystart, cpyend)
        cpy.start.containingObject = cpy
        cpy.end.containingObject = cpy
        cpy.state = self.state

        return cpy


    def __eq__(self, other):

        """
        Returns true if every variable member of both classes are the same
        """

        return self.start == other.start and self.end == other.end


    def getEtElement(self, elem):

        """
        Convert the contents of the object to an xml.etree.ElementTree.Element
        representation. `element` is the object of type xml.e...Tree.Element
        which shall be modified and returned.
        """

        elem.tag = self.xmlName

        startElem = ET.SubElement(elem, "StartPoint")
        startElem = self.start.getEtElement(startElem)

        stopElem = ET.SubElement(elem, "StopPoint")
        stopElem = self.stop.getEtElement(stopElem)

        return elem


class ClippingPlane(Hierarchy, State, XMLName):

    """ Represents the XML type visinfo.xsd:ClippingPlane.

    It represents a plane through one or more objects. Everything pointing from
    the plane in `direction` shall be "clipped" away from the object,
    everything else shall be left visible.
    """

    def __init__(self,
            location: Point,
            direction: Direction,
            containingElement = None,
            state: State.States = State.States.ORIGINAL):

        Hierarchy.__init__(self, containingElement)
        State.__init__(self, state)
        XMLName.__init__(self)
        self.location = location
        self.direction = direction

        # set containingObject of complex members
        if self.location is not None:
            self.location.containingObject = self
        if self.direction is not None:
            self.direction.containingObject = self


    def __deepcopy__(self, memo):

        """ Create a deepcopy of the object without copying `containingObject`
        """

        cpylocation = deepcopy(self.location, memo)
        cpydirection = deepcopy(self.direction, memo)

        cpy = ClippingPlane(cpylocation, cpydirection)
        cpy.direction.containingObject = cpy
        cpy.location.containingObject = cpy
        cpy.state = self.state

        return cpy


    def __eq__(self, other):

        """
        Returns true if every variable member of both classes are the same
        """

        return (self.location == other.location and
                self.direction == other.direction)


    def getEtElement(self, elem):

        """
        Convert the contents of the object to an xml.etree.ElementTree.Element
        representation. `element` is the object of type xml.e...Tree.Element
        which shall be modified and returned.
        """

        elem.tag = self.xmlName

        locElem = ET.SubElement(elem, "Location")
        locElem = self.location.getEtElement(locElem)

        dirElem = ET.SubElement(elem, "Direction")
        dirElem = self.direction.getEtElement(dirElem)

