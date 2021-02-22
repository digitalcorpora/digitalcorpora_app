"""
passenger_wsgi.py script to switch to python3 and use Bottle

To reload:

$ touch tmp/restart.txt
(or)
$ make touch
"""

import sys
import os
import os.path


# Use python of choice
DESIRED_PYTHON = 'python3.9'
DREAMHOST_PYTHON_BINDIR = os.path.join(
    os.getenv('HOME'), 'opt/python-3.9.2/bin')

if DREAMHOST_PYTHON_BINDIR not in os.environ['PATH']:
    os.environ['PATH'] = DREAMHOST_PYTHON_BINDIR + ":" + os.environ['PATH']

if (DESIRED_PYTHON not in sys.executable) and ('RUNNING_PYTEST' not in os.environ):
    os.execlp(DESIRED_PYTHON, DESIRED_PYTHON, *sys.argv)
else:
    # If we get here, we are running under the DESIRED_PYTHON
    import app_wsgi
    application = app_wsgi.app()
