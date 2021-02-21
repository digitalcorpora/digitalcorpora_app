"""
WSGI file used for bottle interface.
"""

import sys
import os
from os.path import abspath, dirname

import bottle
import s3_gateway

@bottle.route('/ver')
def func_ver():
    """Demo for reporting python version. Allows us to validate we are using Python3"""
    return bottle.template("Python version {{version}}", version=sys.version)

@bottle.route('/hello/<name>')
def func_hello(name):
    """Demo for testing bottle parameter passing"""
    return bottle.template('<b>Hello {{name}}</b>!  Running Python version {{version}}',
                           name=name, version=sys.version)



@bottle.route('/test_template')
def func_test_template():
    """Testpoint for testing template without using S3"""
    prefix = 'a/b/c/d/e/f'
    path = ''
    paths = []
    for part in prefix.split('/'):
        path += part + '/'
        paths.append((path, part))
    dirs = ['subdir1', 'subdir2']
    # pylint: disable=C0301
    files = [
        {'a':'https://company.com/a', 'basename':'a', 'size':100, 'ETag':'n/a', 'sha2_256':'n/a', 'sha3_256':'n/a'},
        {'a':'https://company.com/b', 'basename':'b', 'size':200, 'ETag':'n/a', 'sha2_256':'n/a', 'sha3_256':'n/a'}
        ]
    return s3_gateway.S3_INDEX.render(prefix=prefix, paths=paths, files=files, dirs=dirs)

@bottle.route('/')
def func_root():
    """TODO: return a better template"""
    return bottle.static_file('index.html', root=os.path.join(dirname(abspath(__file__)), 'static'))


@bottle.route('/corpora/')
def func_corpora():
    """Route https://downloads.digitalcorpora.org/corpora/ with no path"""
    return s3_gateway.s3_app('digitalcorpora', 'corpora/')


@bottle.route('/corpora/<path:path>')
def func_corpora_path(path):
    """Route https://downloads.digitalcorpora.org/corpora/path"""
    return s3_gateway.s3_app('digitalcorpora', 'corpora/' + path)


@bottle.route('/downloads/')
def func_downloads():
    """Route https://downloads.digitalcorpora.org/downloads/ with no path"""
    return s3_gateway.s3_app('digitalcorpora', 'downloads/')


@bottle.route('/downloads/<path:path>')
def func_downloads_path(path):
    """Route https://downloads.digitalcorpora.org/downloads/path"""
    return s3_gateway.s3_app('digitalcorpora', 'downloads/' + path)


@bottle.route('/robots.txt')
def func_robots():
    """Route https://downloads.digitalcorpora.org/robots.txt which asks Google not to index this."""
    return s3_gateway.s3_app('digitalcorpora', 'robots.txt')

def app():
    """The application"""
    return bottle.default_app()
