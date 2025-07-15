"""
WSGI file used for Flask interface.

The goal is to only have the Flask code in this file and nowhere else.

Debug:
(cd ~/apps.digitalcorpora.org/;make touch)
https://corp.digitalcorpora.org/
https://corp.digitalcorpora.org/ver
https://corp.digitalcorpora.org/reports

"""

import csv
import json
import sys
import io
import os
import functools
import filetype
from urllib.parse import urlparse
import logging

# Set up logging level from LOG_LEVEL environment variable (default WARNING)
log_level = os.environ.get("LOG_LEVEL", "WARNING").upper()
logging.basicConfig(level=getattr(logging, log_level, logging.WARNING))

from flask import Flask, request, send_from_directory, redirect, jsonify, render_template

import digitalcorpora_app.paths as paths
from digitalcorpora_app.paths import STATIC_DIR, TEMPLATE_DIR, CREDENTIALS_FILE, view
from lib.ctools import dbfile

from digitalcorpora_app import s3_gateway, s3_reports

assert os.path.exists(TEMPLATE_DIR)

__version__='1.0.0'
VERSION_TEMPLATE='version.txt'

DEFAULT_OFFSET = 0
DEFAULT_ROW_COUNT = 1000000
DEFAULT_SEARCH_ROW_COUNT = 1000

app = Flask(__name__, 
           template_folder=TEMPLATE_DIR,
           static_folder=STATIC_DIR)

@functools.cache
def get_dbreader(fail_gracefully=False):
    """Get the dbreader authentication info from TEST_CREDENTIALS, or etc/aws_creds.ini, or default credentials.ini"""
    credentials_path = os.environ.get('TEST_CREDENTIALS')
    if credentials_path:
        if not os.path.exists(credentials_path):
            raise FileNotFoundError(f"TEST_CREDENTIALS is set to {credentials_path}, but the file does not exist.")
        try:
            if credentials_path.endswith('.json'):
                import json
                with open(credentials_path, 'r') as f:
                    creds = json.load(f)
                # Map Amazon-style keys to MYSQL_* keys
                keymap = {
                    'host': 'MYSQL_HOST',
                    'username': 'MYSQL_USER',
                    'password': 'MYSQL_PASSWORD',
                    'dbname': 'MYSQL_DATABASE',
                    'port': 'MYSQL_PORT',
                }
                mapped_creds = {keymap.get(k, k): v for k, v in creds.items() if k in keymap}
                import tempfile
                import configparser
                with tempfile.NamedTemporaryFile('w+', delete=False, suffix='.ini') as tmpini:
                    config = configparser.ConfigParser()
                    config['dbreader'] = mapped_creds
                    config.write(tmpini)
                    tmpini.flush()
                    logging.info(f"Using TEST_CREDENTIALS from {credentials_path} via temp ini {tmpini.name}")
                    return dbfile.DBMySQLAuth.FromConfigFile(tmpini.name, 'dbreader')
            else:
                # Assume ini format
                logging.info(f"Using TEST_CREDENTIALS from {credentials_path} (ini format)")
                return dbfile.DBMySQLAuth.FromConfigFile(credentials_path, 'dbreader')
        except Exception as e:
            raise RuntimeError(f"Failed to load TEST_CREDENTIALS from {credentials_path}: {e}")
    elif os.path.exists(os.path.join(os.path.dirname(__file__), 'etc/aws_creds.ini')):
        aws_creds_path = os.path.join(os.path.dirname(__file__), 'etc/aws_creds.ini')
        logging.info(f"Using AWS creds from {aws_creds_path}")
        return dbfile.DBMySQLAuth.FromConfigFile(aws_creds_path, 'dbreader')
    else:
        logging.info(f"Using default credentials file {CREDENTIALS_FILE}")
        return dbfile.DBMySQLAuth.FromConfigFile(CREDENTIALS_FILE, 'dbreader')


@app.route('/ver')
@view('version.txt')
def func_ver():
    """Demo for reporting python version. Allows us to validate we are using Python3"""
    return {'__version__':__version__,'sys_version':sys.version}

### Local Static
@app.route('/static/<path:path>')
def static_path(path):
    kind = filetype.guess(os.path.join(STATIC_DIR,path))
    mimetype = kind.mime if kind else 'text/plain'
    response = send_from_directory(STATIC_DIR, path, mimetype=mimetype)
    response.headers['Cache-Control'] = 'public, max-age=5'
    return response

### S3 STATIC
@app.route('/robots.txt')
def func_robots():
    """Route https://downloads.digitalcorpora.org/robots.txt which asks Google not to index this."""
    return s3_gateway.s3_view(bucket='digitalcorpora', quoted_prefix='robots.txt', url=request.url)

## TEMPLATE VIEWS
@app.route('/')
@view('index.html')
def func_root():
    o = urlparse(request.url)
    return {'title':'ROOT',
            'hostname':o.hostname,
            'root':o.path}


@app.route('/corpora/')
@app.route('/corpora/<path:path>')
def func_corpora_path(path=''):
    """Route https://downloads.digitalcorpora.org/corpora/path"""
    return s3_gateway.s3_view(bucket='digitalcorpora',
                             quoted_prefix='corpora/' + path,
                             auth=get_dbreader(fail_gracefully=True), url=request.url)

@app.route('/downloads/')
@app.route('/downloads/<path:path>')
def func_downloads_path(path=''):
    """Route https://downloads.digitalcorpora.org/downloads/path"""
    return s3_gateway.s3_view(bucket='digitalcorpora',
                             quoted_prefix='downloads/' + path,
                             auth=get_dbreader(fail_gracefully=True), url=request.url)

@app.route('/reports')
def reports():
    o = urlparse(request.url)
    return s3_reports.reports_html(auth=get_dbreader(),root=os.path.dirname(o.path))

@app.route('/search')
def search():
    return render_template('search.html')

@app.route('/index.tsv')
def index_tsf():
    try:
        row_count = int(request.args.get('row_count', DEFAULT_ROW_COUNT))
    except (ValueError,KeyError):
        row_count = DEFAULT_ROW_COUNT
    try:
        offset = int(request.args.get('offset', DEFAULT_OFFSET))
    except (ValueError,KeyError):
        offset = DEFAULT_OFFSET
    with io.StringIO() as f:
        column_names = []
        rows = dbfile.DBMySQL.csfr(get_dbreader(),
                                   """SELECT * from downloadable WHERE present=1 ORDER BY s3key LIMIT %s, %s""",
                                   (offset,row_count), get_column_names=column_names,asDicts=True)
        writer = csv.DictWriter(f, fieldnames=column_names, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        response = app.response_class(f.getvalue(), mimetype='text/plain')
        return response

## API (used by search)

@app.route('/search/api')
def search_api():
    q = '%' + request.args.get('q','') + '%'
    try:
        search_row_count = int(request.args.get('row_count', DEFAULT_SEARCH_ROW_COUNT))
    except (ValueError,KeyError):
        search_row_count = DEFAULT_SEARCH_ROW_COUNT
    try:
        offset = int(request.args.get('offset', DEFAULT_OFFSET))
    except (ValueError,KeyError):
        offset = DEFAULT_OFFSET
    rows = dbfile.DBMySQL.csfr(get_dbreader(),
                               """SELECT * from downloadable
                                  WHERE s3key LIKE %s AND present=1 ORDER BY s3key LIMIT %s, %s
                               """, (q,offset, search_row_count), asDicts=True)
    return jsonify(rows)

if __name__ == '__main__':
    debug_mode = os.environ.get('DEBUG', 'false').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=8000)
