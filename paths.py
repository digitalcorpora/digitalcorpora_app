import os
import os.path
import sys
import json
from os.path import dirname, abspath, join
import functools

STATIC_DIR   = join(dirname(abspath(__file__)), 'static')
TEMPLATE_DIR = join(dirname(abspath(__file__)), 'templates')

from bottle import jinja2_view,static_file
view = functools.partial(jinja2_view, template_lookup=[TEMPLATE_DIR])
