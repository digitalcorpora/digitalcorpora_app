#!/usr/bin/python3
# -*- mode: python -*-

"""
s3_gateway:
bottle/boto3 interface to view an s3 bucket in a web browser.
Currently not operational; based on operational code elsewhere.
Being refactored into public code and prvate code.

"""

import sys
import socket
import bottle
import io
import mimetypes
import boto3
import botocore
import botocore.exceptions
import logging
import json
import urllib.parse

from os.path import abspath,dirname
from bottle import request,response

server_base = ''
DEFAULT_BUCKET='digitalcorpora'
BYPASS_URL = 'https://digitalcorpora.s3.amazonaws.com/'
USE_BYPASS = True

IGNORE_FILES = ['.DS_Store','Icon']

def s3_get_dirs_files(bucket_name, path):
    """
    Returns a list of the s3 objects of the 'dirs' and the 'files'
    """
    s3client  = boto3.client('s3')
    paginator = s3client.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket_name, Prefix=path, Delimiter='/')
    dirs  = []
    files = []
    for page in pages:
        for obj in page.get('CommonPrefixes',[]):
            dirs.append(obj)
        for obj in page.get('Contents',[]):
            files.append(obj)
    if (not dirs) and (not files):
        raise FileNotFoundError(path)
    return (dirs,files)

def s3_to_link(obj):
    """Given a s3 object, return a link to it"""
    if 'Prefix' in obj:
        name = obj['Prefix'].split("/")[-2]+"/"
        return request.url + urllib.parse.quote(name)
    elif 'Key' in obj:
        return BYPASS_URL + urllib.parse.quote(obj['Key'])
    else:
        raise RuntimeError("obj: "+json.dumps(obj,default=str))

def s3_list_prefix(bucket_name, path):
    """
    Display the path in a bucket as a prefix. This is done server-server side so that it will work with wget -r.
    """
    (dirs,files) = s3_get_dirs_files(bucket_name,path)
    parent = dirname(dirname(request.url))+"/"

    f = io.StringIO()
    f.write("<html><body>")
    f.write(f"<h1>{path}</h1>\n")

    # Get all of the objects. We make one pass and separate out the
    # prefixes from the contents.
    # cache pages due to 1000 object limit on aws api

    f.write("<h2>Sub directories:</h2>\n")
    f.write("<ul>\n")
    f.write(f"<li><a href='{parent}'>[Parent Directory]</a>\n")
    for obj in dirs:
        name = obj['Prefix'].split('/')[-2]
        f.write(f"<li><a href='{s3_to_link(obj)}'>{name}</a></li>\n")
    f.write("</ul>\n")

    f.write("<h2>Downloads:</h2>")
    f.write("<table>\n")
    for (ct,obj) in enumerate(files):
        if ct==0:
            f.write("<tr><th>Name</th><th>Size</th><th>Mod Date</th></tr>")
        name = obj['Key'].split('/')[-1]
        if name in IGNORE_FILES:
            continue
        f.write(f"<tr><td><a href='{s3_to_link(obj)}'>{name}</a></td><td> "
                f"{obj['Size']:,}</td><td>{obj['LastModified']}</td></tr>\n")
    f.write("</table>\n")
    f.write("</body></html>")
    return f.getvalue()


def s3_app(bucket, quoted_path):

    """
    Fetching a file
    :param bucket: - the bucket that we are serving from
    :param path:   - the path to display.
    """
    path = urllib.parse.unquote(quoted_path)
    logging.warning("bucket=%s quoted_path=%s path=%s",bucket,quoted_path,path)
    if path.endswith("/"):
        try:
            return s3_list_prefix(bucket, path)
        except FileNotFoundError as e:
            return f"<html><body><pre>\nquoted_path: {quoted_path}\npath: {path}\n</pre>not found</body></html>"

    try:
        response.content_type = mimetypes.guess_type(path)[0]
    except:
        response.content_type = 'application/octet-stream'

    try:
        obj = boto3.client('s3').get_object(Bucket=bucket, Key=path)
        return obj['Body']
    except botocore.exceptions.ClientError  as e:
        # See if it is a prefix
        try:
            return s3_list_prefix(bucket, path+"/")
        except FileNotFoundError as e:
            pass

        response.status=404
        return f"Error 404: File not found -- s3://{bucket}/{path}"



if __name__=="__main__":
    import argparse

    # from ctools.lock import lock_script
    # lock_script()
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description="""This is the testing program for the gateway that allows S3 files to be accessed from the dashboard. If given a prefix, it will display the HTML UI for choosing a file. Otherwise it will provide the file's contents.""")
    parser.add_argument("--bucket", default=DEFAULT_BUCKET, help='which bucket to use.')
    parser.add_argument("--zip_pattern")
    parser.add_argument("--log_cluster")
    parser.add_argument("--log_application")
    parser.add_argument("--pattern")
    parser.add_argument('--dump',help='just dump the file',action='store_true')
    parser.add_argument('--path',help='specify path')

    args = parser.parse_args()

    if args.zip_pattern:
        if args.pattern:
            print(s3_gen_find_in_zip("app/download/", args.bucket, args.path, args.zip_pattern, args.pattern))
        else:
            print(s3_gen_find_in_dir("app/contents/", args.bucket, args.path, args.zip_pattern))
    if args.path:
        print(s3_app(args.bucket,args.path))
