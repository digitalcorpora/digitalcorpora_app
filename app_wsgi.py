"""
WSGI file used for bottle interface.

Debug:
(cd ~/apps.digitalcorpora.org/;make touch)
https://downloads.digitalcorpora.org/
https://downloads.digitalcorpora.org/ver
https://downloads.digitalcorpora.org/reports

"""

import json
import sys
import os
import functools
from os.path import abspath, dirname

STATIC_DIR = os.path.join(dirname(abspath(__file__)), 'static')
TEMPLATE_DIR = os.path.join(dirname(abspath(__file__)), 'templates')
DBREADER_BASH_FILE = os.path.join( os.getenv('HOME'), 'dbreader.bash')

assert os.path.exists(TEMPLATE_DIR)

import lib.ctools.dbfile as dbfile

import bottle
from bottle import jinja2_view
view = functools.partial(jinja2_view, template_lookup=[TEMPLATE_DIR])

import s3_gateway
import s3_reports

@functools.cache()
def get_dbreader():
    try:
        return dbfile.DBMySQLAuth.FromBashEnvFile( DBREADER_BASH_FILE )
    except FileNotFoundError as e:
        return None

@bottle.route('/')
@view('index.html')
def func_root():
    return {'title':'ROOT'}

@bottle.route('/robots.txt')
def func_robots():
    """Route https://downloads.digitalcorpora.org/robots.txt which asks Google not to index this."""
    return s3_gateway.s3_app(bucket='digitalcorpora', quoted_prefix='robots.txt')

@bottle.route('/corpora/')
@bottle.route('/corpora/<path:path>')
def func_corpora_path(path=''):
    """Route https://downloads.digitalcorpora.org/corpora/path"""
    return s3_gateway.s3_app(bucket='digitalcorpora', quoted_prefix='corpora/' + path, auth=get_dbreader())

@bottle.route('/downloads/')
@bottle.route('/downloads/<path:path>')
def func_downloads_path(path=''):
    """Route https://downloads.digitalcorpora.org/downloads/path"""
    return s3_gateway.s3_app(bucket='digitalcorpora', quoted_prefix='downloads/' + path, auth=get_dbreader())

@bottle.route('/reports')
def func_stats():
    return s3_reports.report_app(auth=get_dbreader())

@bottle.route('/reports.js')
def func_root():
    """TODO: return a better template"""
    return bottle.static_file( 'reports.js', root=os.path.join(dirname(abspath(__file__)), 'static'))

@bottle.route('/reports/json/<num>')
def func_stats(num):
    return s3_reports.report_json(auth=get_dbreader(),num=num)

@bottle.route('/hello/<name>')
def func_hello(name):
    """Demo for testing bottle parameter passing"""
    return bottle.template('<b>Hello {{name}}</b>!<br/>  Running Python version {{version}}',
                           name=name, version=sys.version)

@bottle.route('/search')
def search():
    return bottle.static_file( 'search.html', root=STATIC_DIR );

@bottle.route('/search/api')
def search_api():
    q = '%' + bottle.request.query.get('q','') + '%'
    dbreader = get_dbreader()
    rows = dbfile.DBMySQL.csfr(dbreader,
                                      f"select * from downloadable where s3key like %s and present=1 order by s3key limit 1000",q,
                                      asDicts=True)
    return json.dumps(rows,indent=4, sort_keys=True, default=str)


@bottle.route('/ver')
def func_ver():
    """Demo for reporting python version. Allows us to validate we are using Python3"""
    return bottle.template("Python version {{version}}", version=sys.version)



def app():
    """The application"""
    return bottle.default_app()
