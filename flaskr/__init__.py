from flask import Flask
from os.path import dirname,basename,abspath
import os
import sys
import pytest
import datetime
import json

from flask import Flask, redirect, request, render_template
from flask import Flask, send_from_directory


HOME     = os.environ['HOME']
APP_DIR  = os.path.join( os.path.dirname( os.path.abspath( __file__ ) ) )
ROOT_DIR = os.path.dirname(APP_DIR)
BIN_DIR  = os.path.join(ROOT_DIR, 'bin')
LIB_DIR  = os.path.join(ROOT_DIR, 'lib')
TEST_DIR = os.path.join(ROOT_DIR, 'tests')
STATIC_DIR = os.path.join(APP_DIR, 'static')

DBREADER_DIRS  = [APP_DIR, HOME]
DBREADER_FILES = ['dbreader_digitalcorpora.bash','dbreader.bash']

DEBUG=True

for path in [ APP_DIR, BIN_DIR, LIB_DIR, ROOT_DIR ]:
    if path not in sys.path:
        sys.path.append(path)

import ctools.dbfile
import s3_gateway
import s3_reports


def get_dbreader():
    try:
        return ctools.dbfile.DBMySQLAuth(host=os.environ['MYSQL_HOST'],
                                        database=os.environ['MYSQL_DATABASE'],
                                        user=os.environ['MYSQL_USER'],
                                        password=os.environ['MYSQL_PASSWORD'])
    except KeyError as e:
        pass

    for d in DBREADER_DIRS:
        for fname in DBREADER_FILES:
            path = os.path.join( d, fname )
            if os.path.exists(path):
                return ctools.dbfile.DBMySQLAuth.FromBashEnvFile( path )
    return None

def create_app(config_filename=None, auth=None):
    app = Flask(__name__, static_folder='static')
    if config_filename is not None:
        app.config.from_pyfile(config_filename)
    if DEBUG:
        app.debug=DEBUG

    if auth is not None:
        dbreader = auth
    else:
        dbreader = get_dbreader()


    # https://help.dreamhost.com/hc/en-us/articles/215769548-Passenger-and-Python-WSGI
    ################################################################
    ## background

    @app.route('/favicon.ico')
    def icon():
        return redirect("static/favicon.ico.png")

    @app.route('/ver')
    def ver():
        return f"Python version {sys.version}"

    @app.route('/error')
    def error():
        raise RuntimeError("Demonstration Error")

    ################################################################
    ## root

    @app.route('/')
    def func_root():
        return render_template( 'index.html')

    @app.route('/static/<path:path>')
    def send_static():
        return send_from_directory( STATIC_DIR, path )

    ##############
    ## S3 files ##

    @app.route('/robots.txt')
    def func_robots():
        """Route https://downloads.digitalcorpora.org/robots.txt which asks Google not to index this."""
        return s3_gateway.s3_app(bucket='digitalcorpora', quoted_prefix='robots.txt')

    @app.route('/corpora/')
    @app.route('/corpora/<path:path>')
    def func_corpora_path(path=''):
        """Route https://downloads.digitalcorpora.org/corpora/path"""
        return s3_gateway.s3_app(bucket='digitalcorpora', quoted_prefix='corpora/' + path, auth=dbreader)

    @app.route('/downloads/')
    @app.route('/downloads/<path:path>')
    def func_downloads_path(path=''):
        """Route https://downloads.digitalcorpora.org/downloads/path"""
        return s3_gateway.s3_app(bucket='digitalcorpora', quoted_prefix='downloads/' + path, auth=dbreader)

    ################################################################
    ## Reports

    @app.route('/reports')
    @app.route('/reports/')
    def func_reports():
        return s3_reports.report_app(auth=dbreader)

    @app.route('/reports/json/<num>')
    def func_stats(num):
        return json.dumps(s3_reports.report_generate(auth=dbreader,num=num),default=str)

    @app.route('/hello/<name>')
    def func_hello(name):
        """Demo for testing Flask parameter passing"""
        return render_template('hello.html',name=name, version=sys.version)

    @app.route('/search')
    def search():
        return render_template( 'search.html');

    @app.route('/search/api')
    def search_api():
        q = '%' + request.args.get('q','') + '%'
        rows = ctools.dbfile.DBMySQL.csfr(dbreader,
                                          f"select * from downloadable where s3key like %s and present=1 order by s3key limit 1000",q,
                                          asDicts=True)
        return json.dumps(rows, sort_keys=True, default=str)


    @app.route('/test_template')
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
        return render_template(s3_gateway.S3_INDEX,prefix=prefix, paths=paths, files=files, dirs=dirs)

    return app
