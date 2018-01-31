#!/usr/bin/env python
""" Set up Passenger for a virtualenv and the flarezone app. """
# pylint: disable=W0611, C0413
import sys
import os

INTERP = os.getcwd() + "/env/bin/python"
#INTERP is present twice so that the new python interpreter
# knows the actual executable path
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

from flarezone import app as application
