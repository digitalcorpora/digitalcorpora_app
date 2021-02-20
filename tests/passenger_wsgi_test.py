import pytest
import sys
import os

from os.path import abspath,dirname

sys.path.append( dirname(dirname(abspath(__file__))))
import passenger_wsgi

def test_INTERP():
    assert 'python3' in passenger_wsgi.DESIRED_PYTHON
