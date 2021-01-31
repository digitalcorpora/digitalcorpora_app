# Application starts here

import bottle
import sys
import os

@bottle.route('/hello/<name>')
def func(name):
    return bottle.template('<b>Hello {{name}}</b>!  Running Python version {{version}}',
                               name=name, version=sys.version)

@bottle.route('/ver')
def func():
    return bottle.template("Python version {{version}}",version=sys.version)

@bottle.route('/corpora/<path:path>')
def func(path):
    import s3_gateway
    return s3_gateway.s3_app('digitalcorpora','corpora/' + path)

@bottle.route('/corpora/')
def func():
    import s3_gateway
    return s3_gateway.s3_app('digitalcorpora','corpora/')

def app():
    return bottle.default_app()
