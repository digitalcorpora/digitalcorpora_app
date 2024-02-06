"""
Single handy place for paths.
"""

import os
from os.path import dirname, abspath, relpath, join
import functools

from bottle import jinja2_view

STATIC_DIR   = join(dirname(abspath(__file__)), 'static')
TEMPLATE_DIR = join(dirname(relpath(__file__)), 'templates')
ETC_DIR = join(dirname(relpath(__file__)), 'etc')
CREDENTIALS_FILE = join( ETC_DIR, 'credentials.ini')

# Create the @view decorator to add template to the function output
view = functools.partial(jinja2_view, template_lookup=[TEMPLATE_DIR])
