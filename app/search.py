#!/usr/bin/env python3

"""
Search routines for metasearch.
The only fields we care about in searching are:
url - the key
valid - must be 1
title - is displayed
body - is displayed
body_hash - for removing duplicates
datePublished - the date that is displayed for the article

All of the remaining metadata comes from the metadata table
"""

import os
import sys
import json
import time
from os.path import dirname
from collections import defaultdict

DEBUG=True
#DEBUG=False

sys.path.append( dirname( dirname( os.path.abspath( __file__ ))))

import ctools.dbfile as dbfile

def stats( auth ):
    """ Return displayed stats about all of the articles """
    ret = dbfile.DBMySQL.csfr(auth, f"""
          SELECT
          UNIX_TIMESTAMP(MIN(sitemap_last_modified)) as sitemap_start,
          UNIX_TIMESTAMP(MAX(sitemap_last_modified)) as sitemap_end,
          UNIX_TIMESTAMP(MIN(datePublished)) as datePublished_start,
          UNIX_TIMESTAMP(MAX(datePublished)) as datePublished_end,
          COUNT( DISTINCT author) as distinct_authors,
          COUNT( * ) as total_urls,
          SUM( valid ) as valid_urls,
          SUM( IF (valid IS NOT NULL, 1, 0)) as processed_urls
          FROM {auth.prefix}articles
          """, asDicts=True)[0]
    for a in ['sitemap_start', 'sitemap_end','datePublished_start', 'datePublished_end']:
        ret[ a + '_date'] = time.strftime("%Y-%m-%d", time.gmtime(ret[ a ]))
    ret['host']   = auth.host
    ret['prefix'] = auth.prefix
    return ret

def search_api( auth, spec ):
    FIELDS = f'id, url, title, author, datePublished, words, SUBSTRING(body,1,50) as snipit, body_hash '
    cmd = f"SELECT {FIELDS} FROM {auth.prefix}articles WHERE TRUE  "
    args = []

    if len(spec.get('author',''))>0:
        cmd += 'AND author like %s '
        args.append( '%' + spec.get('author', type=str) + '%')

    if len(spec.get('title',''))>0:
        cmd += 'AND title like %s '
        args.append( '%' + spec.get('title', type=str) + '%')

    if len(spec.get('body',''))>0:
        cmd += 'AND MATCH( body ) against  (%s in natural language mode) '
        args.append( spec.get('body', type=str) )

    if len(spec.get('start_date', ''))>0:
        cmd += 'AND datePublished >= %s '
        args.append( spec.get('start_date', type=str) )

    if len(spec.get('end_date', ''))>0:
        cmd += 'AND datePublished <= %s '
        args.append( spec.get('end_date', type=str) )

    if len(spec.get('metadata', ''))>0:
        cmd += f'AND id in (SELECT articleid from {auth.prefix}metadata WHERE MATCH( v ) AGAINST (%s in natural language mode)) '
        args.append( spec.get('metadata', type=str) )

    cmd += f'GROUP BY {auth.prefix}articles.id '
    cmd += f'ORDER BY datePublished desc LIMIT 1000 '

    # No longer needed to factor, since body_hash should not be duplicated:
    # cmd = f'SELECT MAX(id) AS id,MAX(url) AS url,MAX(title) AS title,MAX(author) AS author,DATE(MAX(datePublished)) AS datePublished,MAX(words) AS words,MAX(snipit) AS snipit from ( {cmd} ) a GROUP BY body_hash ORDER BY datePublished '

    if DEBUG:
        print("CMD:",cmd,file=sys.stderr)
        print("ARGS:",args,file=sys.stderr)

    rows = dbfile.DBMySQL.csfr( auth, cmd, args, asDicts=True )
    ids  = set( (int(row['id']) for row in rows) )   #convert to int for security
    metadata = defaultdict(dict)
    metadata_keys = set()
    metadata_keys_matched = set()
    metadata_search = spec.get('metadata','').lower()
    fullnames = defaultdict(list)
    # If we had a match, get the metadata for all matches
    # 'ids' is safe and does not require a prepared parameter.
    if ids:
        articleids = "(" + ','.join( (str(x) for x in ids ) ) + ")"
        cmd = f"SELECT articleid as id, k, v from {auth.prefix}metadata where articleid in {articleids}"
        for (articleid, k, v) in dbfile.DBMySQL.csfr( auth, cmd, [] ):
            metadata[articleid][k]=v
            metadata_keys.add(k)
            if metadata_search and (k not in metadata_keys_matched) and (metadata_search in v.lower()):
                metadata_keys_matched.add(k)
        cmd = f"SELECT articleid as id, fullname from {auth.prefix}fullnames where articleid in {articleids} ORDER BY 1,2 "
        for (articleid, fullname) in dbfile.DBMySQL.csfr( auth, cmd, [] ):
            fullnames[articleid].append(fullname)

    ret = {
        'rows':rows,
        'metadata':metadata,
        'metadata_keys':metadata_keys,
        'metadata_keys_matched':metadata_keys_matched,
        'fullnames':fullnames
        }
    if DEBUG:
        print("RET:", ret,file=sys.stderr)
        print("",file=sys.stderr)
    return ret

def log_search( auth, remote_ipaddr, query):
    cmd = f"INSERT INTO {auth.prefix}searchlog (remote_ipaddr, query) VALUES (%s, %s) "
    return dbfile.DBMySQL.csfr( auth, cmd, (remote_ipaddr, query))
