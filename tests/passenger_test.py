import sys
import os
from os.path import abspath,dirname

sys.path.append( dirname(dirname(abspath(__file__))))

import passenger_wsgi

def passenger_test():
    assert passenger_wsgi.HOME == os.getenv('HOME')
