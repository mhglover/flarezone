import sys, os
cwd = os.getcwd()
INTERP = cwd + "/env/bin/python"

#INTERP is present twice so that the new python interpreter knows the actual executable path 
if sys.executable != INTERP: os.execl(INTERP, INTERP, *sys.argv)

from flarezone import app as application