#!/usr/bin/python3
# -*- mode: python -*-

"""
s3_gateway:
bottle/boto3 interface to view an s3 bucket in a web browser.

2021-02-15 slg - updated to use anonymous s3 requests,
                 per https://stackoverflow.com/questions/34865927/can-i-use-boto3-anonymously

2021-02-20 slg - add support for database queries to augment what's in S3

"""

import json
import logging
import mimetypes
import os
import sys
import urllib.parse
from os.path import dirname

import boto3
import botocore
import botocore.exceptions
import mistune

from botocore import UNSIGNED
from botocore.client import Config

import bottle
from bottle import request, response, redirect

from lib.ctools.dbfile import DBMySQL
from paths import TEMPLATE_DIR

README_NAMES = ['README.txt', 'README.md']
README_TXT_HEADER = "<h3> README </h3>"

DESCRIPTION="""
This is the testing program for the gateway that
allows S3 files to be accessed from the website.
"""
DEFAULT_BUCKET = 'digitalcorpora'
BYPASS_URL = 'https://digitalcorpora.s3.amazonaws.com/'
USE_BYPASS = True

IGNORE_FILES = ['.DS_Store', 'Icon']

INDEX_S3  = 'index_s3.html'
ERROR_404 = 'error_404.html'

def annotate_s3files(auth, objs):
    """Given a dbreader and a set of objects, see if we can find their hash codes in the database"""

    if not objs:
        return

    keys = [obj['Key'] for obj in objs]
    cmd = "select * from downloadable where s3key in (" + ",".join(['%s']*len(keys)) + ")"
    rows = DBMySQL.csfr(auth, cmd, keys, asDicts=True)

    # Re-organize what we got by key...
    rbyk = {row['s3key'] : row for row in rows}
    # Annotate the array
    for obj in objs:
        s3key = obj['Key']
        if s3key in rbyk:
            rk = rbyk[s3key]
            if rk['etag'] == obj['ETag']:
                obj['sha2_256'] = rk['sha2_256']
                obj['sha3_256'] = rk['sha3_256']

def s3_get_dirs_files(bucket_name, prefix):
    """
    Returns a tuple of the s3 objects of the 'dirs' and the 'files'
    Makes an unauthenticated call
    :param bucket_name: bucket to read
    :param prefix: prefix to examine
    :return: (dirs, files) -  a list of prefix objects under `dirs`, and s3 objects under `files`.
    """
    s3client = boto3.client('s3', config=Config(signature_version=UNSIGNED))
    paginator = s3client.get_paginator('list_objects_v2')
    pages = paginator.paginate( Bucket=bucket_name, Prefix=prefix, Delimiter='/' )
    dirs = []
    files = []
    for page in pages:
        for obj in page.get('CommonPrefixes', []):
            dirs.append(obj)
        for obj in page.get('Contents', []):
            files.append(obj)
    if (not dirs) and (not files):
        raise FileNotFoundError(prefix)
    return (dirs, files)

def get_readme(bucket_name, s3_files):
    for name in README_NAMES:
        for obj in s3_files:
            if name.lower() == os.path.basename(obj['Key']).lower():
                o2 = boto3.client('s3', config=Config( signature_version=UNSIGNED)).get_object(Bucket=bucket_name,
                                                                                               Key=obj['Key'])
                if (not o2) or 'Body' not in o2:
                    continue

                if name.lower().endswith(".txt"):
                    return README_TXT_HEADER + "<pre id='readme'>\n" + o2['Body'].read().decode('utf-8','ignore') + "\n<pre>\n"

                if name.lower().endswith(".md"):
                    return "<div id='readme'>" + mistune.html(o2['Body'].read().decode('utf-8','ignore')) + "</div>"
    return ""

def s3_to_link(url, obj):
    """Given a s3 object, return a link to it"""
    # pylint: disable=R1705
    if 'Prefix' in obj:
        name = obj['Prefix'].split("/")[-2]+"/"
        return url + urllib.parse.quote(name)
    elif 'Key' in obj:
        return BYPASS_URL + urllib.parse.quote(obj['Key'])
    else:
        raise RuntimeError("obj: "+json.dumps(obj, default=str))

def s3_list_prefix(bucket_name, prefix, auth=None):
    """The revised s3_list_prefix implementation: uses the Bottle
    template system to generate HTML. Get a list of the sub-prefixes
    (dirs) and the objects with this prefix (files), and then construct
    the dirs[] and files[] arrays. Elements of dirs are strings (one for
    each prefix).  Elements of files[] are (url,name, size,sha256,sha3)
    tuples.

    :param bucket_name: the bucket to list
    :param path: the path within the bucket (no leading /)
"""
    path = '/'
    paths = []
    for part in prefix.split('/')[:-1]:
        part += '/'
        path += part
        paths.append((path, part))

    (s3_dirs, s3_files) = s3_get_dirs_files(bucket_name, prefix)

    dirs = [obj['Prefix'].split('/')[-2]+'/' for obj in s3_dirs]
    if auth is not None and s3_files:
        annotate_s3files(auth, s3_files)
    # pylint: disable=consider-using-f-string
    files = [{'a': s3_to_link(request.url, obj),
              'basename': os.path.basename(obj['Key']),
              'size': "{:,}".format(obj['Size']),
              'ETag': obj['ETag'],
              'LastModified': str(obj['LastModified']).replace("+00:00","Z"),
              'sha2_256': obj.get('sha2_256','n/a'),
              'sha3_256': obj.get('sha3_256','n/a') } for obj in s3_files]

    # Look for a readme file
    readme_html = get_readme(bucket_name, s3_files)

    return bottle.jinja2_template(INDEX_S3,
                                  {'prefix':prefix,
                                   'paths':paths,
                                   'files':files,
                                   'dirs':dirs,
                                   'readme_html':readme_html,
                                   'sys_version':sys.version},template_lookup=[TEMPLATE_DIR])


def s3_app(*, bucket, quoted_prefix, url, auth=None):
    """
    Fetching a file. Called from bottle.
    :param bucket: - the bucket that we are serving from
    :param quoted_prefix:   - the path to display.
    :param auth:   - Database authenticator
    """
    prefix = urllib.parse.unquote(quoted_prefix)
    if 'dev.digitalcorpora' in url:
        logging.info("s3_gateway.py:s3_app url=%s s3_appbucket=%s prefix=%s", url, bucket, prefix)
    else:
        logging.warning("s3_gateway.py:s3_app url=%s s3_appbucket=%s prefix=%s", url, bucket, prefix)

    if prefix.endswith("/"):
        try:
            return s3_list_prefix(bucket, prefix, auth=auth)
        except FileNotFoundError as e:
            logging.warning("e:%s", e)
            response.status = 404
            return bottle.jinja2_template(ERROR_404,bucket=bucket,prefix=prefix,template_lookup=[TEMPLATE_DIR])

    # If the prefix does not end with a '/' and there is object there, see if it is a prefix
    try:
        obj = boto3.client('s3', config=Config( signature_version=UNSIGNED)).get_object(Bucket=bucket, Key=prefix)
    except botocore.exceptions.ClientError:
        try:
            return s3_list_prefix(bucket, prefix+"/", auth=auth)
        except FileNotFoundError:
            # No object and not a prefix
            response.status = 404
            return bottle.jinja2_template('error_404.html',bucket=bucket,prefix=prefix,template_lookup=[TEMPLATE_DIR])

    # If we are using the bypass, redirect

    if USE_BYPASS:
        logging.info("redirect to %s", BYPASS_URL + prefix)
        redirect(BYPASS_URL + prefix)

    # Otherwise download directly
    try:
        response.content_type = mimetypes.guess_type(prefix)[0]
    except (TypeError,ValueError,KeyError):
        response.content_type = 'application/octet-stream'
    return obj['Body']


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description=DESCRIPTION)
    parser.add_argument("--bucket", default=DEFAULT_BUCKET, help='which bucket to use.')
    parser.add_argument('--prefix', help='specify prefix')

    args = parser.parse_args()

    if args.prefix:
        print(s3_app(bucket=args.bucket, quoted_prefix=args.prefix))
