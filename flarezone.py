#!/usr/bin/env python
""" Generate Zone charts for the Elysium Flare RPG. """
# pylint: disable=invalid-name, too-many-locals, too-few-public-methods, too-many-instance-attributes
from __future__ import print_function
import random
import os
import time
from math import sin, cos, radians, degrees, sqrt, asin, atan2
from pprint import pprint
from flask import Flask, render_template, redirect, url_for
from PIL import Image, ImageDraw, ImageFont, ImageOps
from numpy import random
import yaml
import randomcolor
from networkx import Graph, draw_networkx
import networkx as nx
import matplotlib.pyplot as plt

app = Flask(__name__)

class ObjectView(object):
    """ Create an object out of a data structure. """
    def __init__(self, d):
        self.__dict__ = d

datapath = "data/"  # directory where the YAML files defining the world types live
planets = []  # a corpus of planet names to use for random generation
suffixes = [] # a list of planetary suffixes
zones = {}  # a data structure of zone names (keys) and YAML-derived definition objects

canvas = (2048, 1536)  # The size of the final image in pixels.
# We'll work at a large size, then resize to smooth edges.
shrink = 3

# fontfile = 'fonts/GL-Nummernschild-Eng.otf'
# fontfile = 'fonts/telegrama_render.otf'
# fontfile = 'fonts/TextMeOne-Regular.ttf'
fontfile = 'fonts/Crushed-Regular.ttf'
fontname = "Crushed"
zone_label_size = 128
planet_label_size = 50
# descrip_label_size = 28
planet_min = 40
planet_max = 80

# remove image files older than a certain time
timeout = 60 * 5 # five minutes
# timeout = 60 * 60 * 24 # one day

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

class NameGenerator(object):
    """ Build sci-fi planet names.
    
    :param planetnames - a list of planet names read from a file
    :param suffixnames - a list of suffixnames read from a file
    :param zonename - a zone name to ensure we don't duplicate it with a planet name
    
    :method genName(suffix=True/False)

    :returns - a NameGenerator object"""

    def __init__(self, planetnames, suffixnames, zonename=''):
        total_syllables = 0

        self.generatednames = []
        self.syllables = []

        self.zonename = zonename

        for p in planetnames:
            lex = p.split("-")
            total_syllables += len(lex)
            for l in lex:
                if l not in self.syllables:
                    self.syllables.append(l)

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
        length = random.randint(2, 3)
        initial = random.randint(0, self.size - 2)
        while length > 0:
            while 1 not in self.freq[initial]:
                initial = random.randint(0, self.size - 2)
            planet_name += self.syllables[initial]
            initial = self.freq[initial].index(1)
            length -= 1
        suffix_index = random.randint(0, len(self.suffixes) - 1)
        planet_name = planet_name.title()
        if self.suffixes[suffix_index] and suffix:
            planet_name += " " + self.suffixes[suffix_index]
        planet_name = planet_name.rstrip()
        self.generatednames.append(planet_name)
        return planet_name

class Sector(Graph):
    """ Represents a set of interconnected star systems. """

    def __init__(self,
                 data=None,
                 file=None,
                 region=None,
                 name='',
                 seed=None,
                 **attr):
        Graph.__init__(self, data=data, name=name, **attr)
        region = region.lower()
        name = name.lower()

        self.name = name
        self.region = region
        self.chartables = zones[region].characteristics
        self.namer = NameGenerator(planets, suffixes, zonename=name)
        self.colorist = randomcolor.RandomColor(seed=seed)

        # generate the capital world
        self.genWorld()

        # generate the worlds linked from the capital world
        self.genWorlds()

        # generate second order worlds
        self.genWorlds()

        # print("Sector - %s:%s" % (self.region, self.name))
        
        if "distant" in [i[1] for i in self.nodes(data="distance")]:
            self.distant = True
        else:
            self.distant = False
        
        if "far" in [i[1] for i in self.nodes(data="distance")]:
            self.far = True
        else:
            self.far = False

        iterations = 150
        pos = nx.spring_layout(self,
                               k=.5,
                               iterations=iterations,
                               center=[1, 1],
                               weight='weight')

        labels = {key:self.node[key]['label'] for key in self.nodes().keys()}
        for world in pos:
            x, y = pos[world]
            self.node[world]['x'] = x * (canvas[0] / 2 - 150) + 75
            self.node[world]['y'] = y * (canvas[1] / 2 - 150) + 75
            pos[world] = (x, y)

        for world in pos:
            if "far" in self.node[world]['distance'] or "distant" in self.node[world]['distance']:
                origin_world = self.adj[world].keys()[0]
                # print(world, origin_world)
                coords = [self.node[world]['x'],
                          self.node[world]['y']]
                origin = [self.node[origin_world]['x'],
                          self.node[origin_world]['y']]
                
                # print(coords, origin)

        # draw_networkx(self, pos, labels=labels)
        # plt.savefig("static/plot-%s.jpg" % self.name, dpi=1000)
        # plt.close()
        return

    def genWorlds(self):
        distances = ['veryclose', 'close', 'far', 'distant']

        for (world, data) in self.nodes(data=True):
            if data['linked'] is False:
                prox = data['characteristics']['proximity']
                for distance in xrange(len(distances)):
                    for _ in xrange(prox[distance]):
                        self.genWorld(anchor=world, distance=distances[distance])
                self.node(world).linked = True

        return

    def genWorld(self, anchor=None, distance=''):
        """ Create a world and its characteristics.
        Adds a node and edges to the graph, and attributes to the node.

        :param anchor - The name of the world connected to this one.
        :param distance - The length of the jump from the anchor world.

        :attribute name - The name of the world (string).
        :attribute region - The region this world is in (string).
        :attribute characteristics - A dictionary of details about the world.

        :returns string - The name of the generated world.
        """

        if len(self.nodes) > 16:
            return

        linked = False

        if "far" in distance:
            region = random.choice(zones[self.region].borders)
        else:
            region = self.region

        if "far" in distance or "distant" in distance:
            name = self.namer.genName(suffix=False)
            label = "%s:%s" % (region.title(), name)
            linked = True
        else:
            name = self.namer.genName()
            label = name

        characteristics = {}
        characteristic_list = self.chartables.keys()
        self.characteristics = {key: 0 for key in characteristic_list}
        distributions = [
            [4, 1, 0, 0, 0],
            [3, 2, 0, 0, 0],
            [3, 1, 1, 0, 0],
            [2, 2, 1, 0, 0],
            [2, 1, 1, 1, 0],
            [1, 1, 1, 1, 1]
        ]
        distribution = distributions[(random.randint(1, 5) - 1)]
        random.shuffle(distribution)
        characteristics = dict(zip(characteristic_list, distribution))

        for each in characteristics:
            cost = characteristics[each]
            result = self.chartables[each][cost]
            characteristics[each] = result

        radius = random.randint(planet_min, planet_max)

        if "veryclose" in distance:
            weight = 10
            color = "red"
        elif "close" in distance:
            weight = 3
            color = "blue"
        elif "far" in distance:
            weight = 1
            color = "green"
        elif "distant" in distance:
            weight = 1
            color = "orange"
        else:
            weight = 1
            color = "black"

        color = getcolor(region, self.colorist)
        # print(anchor, name, region, distance, color)

        self.add_node(name,
                      region=region,
                      characteristics=characteristics,
                      linked=linked,
                      label=label,
                      distance=distance,
                      radius=radius,
                      color=color)
        if anchor is not None:
            self.add_edge(anchor,
                            name,
                            distance=distance,
                            weight=weight)
        return name

def theta_point(coordinates, distance, theta):
    """ generate a new point at a given distance and angle

    :param coordinates: 2-tuple, origin point in (x, y) format
    :param distance: int, distance in pixels to new point
    :param theta: int 0-360, angle to new point

    :returns 2-tuple of new point coordinates
    """
    x, y = coordinates
    theta_rad = radians(theta)
    return cos(theta_rad) * distance + x, sin(theta_rad) * distance + y

def findtan(point, circ):
    """ find the angle of the tangent of a line from a point to a circle

    :param point: 2-tuple, origin point in (x, y) format
    :param circ: 3-tuple, (x, y, radius)

    : returns angle in degrees between the line from point to center and the
    tangent line
    """
    x1, y1 = point
    x2, y2, radius = circ
    hypotenuse = sqrt((x2 - x1)**2 + (y2 - y1)**2)
    return degrees(asin(radius/hypotenuse))

def getcolor(hue, rand_color):
    """ Generate a random color from a base hue and return an rgb value. """
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

def drawLabel(image, link):
    """ Draw a label at a given location.

    :param image - an image object from Pillow
    :param location - 2-tuple, (x, y) coordinates
    :param text - string, words to put on the image

    :returns nothing
    """
    capx, capy = (canvas[0] / 2, canvas[1] / 2)
    distance = canvas[1] / 2.2
    heading = link[2]
    location = theta_point((capx, capy), distance, heading)
    label = "%s:%s" % (link[0].title(), link[1])

    fnt = ImageFont.truetype(fontfile, planet_label_size)
    d = ImageDraw.Draw(image)
    d.text(location,
           label,
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

def drawSector(s):
    """ Render an image with all the worlds in the sector. """
    background = (240, 240, 240)
    image = Image.new('RGB', canvas, background)
    d = ImageDraw.Draw(image)
    fnt = ImageFont.truetype(fontfile, planet_label_size)
    
    jumps = {}
    for edge in s.edges():
        a, b = edge
        # draw the out-sector jumps
        
        if "close" not in s[a][b]['distance']:
            if ":" not in s.node[a]['label']:
                anchor = a
                link = b
            else:
                anchor = b
                link = a
            label = s.node[link]['label']
            
            x1 = s.node[link]['x']
            x2 = s.node[anchor]['x']
            y1 = s.node[link]['y']
            y2 = s.node[anchor]['y']
            angle = degrees(atan2(y1 - y2, x1 - x2))
            s[a][b]['angle'] = angle
            pos = theta_point((x2, y2), canvas[0], angle)
            labpos = theta_point((x2, y2), canvas[0]/4, angle)
            s.node[link]['x'] = pos[0]
            s.node[link]['y'] = pos[1]
            print(label, labpos)
            jumps[label] = labpos

    # draw the edges
    for edge in s.edges():
        a, b = edge
        distance =  s[a][b]['distance']
        if "veryclose" in distance:
            color = "red"
        elif "close" in distance:
            color = "blue"
        elif "far" in distance:
            color = "black"
        elif "distant" in distance:
            color = "black"
        else:
            color = "black"
        
        x1 = s.node[a]['x']
        y1 = s.node[a]['y']
        x2 = s.node[b]['x']
        y2 = s.node[b]['y']
        d.line((x1, y1, x2, y2),
                fill=color,
                width=2)
    
    # draw the worlds
    for node, data in s.nodes(data=True):
        if "far" not in data['distance'] and \
            "distant" not in data['distance']:
            x = data['x']
            y = data['y']
            r = data['radius']
            c = data['color']
            ul = (x-r, y-r)
            lr = (x+r, y+r)
            box = (ul, lr)
            d.ellipse(box, fill=c, outline=c)

    # draw the labels for the worlds
    for node, data in s.nodes(data=True):
        if "far" not in data['distance'] and \
            "distant" not in data['distance']:
            r = data['radius']
            if data['x'] < canvas[0] / 2:
                x = data['x'] - fnt.getsize(node)[0]
            else:
                x = data['x']
            y = data['y'] + r
            d.text((x, y),
                node,
                font=fnt,
                fill="black")

    for j in jumps:
        d.text(jumps[j], j, font=fnt, fill="black")

    out = image.resize((canvas[0]/shrink, canvas[1]/shrink), resample=1)
    out.save("static/%s.jpg" % s.name)
    return

def drawZone(thiszone):
    """ Render an image with all the worlds in the thiszone. """
    background = (240, 240, 240)
    zoneimage = Image.new('RGB', canvas, background)
    d = ImageDraw.Draw(zoneimage)

    capx, capy = thiszone.capital.coordinates

    # draw the close links
    for w in thiszone.veryclose + thiszone.close:
        d.line((thiszone.capital.coordinates, w.coordinates),
               fill=(0, 0, 0), width=2)

    # draw the far and distant links
    for w in thiszone.distant + thiszone.far:
        a = w[2]
        # by using the width of the canvas as the distance, we
        # ensure that the line will run off the edge.  lazy.
        destination = theta_point((capx, capy), canvas[0], a)
        d.line((thiszone.capital.coordinates, destination),
               fill=(0, 0, 0), width=2)

    # draw the worlds
    for w in [thiszone.capital] + thiszone.veryclose + thiszone.close:
        drawWorld(world=w, image=zoneimage)

    # draw the labels for worlds
    for w in [thiszone.capital] + thiszone.veryclose + thiszone.close:
        drawName(world=w, image=zoneimage)

    # draw the labels for outgoing links
    for link in thiszone.distant + thiszone.far:
        drawLabel(zoneimage, link)

    # draw the zone label
    label = "%s:%s" % (thiszone.region.title(), thiszone.zonename)
    fnt = ImageFont.truetype(fontfile, zone_label_size)
    d.text((0, 0),
           label,
           font=fnt,
           fill=(0, 0, 0, 255))

    out = zoneimage.resize((canvas[0]/shrink, canvas[1]/shrink), resample=1)
    out.save("static/%s.jpg" % thiszone.zonename)

def wordstoseed(words):
    """ convert a list of words into an integer """
    # concatenate the letters, convert them to numbers
    s = int(''.join([str(ord(char) - 96) for char in ''.join(words).lower()]))
    # Random seeds have to be less than 2^32-1
    # so we cut it down until it fits. Dividing by seven seems to give good
    # "randomness".
    while s > (2**32 - 1):
        s = str(s)[1:]
        s = int(s)/7
    return s

def cleanup():
    """ Remove old image files. """
    path = "static"
    now = time.time()
    for f in os.listdir(path):
        ff = os.path.join(path, f)
        if os.stat(ff).st_mtime < now - timeout:
            if os.path.isfile(ff) and "jpg" in f:
                os.remove(ff)

@app.route('/region/<region>/<zonename>/')
def zonemaker(region, zonename):
    """ Default endpoint - generate text defining a zone and the worlds in it."""
    cleanup()

    if region is None:
        region = random.choice(zones.keys()).lower()
    else:
        region = region.lower()

    if zonename is None:
        zonenamer = NameGenerator(planets, suffixes)
        zonename = zonenamer.genName(suffix=False).title()
    else:
        zonename = zonename.title()

    seed = wordstoseed([region, zonename])
    random.seed(seed)

    sector = Sector(region=region, name=zonename, seed=seed)
    drawSector(sector)
    # text = "%s\n" % capital.getWorld()
    # text += myzone.getNeighbors()

    # drawZone(myzone)
    # image = myzone.zonename + ".jpg"

    image = sector.name + ".jpg"
    return render_template('sector.html',
                           image=image,
                           font="Crushed",
                           sector=sector
                          )

@app.route('/region/<region>/')
@app.route('/')
def zonefinder(region=None):
    random.seed()
    if region is None:
        region = random.choice(zones.keys()).lower()
    else:
        region = region.lower()

    zonenamer = NameGenerator(planets, suffixes)
    zonename = zonenamer.genName(suffix=False).title()

    return redirect(url_for('zonemaker', region=region.title(), zonename=zonename.title()))

if __name__ == '__main__':
    cleanup()
    app.run(debug=True, host='::')
    # app.run(host='::')
