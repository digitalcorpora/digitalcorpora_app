import pytest
import sys
import os
import bottle

from os.path import abspath,dirname

# https://bottlepy.org/docs/dev/recipes.html#unit-testing-bottle-applications

from boddle import boddle
from webtest import TestApp

sys.path.append( dirname(dirname(abspath(__file__))))

import bottle_app

def test_app_boddle():
    with boddle(params={}):
        res = bottle_app.func_ver()
        assert bottle_app.__version__ in res
