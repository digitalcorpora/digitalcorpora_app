"""
Single handy place for paths.
"""

import os
from os.path import dirname, abspath, relpath, join
import functools

from flask import render_template

STATIC_DIR   = join(dirname(abspath(__file__)), 'static')
TEMPLATE_DIR = join(dirname(abspath(__file__)), 'templates')
ETC_DIR = join(dirname(abspath(__file__)), 'etc')
CREDENTIALS_FILE = join( ETC_DIR, 'credentials.ini')

# Create the @view decorator to add template to the function output
def view(template_name):
    """Decorator to render a template with the function's return value as context"""
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            context = f(*args, **kwargs)
            if isinstance(context, dict):
                return render_template(template_name, **context)
            else:
                return render_template(template_name, result=context)
        return wrapper
    return decorator
