import sys
import os
import json
import tempfile
import urllib.parse
import pymysql
import io
import re
import html
from os.path import basename,dirname,abspath

from flask import Flask, redirect, request, render_template
from flask import Flask, send_from_directory

sys.path.append( dirname( abspath( __file__ )))
from app import app                       # needed for app routing

from . import APP_DIR, BIN_DIR, LIB_DIR, ROOT_DIR, STATIC_DIR, HOME

import ctools.dbfile
import s3_gateway

DBREADER_BASH_FILE = os.path.join( os.getenv('HOME'), 'dbreader.bash')
try:
    dbreader = ctools.dbfile.DBMySQLAuth.GetBashEnvFromFile( DBREADER_BASH_FILE )
except FileNotFoundError as e:
    dbreader = None


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
    print("func_root",file=sys.stderr)
    return send_from_directory( STATIC_DIR, 'index.html')

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
def func_reports():
    return s3_reports.report_app(auth=dbreader)

@app.route('/reports/json/<num>')
def func_stats(num):
    return s3_reports.report_json(auth=dbreader,num=num)

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
    return json.dumps(rows,indent=4, sort_keys=True, default=str)


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
    return s3_gateway.S3_INDEX.render(prefix=prefix, paths=paths, files=files, dirs=dirs)
