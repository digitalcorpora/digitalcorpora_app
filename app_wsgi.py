# Application starts here

import bottle
import sys
import os
from os.path import abspath, dirname

# Testing:
@bottle.route('/hello/<name>')
def func(name):
    return bottle.template('<b>Hello {{name}}</b>!  Running Python version {{version}}',
                               name=name, version=sys.version)

# Testing:
@bottle.route('/ver')
def func():
    return bottle.template("Python version {{version}}",version=sys.version)

s3_index = bottle.SimpleTemplate( open(os.path.join( dirname(__file__), "templates/s3_index.tpl")).read() )
@bottle.route('/t')
def func():
    prefix = 'a/b/c/d/e/f'
    path = ''
    paths = []
    for part in prefix.split('/'):
        path += part + '/'
        paths.append( (path,part) )
    dirs = ['subdir1','subdir2']
    files= [ ('https://company.com/a','a',100,'n/a','n/a'),
             ('https://company.com/b','b',200,'n/a','n/a')]
    return s3_index.render(prefix=prefix, paths=paths, files=files, dirs=dirs)

# Production
@bottle.route('/')
def root():
    return bottle.static_file('index.html', root= os.path.join(dirname(abspath(__file__)), 'static'))

@bottle.route('/corpora/')
def func():
    import s3_gateway
    return s3_gateway.s3_app('digitalcorpora','corpora/')

@bottle.route('/corpora/<path:path>')
def func(path):
    import s3_gateway
    return s3_gateway.s3_app('digitalcorpora','corpora/' + path)

@bottle.route('/downloads/')
def bottle_downloads():
    import s3_gateway
    return s3_gateway.s3_app('digitalcorpora','downloads/' )

@bottle.route('/downloads/<path:path>')
def f2(path):
    import s3_gateway
    return s3_gateway.s3_app('digitalcorpora','downloads/' + path)

@bottle.route('/robots.txt')
def robots():
    import s3_gateway
    return s3_gateway.s3_app('digitalcorpora','robots.txt')

def app():
    return bottle.default_app()
