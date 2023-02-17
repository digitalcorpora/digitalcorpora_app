from flask import Flask
from os.path import dirname,basename,abspath
import os
import sys
import pytest
import datetime

HOME     = os.environ['HOME']
APP_DIR  = os.path.join( os.path.dirname( os.path.abspath( __file__ ) ) )
ROOT_DIR = os.path.dirname(APP_DIR)
BIN_DIR  = os.path.join(ROOT_DIR, 'bin')
LIB_DIR  = os.path.join(ROOT_DIR, 'lib')
TEST_DIR = os.path.join(ROOT_DIR, 'tests')
STATIC_DIR = os.path.join(APP_DIR, 'static')

DEBUG=True

for path in [ APP_DIR, BIN_DIR, LIB_DIR, ROOT_DIR ]:
    if path not in sys.path:
        sys.path.append(path)


app = Flask(__name__, static_folder='static')
if DEBUG:
    app.debug=DEBUG

# Now bring in the routing...
from app import routes
