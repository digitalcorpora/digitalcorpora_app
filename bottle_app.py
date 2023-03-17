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
import io
import os
import functools
from urllib.parse import urlparse

import bottle

from paths import STATIC_DIR,TEMPLATE_DIR,DBREADER_BASH_FILE,view
from lib.ctools import dbfile

import s3_gateway
import s3_reports

assert os.path.exists(TEMPLATE_DIR)

VERSION_TEMPLATE="""
Python version {{version}}
"""

@functools.cache
def get_dbreader():
    try:
        return dbfile.DBMySQLAuth.FromBashEnvFile( DBREADER_BASH_FILE )
    except FileNotFoundError:
        return None

@bottle.route('/ver')
def func_ver():
    """Demo for reporting python version. Allows us to validate we are using Python3"""
    return bottle.jinja2_template(VERSION_TEMPLATE, version=sys.version)

### Local Static
@bottle.get('/static/<path:path>')
def static_path(path):
    return bottle.static_file(path, root=STATIC_DIR)

### S3 STATIC
@bottle.route('/robots.txt')
def func_robots():
    """Route https://downloads.digitalcorpora.org/robots.txt which asks Google not to index this."""
    return s3_gateway.s3_app(bucket='digitalcorpora', quoted_prefix='robots.txt')

## TEMPLATE VIEWS
@bottle.route('/')
@view('index.html')
def func_root():
    o = urlparse(bottle.request.url)
    return {'title':'ROOT',
            'hostname':o.hostname}


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
def reports():
    return s3_reports.reports_html(auth=get_dbreader())

@bottle.route('/search')
def search():
    return bottle.jinja2_template('search.html', template_lookup=[TEMPLATE_DIR])

@bottle.route('/index.tsv')
def index_tsf():
    with io.StringIO() as f:
        column_names = []
        rows = dbfile.DBMySQL.csfr(get_dbreader(),
                                   """SELECT * from downloadable WHERE present=1 ORDER BY s3key""",
                                   (), get_column_names=column_names,asDicts=False)
        print("\t".join(column_names), file=f)
        for row in rows:
            print("\t".join([str(v) for v in row]), file=f)
        bottle.response.content_type = "text/plain"
        return f.getvalue()

## API (used by search)

@bottle.route('/search/api')
def search_api():
    # pylint: disable=no-member
    q = '%' + bottle.request.query.get('q','') + '%'
    # pylint: enable=no-member
    rows = dbfile.DBMySQL.csfr(get_dbreader(),
                               """SELECT * from downloadable
                                  WHERE s3key LIKE %s AND present=1 ORDER BY s3key LIMIT 1000
                               """, (q,), asDicts=True)
    return json.dumps(rows,indent=4, sort_keys=True, default=str)



def app():
    """The application"""
    return bottle.default_app()
