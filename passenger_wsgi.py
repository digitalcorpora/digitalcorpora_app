"""
passenger_wsgi.py script to switch to python3 and use Flask on Dreamhost.

To reload:

$ touch tmp/restart.txt
(or)
$ make touch

Version History:
2023-02-17 - slg - updated for flask
"""

import sys
import os
import os.path

DESIRED_PYTHON_VERSION  = '3.9'
DESIRED_PYTHON          = 'python3.9'
DREAMHOST_PYTHON_BINDIR = os.path.join( os.getenv('HOME'), 'opt/python-3.9.2/bin')
MYDIR = os.path.dirname( os.path.abspath( __file__ ))
APP_NAME = 'flaskr'
debug=False

# Rewrite stderr if not running under pytest
if 'PYTEST' not in os.environ:
    with open( os.path.join( os.getenv('HOME'), 'error.log'),'a') as errfile:
        os.close(sys.stderr.fileno())
        os.dup2(errfile.fileno(), sys.stderr.fileno())

if sys.version < DESIRED_PYTHON_VERSION:
    if DREAMHOST_PYTHON_BINDIR not in os.environ['PATH']:
        if debug:
            sys.stderr.write("Adding "+DREAMHOST_PYTHON_BINDIR+" to PATH\n")
        os.environ['PATH'] = DREAMHOST_PYTHON_BINDIR + ":" + os.environ['PATH']

    if (DESIRED_PYTHON not in sys.executable) and ('PYTEST' not in os.environ):
        if debug:
            sys.stderr.write("Executing "+DESIRED_PYTHON+"\n")
        os.execlp(DESIRED_PYTHON, DESIRED_PYTHON, *sys.argv)

sys.path.append( MYDIR )
sys.path.append( os.path.join(MYDIR,APP_NAME))

## Run Flask application
import flaskr
application = flaskr.create_app()
