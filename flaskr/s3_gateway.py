#!/usr/bin/python3
# -*- mode: python -*-

"""
s3_gateway:

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
import pymysql
from os.path import dirname

import boto3
import botocore
import botocore.exceptions

from botocore import UNSIGNED
from botocore.client import Config

from flask import Flask, redirect, request, render_template, Response
from flask import Flask, send_from_directory

import db_lookup

DESCRIPTION="""
This is the testing program for the gateway that
allows S3 files to be accessed from the website.
"""
DEFAULT_BUCKET = 'digitalcorpora'
BYPASS_URL = 'https://digitalcorpora.s3.amazonaws.com/'
USE_BYPASS = True

IGNORE_FILES = ['.DS_Store', 'Icon']

S3_INDEX  = "s3_index.html"
ERROR_404 = "error_404.html"

def s3_get_dirs_files(bucket_name, prefix):
    """
    Returns a tuple of the s3 objects of the 'dirs' and the 'files'
    Makes an unauthenticated call
    :param bucket_name: bucket to read
    :param prefix: prefix to examine
    :return: (prefixes,keys) -  a list of prefixes under `prefix`, and keys under `prefix`.
    """
    s3client = boto3.client('s3', config=Config(signature_version=UNSIGNED))
    paginator = s3client.get_paginator('list_objects_v2')
    pages = paginator.paginate(
        Bucket=bucket_name, Prefix=prefix, Delimiter='/')
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
        try:
            db_lookup.annotate_s3files(auth, s3_files)
        except pymysql.err.ProgrammingError as e:
            if e.args[0]!=1146:
                raise
            logging.error("%s: %s",e.args[0],e.args[1])
    files = [{'a': s3_to_link(request.url, obj),
              'basename': os.path.basename(obj['Key']),
              'size': "{:,}".format(obj['Size']),
              'ETag': obj['ETag'],
              'LastModified': str(obj['LastModified']).replace("+00:00",""),
              'sha2_256': obj.get('sha2_256','n/a'),
              'sha3_256': obj.get('sha3_256','n/a') } for obj in s3_files]

    return render_template(S3_INDEX,prefix=prefix, paths=paths, files=files, dirs=dirs, sys_version=sys.version)


def s3_app(*, bucket, quoted_prefix, auth=None):
    """
    Fetching a file. Called from bottle.
    :param bucket: - the bucket that we are serving from
    :param quoted_prefix:   - the path to display.
    :param auth:   - Database authenticator
    """
    prefix = urllib.parse.unquote(quoted_prefix)
    logging.warning("s3_gateway.py::s3_app url=%s s3_appbucket=%s prefix=%s", request.url, bucket, prefix)

    if prefix.endswith("/"):
        try:
            return s3_list_prefix(bucket, prefix, auth=auth)
        except FileNotFoundError as e:
            logging.warning("e:%s", e)
            return Response(response=render_template(ERROR_404, bucket=bucket,prefix=prefix), status=404)


    # If the prefix does not end with a '/' and there is object there, see if it is a prefix
    try:
        obj = boto3.client('s3', config=Config( signature_version=UNSIGNED)).get_object(Bucket=bucket, Key=prefix)
    except botocore.exceptions.ClientError as e:
        try:
            return s3_list_prefix(bucket, prefix+"/", auth=auth)
        except FileNotFoundError as e:
            # No object and not a prefix
            return Response(response=render_template(ERROR_404, bucket=bucket,prefix=prefix), status=404)

    # If we are using the bypass, redirect

    if USE_BYPASS:
        logging.info("redirect to %s", BYPASS_URL + prefix)
        redirect(BYPASS_URL + prefix)

    # Otherwise download directly
    try:
        r = Response(response=obj['Body'], status=200, mimetype=mimetypes.guess_type(prefix)[0])
    except (TypeError,ValueError,KeyError) as e:
        r = Response(response=obj['Body'], status=200, mimetype='application/octet-stream')
        r.headers['Content-Type'] = 'application/octet-stream'
    return r


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description=DESCRIPTION)
    parser.add_argument("--bucket", default=DEFAULT_BUCKET, help='which bucket to use.')
    parser.add_argument('--prefix', help='specify prefix')

    args = parser.parse_args()

    if args.prefix:
        print(s3_app(bucket=args.bucket, quoted_prefix=args.prefix))
