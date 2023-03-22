import sys
import os

from os.path import abspath,dirname

sys.path.append( dirname(dirname(abspath(__file__))))

import bottle_app

def test_dbreader():
    dbreader = bottle_app.get_dbreader()
    assert dbreader is not None
