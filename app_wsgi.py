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
from os.path import abspath, dirname

import bottle

import lib.ctools.dbfile as dbfile

import s3_gateway
import s3_reports

STATIC_DIR = os.path.join(dirname(abspath(__file__)), 'static')
DBREADER_BASH_FILE = os.path.join( os.getenv('HOME'), 'dbreader.bash')
try:
    dbreader = dbfile.DBMySQLAuth.FromBashEnvFile( DBREADER_BASH_FILE )
except FileNotFoundError as e:
    dbreader = None

@bottle.route('/')
def func_root():
    """TODO: return a better template"""
    return bottle.static_file('index.html', root=STATIC_DIR)

@bottle.route('/corpora/')
@bottle.route('/corpora/<path:path>')
def func_corpora_path(path=''):
    """Route https://downloads.digitalcorpora.org/corpora/path"""
    return s3_gateway.s3_app(bucket='digitalcorpora', quoted_prefix='corpora/' + path, auth=dbreader)


@bottle.route('/downloads/')
@bottle.route('/downloads/<path:path>')
def func_downloads_path(path=''):
    """Route https://downloads.digitalcorpora.org/downloads/path"""
    return s3_gateway.s3_app(bucket='digitalcorpora', quoted_prefix='downloads/' + path, auth=dbreader)

@bottle.route('/robots.txt')
def func_robots():
    """Route https://downloads.digitalcorpora.org/robots.txt which asks Google not to index this."""
    return s3_gateway.s3_app(bucket='digitalcorpora', quoted_prefix='robots.txt')

@bottle.route('/reports')
def func_stats():
    return s3_reports.report_app(auth=dbreader)

@bottle.route('/reports.js')
def func_root():
    """TODO: return a better template"""
    return bottle.static_file( 'reports.js', root=os.path.join(dirname(abspath(__file__)), 'static'))

@bottle.route('/reports/json/<num>')
def func_stats(num):
    return s3_reports.report_json(auth=dbreader,num=num)

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
    rows = dbfile.DBMySQL.csfr(dbreader,
                                      f"select * from downloadable where s3key like %s and present=1 order by s3key limit 1000",q,
                                      asDicts=True)
    return json.dumps(rows,indent=4, sort_keys=True, default=str)


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

@bottle.route('/ver')
def func_ver():
    """Demo for reporting python version. Allows us to validate we are using Python3"""
    return bottle.template("Python version {{version}}", version=sys.version)



def app():
    """The application"""
    return bottle.default_app()
