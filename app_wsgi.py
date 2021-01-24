# Application starts here

import bottle
import sys
import os

@bottle.route('/hello/<name>')
def func(name):
    return bottle.template('<b>Hello {{name}}</b>!  Running Python version {{version}}',
                               name=name, version=sys.version)

@bottle.route('/notepaper')
def func():
    import notepaper
    return notepaper.notepaper_app()

@bottle.route('/ver')
def func():
    return bottle.template("Python version {{version}}",version=sys.version)

def app():
    return bottle.default_app()


