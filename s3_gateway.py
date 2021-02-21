#!/usr/bin/python3
# -*- mode: python -*-

"""
s3_gateway:
bottle/boto3 interface to view an s3 bucket in a web browser.

2021-02-15 slg - updated to use anonymous s3 requests,
                 per https://stackoverflow.com/questions/34865927/can-i-use-boto3-anonymously

2021-02-20 slg - add support for database queries to augment what's in S3

"""

import sys
import mimetypes
import logging
import json
import urllib.parse
import os
from os.path import dirname

import boto3
import botocore
import botocore.exceptions

from botocore import UNSIGNED
from botocore.client import Config

import bottle

#from botocore.exceptions import ClientError

from bottle import request, response, redirect

import ctools.dbfile
import ctools.env

DEFAULT_BUCKET = 'digitalcorpora'
BYPASS_URL = 'https://digitalcorpora.s3.amazonaws.com/'
USE_BYPASS = True

IGNORE_FILES = ['.DS_Store', 'Icon']

# Specify files in the runtime environment
DBENV_FILE       = os.path.join( os.getenv('HOME'), 'dbreader.bash')
S3_TEMPLATE_FILE = os.path.join(dirname(__file__), "templates/s3_index.tpl")

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

def s3_to_link(obj):
    """Given a s3 object, return a link to it"""
    # pylint: disable=R1705
    if 'Prefix' in obj:
        name = obj['Prefix'].split("/")[-2]+"/"
        return request.url + urllib.parse.quote(name)
    elif 'Key' in obj:
        return BYPASS_URL + urllib.parse.quote(obj['Key'])
    else:
        raise RuntimeError("obj: "+json.dumps(obj, default=str))


# Create the S3_INDEX bottle SimpleTemplate here, outside of the
# s3_list_prefix_v1, so that it gets read when s3_gateway.py is imported.
# This causes bottle to compile it ONCE and repeatedly serve it out

S3_INDEX = bottle.SimpleTemplate( open( S3_TEMPLATE_FILE ).read())

def s3_list_prefix(bucket_name, prefix):
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
    files = [{'a': s3_to_link(obj),
              'basename': os.path.basename(obj['Key']),
              'size': obj['Size'],
              'ETag': obj['ETag'],
              'sha2_256': 'n/a',
              'sha3_256': 'n/a'} for obj in s3_files]

    logging.warning("bucket_name=%s prefix=%s paths=%s files=%s dirs=%s",
                    bucket_name, prefix, paths, files, dirs)
    return S3_INDEX.render(prefix=prefix, paths=paths, files=files, dirs=dirs, sys_version=sys.version)


def s3_app(bucket, quoted_path):
    """
    Fetching a file. Called from bottle.
    :param bucket: - the bucket that we are serving from
    :param path:   - the path to display.
    """
    path = urllib.parse.unquote(quoted_path)
    logging.warning("bucket=%s quoted_path=%s path=%s",
                    bucket, quoted_path, path)
    # pylint ignore=C0103
    if path.endswith("/"):
        try:
            return s3_list_prefix(bucket, path)
        except FileNotFoundError as e:
            logging.warning("e:%s", e)
            return f"<html><body><pre>\nquoted_path: {quoted_path}\npath: {path}\n</pre>not found</body></html>"

    # If the path does not end with a '/' and there is object there, see if it is a prefix
    try:
        obj = boto3.client('s3', config=Config(
            signature_version=UNSIGNED)).get_object(Bucket=bucket, Key=path)
    except botocore.exceptions.ClientError as e:

        # See if it is a directory list.
        try:
            return s3_list_prefix(bucket, path+"/")
        except FileNotFoundError as e:
            # No object and not a prefix
            response.status = 404
            return f"Error 404: File not found -- s3://{bucket}/{path}"

    # If we are using the bypass, redirect

    if USE_BYPASS:
        print("redirect to", BYPASS_URL + path, file=sys.stderr)
        redirect(BYPASS_URL + path)

    # Otherwise download directly
    try:
        response.content_type = mimetypes.guess_type(path)[0]
    except (TypeError,ValueError,KeyError) as e:
        response.content_type = 'application/octet-stream'
    return obj['Body']


DESCRIPTION="""
This is the testing program for the gateway that
allows S3 files to be accessed from the website.
"""
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description=DESCRIPTION)
    parser.add_argument("--bucket", default=DEFAULT_BUCKET,
                        help='which bucket to use.')
    parser.add_argument('--path', help='specify path')

    args = parser.parse_args()

    if args.path:
        print(s3_app(args.bucket, args.path))
