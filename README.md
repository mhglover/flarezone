# FlareZone

A simple sci-fi zone generator for the Elysium Flare RPG by Brad Murray (https://www.patreon.com/halfjack).  You can see this running at http://binary-systems.net.

<!-- ## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system. -->

<!-- ### Prerequisites

What things you need to install the software and how to install them

```
Give examples
``` -->

### Installing

Pull down the source, create a virtual environment, active the virtualenv, and install the requirements.

```
git clone https://github.com/mhglover/flarezone.git
cd flarezone
virtualenv env
source env/bin/activate
pip install -r requirements.txt
```

### Running

#### Flask
You can develop locally by running in Flask in debug mode. Debug mode will automatically reload the application upon changes to the source.
```
export FLASK_APP=flarezone.py
export FLASK_DEBUG=1
python -m flask run
```

Browse to http://localhost:5000

#### Passenger

We're using Passenger at Dreamhost for running at binary-systems.net. If you've got Passenger installed, you can run it with:
```
passenger start
```


<!-- ## Running the tests

Explain how to run the automated tests for this system

### Break down into end to end tests

Explain what these tests test and why

```
Give an example
```

### And coding style tests

Explain what these tests test and why

```
Give an example
``` -->

<!-- ## Deployment

Add additional notes about how to deploy this on a live system -->

## Built With

* Python
* [Flask](http://flask.pocoo.org/docs/0.12/quickstart/)
* [Passenger](https://www.phusionpassenger.com/library/walkthroughs/start/python.html)

<!-- ## Contributing

Please read [CONTRIBUTING.md](https://gist.github.com/PurpleBooth/b24679402957c63ec426) for details on our code of conduct, and the process for submitting pull requests to us. -->

<!-- ## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/your/project/tags).  -->

## Data Files

Each zone type (Hub, Rim, Gulf, and each Arm) should have a YAML file in the _data_ directory to define the characteristics to be generated for a given world in that area. 

For the Proximity characteristic, I'm using an array with an integer for each category.

## Zone and Planet Names
We're using code derived from Sayam Qazi's [planet-name-generator](https://github.com/sayamqazi/planet-name-generator) for building zone and planet names. You can modify the planet name corpus by editing _planet.txt_ and removing or adding planet names separated into syllables with dashes: _Jupiter_ becomes *ju-pi-ter*
. Planetary suffixes are defined in the _generate.py_ script itself in the _genName()_ method.

## Fonts

The following fonts are included for generating text upon zone images:
* [GL-Nummernschild-Eng](https://fontlibrary.org/en/font/gl-nummernschild-eng) - License: [M+ Fonts Project License](https://en.wikipedia.org/wiki/M%2B_FONTS#Licensing)
* [Telegrama](https://www.fontsquirrel.com/fonts/Telegrama) - License: [YOFonts License Agreement](https://www.fontsquirrel.com/license/Telegrama)


## Authors

* Matthew Harris Glover - *Initial work* - [@mhglover](https://twitter.com/mhglover)

<!-- See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project. -->

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Brad Murray's RPG development of [Elysium Flare](https://www.patreon.com/halfjack)
* Sayam Qazi's [planet-name-generator](https://github.com/sayamqazi/planet-name-generator)
