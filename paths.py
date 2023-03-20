"""
Single handy place for paths.
"""

import os
from os.path import dirname, abspath, relpath, join
import logging
import functools

from bottle import jinja2_view

STATIC_DIR   = join(dirname(abspath(__file__)), 'static')
TEMPLATE_DIR = join(dirname(abspath(__file__)), 'templates')
DBREADER_BASH_FILE = join( os.getenv('HOME'), 'dbreader.bash')

view = functools.partial(jinja2_view, template_lookup=[TEMPLATE_DIR])
