import sys, os

"""
To reload:

touch tmp/restart.txt 
(or)
maken
"""

# Use python of choice
INTERP = "/usr/bin/python3.6"

if sys.executable != INTERP: 
    os.execl(INTERP, INTERP, *sys.argv)
else:
    import bottle
    import app_wsgi
application = app_wsgi.app()
    
