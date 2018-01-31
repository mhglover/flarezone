#!/usr/bin/env python
""" Generate Worlds for the Elysium Flare RPG. """
# pylint: disable=E1101,C0103, R0903, R0902
from __future__ import print_function
from random import randint
import os
import time
from math import sin, cos, radians, pi
# from pprint import pprint
from flask import Flask
from PIL import Image, ImageDraw, ImageFont
from numpy import random
import yaml
import randomcolor

app = Flask(__name__)

def getcolor(hue):
    """ Generate a random color from a base hue and return an rgb value. """
    rand_color = randomcolor.RandomColor()
    c = rand_color.generate(hue=hue, format_='rgb')[0]
    return c


def drawName(image, world):
    """ Draw the name of this world on the zone image. """
    fnt = ImageFont.truetype(fontfile, planet_label_size)
    d = ImageDraw.Draw(image)
    d.text((world.coordinates[0],
            world.coordinates[1] + world.radius + (planet_label_size * .5)
           ),
           world.name,
           font=fnt,
           fill=(0, 0, 0, 128))


def drawWorld(world, image):
    """ Draw and label a world on the zone image. """
    x, y = world.coordinates
    r = world.radius
    ul = (x-r, y-r)
    lr = (x+r, y+r)
    box = (ul, lr)
    d = ImageDraw.Draw(image)
    color = world.color
    d.ellipse(box, fill=color, outline=color)


class ObjectView(object):
    """ Create an object out of a data structure. """
    def __init__(self, d):
        self.__dict__ = d


class NameGenerator(object):
    """ Build sci-fi planet names. """

    def __init__(self, planetnames, suffixnames):
        total_syllables = 0

        self.syllables = []

        for p in planetnames:
            lex = p.split("-")
            total_syllables += len(lex)
            for l in lex:
                if l not in self.syllables:
                    self.syllables.append(l)

        # div_index = len(syllables) / total_syllables
        # div_index_str = str(div_index)[:4]

        self.size = len(self.syllables) + 1
        self.freq = [[0] * self.size for i in range(self.size)]

        for p in planets:
            lex = p.split("-")
            i = 0
            while i < len(lex) - 1:
                self.freq[self.syllables.index(lex[i])][self.syllables.index(lex[i+1])] += 1
                i += 1
            self.freq[self.syllables.index(lex[len(lex) - 1])][self.size-1] += 1

        blanks = [""] * (len(suffixnames) + 2)
        self.suffixes = suffixnames + blanks

    def genName(self, suffix=True):
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
        if self.suffixes[suffix_index] and suffix:
            planet_name += " " + self.suffixes[suffix_index]
        return planet_name.rstrip()


def point_pos(x0, y0, d):
    """ find a point in a random direction at a given distance """
    theta = randint(1, 361) -1
    theta_rad = pi/2 - radians(theta)
    return x0 + d*cos(theta_rad), y0 + d*sin(theta_rad)

class World(object):
    """ Generate a World object. """

    def __init__(self, namer, worldtype=None):
        """ Create the world. """

        # if no world type is given, pick one at random from zones
        if worldtype is None:
            z = (randint(1, len(zones)) - 1)
            self.type = zones.keys()[z]
        else:
            self.type = zones[worldtype].name

        self.chartables = zones[self.type].characteristics
        self.name = namer.genName()

        # the dimensions of the final canvas
        xmax, ymax = canvas

        # the margins - we don't want a world too close to the edge
        # xmargin = int(xmax * .1)
        # ymargin = int(ymax * .1)

        # the radius for the world
        r = randint(int(xmax * .03), int(xmax * .08))

        # coordinates of the sphere for this world
        # we place every world at the center of the map
        # and for linked worlds, we change that to be
        # relative to the capital world
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
        distribution = distributions[(randint(1, 5) - 1)]
        random.shuffle(distribution)
        self.characteristics = dict(zip(characteristic_list, distribution))

        for each in self.characteristics:
            cost = self.characteristics[each]
            result = chartables[each][cost]
            self.characteristics[each] = result

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
                 namer,
                 zonetype=None):

        # pick a zonetype randomly if we weren't given one
        if zonetype is None:
            z = (randint(1, len(zones)) - 1)
            self.type = zones.keys()[z]
        else:
            self.type = zones[zonetype].name

        self.zonename = namer.genName(suffix=False)

        # note the other zones we border
        self.borders = zones[self.type].borders

        # generate our zone capital
        self.capital = World(namer, worldtype=zonetype)

        self.capital.color = getcolor('blue')

        # generate the other worlds in the zone
        p = self.capital.characteristics['proximity']

        self.veryclose = []
        for _ in xrange(p[0]):
            w = World(namer, worldtype=zonetype)
            w.coordinates = point_pos(w.coordinates[0],
                                      w.coordinates[1],
                                      self.capital.radius + w.radius)
            w.color = getcolor("green")
            self.veryclose.append(w)

        self.close = []
        for _ in xrange(p[1]):
            w = World(namer, worldtype=zonetype)
            w.coordinates = point_pos(w.coordinates[0],
                                      w.coordinates[1],
                                      self.capital.radius + w.radius + randint(150, 250))
            w.color = getcolor("red")
            self.close.append(w)

        self.distant = []
        for _ in xrange(p[2]):
            self.distant.append((self.type,
                                 namer.genName(suffix=False),
                                 randint(1, 361) - 1))

        self.far = []
        for _ in xrange(p[3]):
            self.far.append((random.choice(self.borders),
                             namer.genName(suffix=False),
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

def drawZone(thiszone, text):
    """ Render an image with all the worlds in the thiszone. """
    background = (240, 240, 240)
    zoneimage = Image.new('RGB', canvas, background)
    d = ImageDraw.Draw(zoneimage)

    # draw the close links
    for w in thiszone.veryclose + thiszone.close:
        d.line((thiszone.capital.coordinates, w.coordinates),
               fill=(0, 0, 0), width=2)

    # draw the far and distant links
    for w in thiszone.distant + thiszone.far:
        # angle = randint(1, 361) - 1
        # point_pos picks a random angle
        x, y = thiszone.capital.coordinates
        destination = point_pos(x, y, canvas[0])
        print("Destination: %s,%s" % destination)
        d.line((thiszone.capital.coordinates, destination),
               fill=(0, 0, 0), width=2)

    # draw the worlds
    for w in [thiszone.capital] + thiszone.veryclose + thiszone.close:
        drawWorld(world=w, image=zoneimage)

    # draw the labels
    for w in [thiszone.capital] + thiszone.veryclose + thiszone.close:
        drawName(world=w, image=zoneimage)

    # draw the world descriptions
    fnt = ImageFont.truetype(fontfile, descrip_label_size)
    # text = textwrap.wrap(text, 40)
    # text = '\n'.join(text)
    d.text((0, 0),
           text,
           font=fnt,
           fill=(0, 0, 0, 255))

    # draw the zone label
    label = "%s:%s" % (thiszone.type.title(), thiszone.zonename)
    fnt = ImageFont.truetype(fontfile, zone_label_size)
    d.text((0, canvas[1] - zone_label_size),
           label,
           font=fnt,
           fill=(0, 0, 0, 255))

    out = zoneimage.resize((1024, 768), resample=1)
    out.save("static/%s.jpg" % thiszone.zonename)


@app.route('/')
def serveZone():
    """ Default endpoint - generate text defining a zone and the worlds in it."""
    mynamer = NameGenerator(planets, suffixes)
    myzone = Zone(mynamer)
    capital = myzone.capital
    text = "%s\n" % capital.getWorld()
    text += myzone.getNeighbors()
    drawZone(myzone, text)

    output = "<html><body>\n"
    output += "<img src='static/%s.jpg'\n" % myzone.zonename
    output += "alt=\"%s\">\n" % text
    output += "</body></html>\n"

    # remove image files older than five minutes
    path = "static"
    now = time.time()
    for f in os.listdir(path):
        ff = os.path.join(path, f)
        if os.stat(ff).st_mtime < now - 300:
            if os.path.isfile(ff):
                os.remove(ff)
    return output

if __name__ == '__main__':
    datapath = "data/"  # directory where the YAML files defining the world types live
    planets = []  # a corpus of planet names to use for random generation
    suffixes = [] # a list of planetary suffixes
    zones = {}  # a data structure of zone names (keys) and YAML-derived definition objects

    # Read in the zone definition YAML files
    # and create a data structure for zone info:
    filenames = [fn for fn in os.listdir(datapath)
                 if any(fn.endswith(ext) for ext in "yaml")]
    for filename in filenames:
        with open(datapath + filename, 'r') as datafile:
            zone = yaml.load(datafile)
            name = zone['name']
            zoneobject = ObjectView(zone)
            zones[name] = zoneobject

    # Read in the list of planets for name generation.
    with open(datapath + "planets.txt", "r") as pfile:
        planets = pfile.read().split("\n")

    with open(datapath + "planet-suffixes.txt", "r") as sfile:
        suffixes = sfile.read().split("\n")

    canvas = (2048, 1536)  # The size of the final image in pixels.
    # We'll work at double the size, then resize to smooth edges.

    fontfile = 'fonts/GL-Nummernschild-Eng.otf'
    fontfile = 'fonts/telegrama_render.otf'
    zone_label_size = 64
    planet_label_size = 36
    descrip_label_size = 28

    app.run(debug=True, host='::')
