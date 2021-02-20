import sys
import os
import os.path

"""
passenger_wsgi.py script to switch to python3 and use Bottle

To reload:

$ touch tmp/restart.txt
(or)
$ make touch
"""

# Use python of choice
INTERP = os.path.join(os.getenv('HOME'), 'opt/python-3.9.2/bin/python3.9')

if sys.executable != INTERP:
    if not os.path.exists(INTERP):
        print("File not found:"+INTERP)
        exit(1)
    os.execl(INTERP, INTERP, *sys.argv)
else:
    import bottle
    import app_wsgi
application = app_wsgi.app()
