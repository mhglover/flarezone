#!/usr/bin/env python
""" Generate Worlds for the Elysium Flare RPG. """
# pylint: disable=E1101,C0103, R0903, R0902
from __future__ import print_function
from random import randint
# from os import walk
# from pprint import pprint
import itertools
import bisect
from numpy import random
import yaml
from flask import Flask
app = Flask(__name__)

# directory where the YAML files defining the world types live
DATAPATH = "./data"

class ObjectView(object):
    """ Create an object out of a data structure. """
    def __init__(self, d):
        self.__dict__ = d

class Zone(object):
    """ Represents a world generated for Elysium Flare. """

    # the worldtypes are the different types of worlds we can create

    def __init__(self,
                 worldtype,
                 links=True,
                 link_count=-1):
        """ Read in the data files for the regions. """

        _datafile = "%s/%s.yaml" % (DATAPATH, worldtype)
        with open(_datafile, 'r') as datafile:
            self.worldtype = ObjectView(yaml.load(datafile))
        
        _planets = "%s/%s" % (DATAPATH, "planets.txt")
        with open(_planets, "r") as datafile:
            _raw = datafile.read()
        self.planets = _raw.split("\n")

        # what kind of zone is this?
        self.type = self.worldtype.name
        self.zonename = self.genName()
        self.name = self.genName()

        # roll up characteristics for this world
        self.characteristic_list = sorted(self.worldtype.characteristics.keys())
        self.characteristics = {}
        self.genCharacteristics()

        if link_count == -1:
            # if we don't specify a number of links, generate it
            self.link_count = int(random.exponential(scale=1)) + 4
        else:
            # if we specify a number of links, use that
            self.link_count = link_count

        if links:
            # generate a number of additional planets linked to this one
            self.genLinks()

    def genCharacteristics(self):
        """ Roll characteristics for a type and add them to the object. """
        self.characteristic_list = sorted(self.worldtype.characteristics.keys())

        for _characteristic in self.characteristic_list:
            _roll = randint(1, 100)
            _rolls = sorted(self.worldtype.characteristics[_characteristic].keys())
            _nearest = bisect.bisect_left(_rolls, _roll)
            _value = self.worldtype.characteristics[_characteristic][_rolls[_nearest]]
            self.characteristics[_characteristic] = _value

    def genName(self):
        """ Return a generated planet name. """
        total_syllables = 0

        syllables = []
        planets = self.planets

        for p in planets:
            lex = p.split("-")
            total_syllables += len(lex)
            for l in lex:
                if l not in syllables:
                    syllables.append(l)

        # div_index = len(syllables) / total_syllables
        # div_index_str = str(div_index)[:4]

        size = len(syllables) + 1
        freq = [[0] * size for i in range(size)]

        for p in planets:
            lex = p.split("-")
            i = 0
            while i < len(lex) - 1:
                freq[syllables.index(lex[i])][syllables.index(lex[i+1])] += 1
                i += 1
            freq[syllables.index(lex[len(lex) - 1])][size-1] += 1

        planet_name = ""
        suffixes = ["Prime", "",
                    "Alpha", "",
                    'Proxima', "",
                    "B", "",
                    "C", "",
                    "D", "",
                    "III", "",
                    "IV", "",
                    "V", "",
                    "VI", "",
                    "VII", "",
                    "VIII", "",
                    "IX", ""
                    "X", "",
                    "", ""]

        length = randint(2, 3)
        initial = randint(0, size - 2)
        while length > 0:
            while 1 not in freq[initial]:
                initial = randint(0, size - 2)
            planet_name += syllables[initial]
            initial = freq[initial].index(1)
            length -= 1
        suffix_index = randint(0, len(suffixes) - 1)
        planet_name = planet_name.title()
        if not suffixes[suffix_index]:
            planet_name += " " + suffixes[suffix_index]
        return planet_name

    def getCharacteristics(self):
        """ Print the characteristics of this world. """
        output = ""
        for key in sorted(self.characteristics):
            output += "%s - %s\n" % (key.title(), self.characteristics[key])
        return output

    def genLinks(self):
        """ Generate the linked worlds for this world. """
        self.links = []
        for _ in itertools.repeat(None, self.link_count):
            link = Zone(self.type, links=False)
            # print("%s link count: %s" % (link.name, link.link_count))
            self.links.append(link)

    def getLinks(self):
        """ Print the linked worlds defined for this one. """
        output = ""
        for link in self.links:
            output += "%s\n" % link.name
            output += "Linked World - %s ---------------------------\n" % self.type.title()
            output += "%s\n" % link.getCharacteristics()
            output += "\n"
            # when we print a count of linked worlds' forward links, we print
            # one fewer because it's also linked to the generated world.
            # link.printLinkCount(fewer=1)
        return output

    def getLinkCount(self, fewer=0):
        """ Print the count of links from this world. """
        # if we need to subtract a number of links to account for the
        # incoming links from a generated world, we can use 'fewer'
        if fewer > 0:
            output = "Ongoing Links: %s\n" % (int(self.link_count) - fewer)
        else:
            output = "Total Links: %s\n" % (int(self.link_count))
        return output

    def getWorld(self):
        """ Print all the details about this world. """
        output = "%s\n" % self.name
        output += "Generated World - %s ---------------------------\n" % self.type.title()
        output += "%s\n" % self.getCharacteristics()
        output += "%s\n" % self.getLinkCount()
        return output


@app.route('/')
def serveZone():
    myzone = Zone('hub')
    output = "<html><body><pre>\n"
    output += "Zone Name: %s\n" % myzone.zonename 
    output += "%s\n" % myzone.getWorld()
    output += "%s\n" % myzone.getLinks()
    output += "</pre></body></html>\n"
    return output
