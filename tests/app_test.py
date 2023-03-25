import pytest
import sys
import os
import bottle
import warnings
import json

from os.path import abspath,dirname

# https://bottlepy.org/docs/dev/recipes.html#unit-testing-bottle-applications

from boddle import boddle
from webtest import TestApp

sys.path.append( dirname(dirname(abspath(__file__))))

import bottle_app
from paths import STATIC_DIR

def test_version():
    # With templates, res is just a string
    with boddle(params={}):
        res = bottle_app.func_ver()
        assert bottle_app.__version__ in res

def test_static_path():
    # Without templates, res is an HTTP response object with .body and .header and stuff
    with boddle(params={}):
        res = bottle_app.static_path('test.txt')
        assert open( os.path.join( STATIC_DIR, 'test.txt'), 'rb').read() == res.body.read()

def test_reports():
    # With templates, res is just a string
    with boddle(params={}):
        bottle_app.reports()

def test_search():
    # With templates, res is just a string
    with boddle(params={}):
        bottle_app.search()

def test_index_tsv():
    with boddle(params={'row_count':'5', 'offset':'0'}):
        res = bottle_app.index_tsf()
        lines = res.split('\n')
        assert len(lines) == 6

def test_search_api():
    with boddle(params={'q':'dmg'}):
        res = bottle_app.search_api()
        print(json.loads(res))         # make sure it converts from JSON

    with boddle(params={'q':'dmg', 'row_count':'1', 'offset':'0'}):
        res = bottle_app.search_api()
        val = json.loads(res)         # make sure it converts from JSON
        assert len(val)==1            # make sure we got one row
