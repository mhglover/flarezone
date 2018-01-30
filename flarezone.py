#!/usr/bin/env python
""" Generate Worlds for the Elysium Flare RPG. """
# pylint: disable=E1101,C0103, R0903, R0902
from __future__ import print_function
from random import randint
import os
import time
import sys
from math import sin, cos, radians, pi
# from pprint import pprint
from flask import Flask
from PIL import Image, ImageDraw, ImageFont
# import itertools
# import bisect
from numpy import random
import yaml
import randomcolor

app = Flask(__name__)

DATAPATH = "data/"  # directory where the YAML files defining the world types live
CANVAS = (1024, 768)  # The size of the final image in pixels.
# We'll work at double the size, then resize to smooth edges.
PLANETS = []  # a corpus of planet names to use for random generation
ZONES = {}  # a data structure of zone names (keys) and YAML-derived definition objects 

fontfile = 'fonts/GL-Nummernschild-Eng.otf'
fontfile = 'fonts/telegrama_render.otf'
zone_label_size = 20
planet_label_size = 18
descrip_label_size = 14

# Read in the list of planets for name generation.
with open(DATAPATH + "planets.txt", "r") as pfile:
    PLANETS = pfile.read().split("\n")

with open(DATAPATH + "planet-suffixes.txt", "r") as sfile:
    SUFFIXES = sfile.read().split("\n")

rand_color = randomcolor.RandomColor()
def getcolor(hue):
    c = rand_color.generate(hue=hue, format_='rgb')[0]
    return c


class ObjectView(object):
    """ Create an object out of a data structure. """
    def __init__(self, d):
        self.__dict__ = d

# Read in the zone definition YAML files
# and create a data structure for zone info:
filenames = [fn for fn in os.listdir(DATAPATH)
             if any(fn.endswith(ext) for ext in "yaml")]
for filename in filenames:
    with open(DATAPATH + filename, 'r') as datafile:
        zone = yaml.load(datafile)
        name = zone['name']
        zoneobject = ObjectView(zone)
        ZONES[name] = zoneobject


class NameGenerator(object):
    """ Build sci-fi planet names. """

    def __init__(self):
        total_syllables = 0

        self.syllables = []

        for p in PLANETS:
            lex = p.split("-")
            total_syllables += len(lex)
            for l in lex:
                if l not in self.syllables:
                    self.syllables.append(l)

        # div_index = len(syllables) / total_syllables
        # div_index_str = str(div_index)[:4]

        self.size = len(self.syllables) + 1
        self.freq = [[0] * self.size for i in range(self.size)]

        for p in PLANETS:
            lex = p.split("-")
            i = 0
            while i < len(lex) - 1:
                self.freq[self.syllables.index(lex[i])][self.syllables.index(lex[i+1])] += 1
                i += 1
            self.freq[self.syllables.index(lex[len(lex) - 1])][self.size-1] += 1

        blanks = [""] * (len(SUFFIXES) + 2)
        self.suffixes = SUFFIXES + blanks

    def genName(self):
        """ Produce a sci-fi name. """
        planet_name = ""
        length = randint(2, 3)
        initial = randint(0, self.size - 2)
        while length > 0:
            while 1 not in self.freq[initial]:
                initial = randint(0, self.size - 2)
            planet_name += self.syllables[initial]
            initial = self.freq[initial].index(1)
            length -= 1
        suffix_index = randint(0, len(self.suffixes) - 1)
        planet_name = planet_name.title()
        if not self.suffixes[suffix_index]:
            planet_name += " " + self.suffixes[suffix_index]
        return planet_name.rstrip()


def point_pos(x0, y0, d):
    """ find a point in a random direction at a given distance """
    theta = randint(1, 361) -1
    theta_rad = pi/2 - radians(theta)
    return x0 + d*cos(theta_rad), y0 + d*sin(theta_rad)

class World(object):
    """ Generate a World object. """

    def __init__(self, worldtype=None, seed=None):
        """ Create the world. """

        # use a seed if it's supplied so we can recreate worlds.
        random.seed(seed)

        # if no world type is given, pick one at random from ZONES
        if worldtype is None:
            z = (randint(1, len(ZONES)) - 1)
            self.type = ZONES.keys()[z]
        else:
            self.type = ZONES[worldtype].name

        self.chartables = ZONES[self.type].characteristics
        self.namer = NameGenerator()
        self.name = self.namer.genName()

        # the dimensions of the final canvas
        xmax, ymax = CANVAS

        # the margins - we don't want a world too close to the edge
        xmargin = int(xmax * .1)
        ymargin = int(ymax * .1)

        # the radius and coordinates of the sphere for this world
        r = randint(int(xmax * .03), int(xmax * .08))
        # x = randint(xmargin + r, xmax - xmargin - r)
        # y = randint(ymargin + r, ymax - ymargin - r)
        x = xmax / 2
        y = ymax / 2

        self.radius = r
        self.coordinates = (x, y)

        # roll up characteristics for this world
        self.genCharacteristics()
        return

    def genCharacteristics(self):
        """ Roll characteristics for a type and add them to the object. """
        chartables = self.chartables
        characteristic_list = chartables.keys()
        self.characteristics = {key: 0 for key in characteristic_list}
        distributions = [
            [4, 1, 0, 0, 0],
            [3, 2, 0, 0, 0],
            [3, 1, 1, 0, 0],
            [2, 2, 1, 0, 0],
            [2, 1, 1, 1, 0],
            [1, 1, 1, 1, 1]
        ]
        distribution = distributions[(randint(1,5) - 1)]
        random.shuffle(distribution)
        self.characteristics = dict(zip(characteristic_list, distribution))

        # for a in xrange(total):
        #     unmaxed = [x for x in self.characteristics.keys() if self.characteristics[x] < 4]
        #     chosen = random.choice(unmaxed)
        #     self.characteristics[chosen] = self.characteristics[chosen] + 1

        for each in self.characteristics:
            cost = self.characteristics[each]
            result = chartables[each][cost]
            self.characteristics[each] = result
            
        # for characteristic in characteristic_list:
        #     table = chartables[characteristic]
        #     roll = randint(1, 100)
        #     rolls = sorted(table.keys())
        #     nearest_index = bisect.bisect_left(rolls, roll)
        #     value = table[rolls[nearest_index]]
        #     self.characteristics[characteristic] = value

    def getWorld(self):
        """ Print all the details about this world. """
        output = "%s\n" % self.name
        # output += "Generated World - %s ---------------------------\n" % self.type.title()
        output += "%s" % self.getCharacteristics()
        # output += "Coordinates: (%s, %s)\n" % (self.coordinates[0], self.coordinates[1])
        # output += "Size: [%s]\n" % (self.radius * 2)
        return output

    def getCharacteristics(self):
        """ Print the characteristics of this world. """
        output = ""
        for key in sorted(self.characteristics):
            if "proximity" not in key:
                output += "%s - %s\n" % (key.title(), self.characteristics[key])
        return output


class Zone(object):
    """ Represents a zone generated for Elysium Flare. """

    def __init__(self,
                 zonetype=None):

        # pick a zonetype randomly if we weren't given one
        if zonetype is None:
            z = (randint(1, len(ZONES)) - 1)
            self.type = ZONES.keys()[z]
        else:
            self.type = ZONES[zonetype].name

        # TODO - we're creating a name generator for the zone
        # and another for each world - overkill
        self.namer = NameGenerator()
        self.zonename = self.namer.genName()

        # note the other zones we border
        self.borders = ZONES[self.type].borders

        # generate our zone capital
        self.capital = World(worldtype=zonetype)

        self.capital.color = getcolor('blue')

        # generate the other worlds in the zone
        p = self.capital.characteristics['proximity']

        self.veryclose = []
        for a in xrange(p[0]):
            w = World(worldtype=zonetype)
            w.coordinates = point_pos(w.coordinates[0],
                                      w.coordinates[1],
                                      self.capital.radius + w.radius)
            w.color = getcolor("green")
            self.veryclose.append(w)

        self.close = []
        for a in xrange(p[1]):
            w = World(worldtype=zonetype)
            w.coordinates = point_pos(w.coordinates[0],
                                      w.coordinates[1],
                                      self.capital.radius + w.radius + randint(150, 250))
            w.color = getcolor("red")
            self.close.append(w)

        self.distant = []
        for a in xrange(p[2]):
            self.distant.append((self.type, 
                                 self.namer.genName(),
                                 randint(1, 361) - 1))

        self.far = []
        for a in xrange(p[3]):
            self.far.append((random.choice(self.borders),
                             self.namer.genName(),
                             randint(1, 361) - 1))

    def getNeighbors(self):
        """ Return text describing the neighboring worlds and zones. """
        output = ""

        for z in self.veryclose:
            # output += "Very Close World -----------\n"
            output += z.getWorld()
            output += "\n"

        for z in self.close:
            # output += "Close World ----------------\n"
            output += z.getWorld()
            output += "\n"

        for z in self.distant:
            output += "Distant %s Sector - %s\n\n" % (z[0].title(), z[1])

        for z in self.far:
            output += "Far - %s:%s\n\n" % (z[0].title(), z[1])

        return output

    def drawWorld(self, world, image):
        """ Draw and label a world on the zone image. """
        x, y = world.coordinates
        r = world.radius
        ul = (x-r, y-r)
        lr = (x+r, y+r)
        box = (ul, lr)
        d = ImageDraw.Draw(image)
        color = world.color
        d.ellipse(box, fill=color, outline=color)

    def drawName(self, image, world):
        fnt = ImageFont.truetype(fontfile, planet_label_size)
        d = ImageDraw.Draw(image)
        d.text((world.coordinates[0], world.coordinates[1] + world.radius + (planet_label_size * .5)),
               world.name,
               font=fnt,
               fill=(0, 0, 0, 128))

    def drawZone(self, text):
        """ Render an image with all the worlds in the zone. """
        background = (240, 240, 240)
        zoneimage = Image.new('RGB', CANVAS, background)
        d = ImageDraw.Draw(zoneimage)

        # draw the close links
        for w in self.veryclose + self.close:
            d.line((self.capital.coordinates, w.coordinates),
                    fill=(0, 0, 0), width=2)

        # draw the far and distant links
        for w in self.distant + self.far:
            angle = randint(1, 361) - 1
            x, y = self.capital.coordinates
            destination = point_pos(x, y, CANVAS[0])
            print("Destination: %s,%s" % destination)
            d.line((self.capital.coordinates, destination),
                    fill=(0, 0, 0), width=2)

        # draw the worlds
        for w in [self.capital] + self.veryclose + self.close:
            self.drawWorld(world=w, image=zoneimage)

        # draw the labels
        for w in [self.capital] + self.veryclose + self.close:
            self.drawName(world=w, image=zoneimage)

        fnt = ImageFont.truetype(fontfile, descrip_label_size)
        d.text((0,0),
                text,
                font=fnt,
                fill=(0, 0, 0, 255))

        out = zoneimage.resize((1024, 760), resample=1)
        out.save("static/%s.jpg" % self.zonename)


@app.route('/')
def serveZone():
    """ Default endpoint - generate text defining a zone and the worlds in it."""
    zone = Zone()
    capital = zone.capital
    text = "%s\n" % capital.getWorld()
    text += zone.getNeighbors()
    print(text)
    zone.drawZone(text)

    output = "<html><body>\n"
    output += "<img src='static/%s.jpg'>\n" % zone.zonename
    output += "</body></html>\n"
    return output

    # remove image files older than five minutes
    path = "static"
    now = time.time()
    for f in os.listdir(path):
        if os.stat(f).st_mtime < now - 300:
            if os.path.isfile(f):
                os.remove(os.path.join(path, f))

if __name__ == '__main__':
    app.run(debug=True, host='::')