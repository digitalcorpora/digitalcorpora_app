#!/usr/bin/env python3

"""
TRTools - tools for extracting articles from the website and store in the database.

See:
https://stackoverflow.com/questions/31276001/parse-xml-sitemap-with-python
https://advertools.readthedocs.io/en/master/advertools.sitemaps.html
https://github.com/mediacloud/ultimate-sitemap-parser
"""

import requests
import sys
import os
import os.path
import pickle
import logging
import warnings
import json
import configparser
import re
import datetime
import time
import pymysql.cursors
import zlib
import subprocess
from collections import defaultdict
from os.path import abspath,basename,dirname
from w3lib.url import canonicalize_url


## Configuration
MAX_SIZE_CONTENT_COMPRESSED=65535
SAVE_HTTP_CONTENT=True
SAVE_PDF_CONTENT=False


ROOT_DIR = dirname(dirname( abspath( __file__ )))
if ROOT_DIR not in sys.path:
    sys.path.append( ROOT_DIR )

SCHEMA_FILE = os.path.join(ROOT_DIR, 'schema.sql')


import article
import app
import app.config
import urllib.parse
import urllib3
from app import APP_DIR, BIN_DIR, LIB_DIR, DEFAULT_CONFIG

from usp.tree import sitemap_tree_for_homepage  #  ultimate_sitemap_parser

import ctools.lock
import ctools.env
import ctools.clogging as clogging
import ctools.dbfile as dbfile

DEBUG_DEFAULT = False
DEFAULT_SITE = 'trsearch.simson.net'
debug = os.environ.get("DEBUG", DEBUG_DEFAULT )

import app.config
import app.search

DBWRITER_FNAME = os.path.join( os.environ['HOME'], 'dbwriter.bash')

def flatten(xs):
    ys = []
    for x in xs:
        ys.extend(x)
    return ys

def safe_len(x):
    return None if x is None else len(x)

def safe_int(x):
    try:
        return int(x)
    except (TypeError,AttributeError) as e:
        return 0

def clean_link(url, link):
    link = link.strip()
    # Remove // if it looks like we will get one (through a link error)
    if url.endswith('/') and link.startswith('/'):
        link = link[1:]
    u2 = urllib.parse.urljoin(url,link)
    # Remove from # to end
    hloc = u2.find('#')
    if hloc>0:
        u2 = u2[0:hloc]
    return canonicalize_url(u2)


def response_is_pdf(response):
    try:
        return response.headers['Content-Type'] == 'application/pdf'
    except KeyError:
        return False


class FakeResponse:
    __slots__ = ['headers','content','status_code','url']
    def __init__(self, *, fname=None, status_code=None,headers=None,content=None,url=None):
        if fname:
            with open(fname) as f:
                self.content = f.read()
            self.status_code = 200
            self.url = "file://" + fname
        if headers:
            self.headers       = json.loads(headers)
        if content:
            self.content = content
            self.status_code = 200
        if status_code:
            self.status_code = 200
        if url:
            self.url = url

class FakeSitemap:
    def __init__(self, *, url, last_modified):
        self.url = canonicalize_url(url)
        self.last_modified = last_modified

class DBTool:
    def __init__(self, *, cfg, auth, quiet=False):
        self.cfg  = cfg
        self.auth = auth
        self.quiet = quiet
        assert self.auth.prefix!=''

    def add_sitemap_page(self, page):
        """Add a URL to the articles table. It will be fetched later.
        @param page.url - pagemap URL
        @param page.sitemap_last_modified - pagemap sitemap_last_modified
        """
        logging.debug("add_sitemap_page(%s)",page)
        try:
            curl = canonicalize_url(page.url)
            dbfile.DBMySQL.csfr(self.auth,
                                f"""INSERT INTO {self.auth.prefix}articles (url, url_sha1, sitemap_last_modified, dist)
                                VALUES (%s, SHA1(%s), %s, 1) ON DUPLICATE KEY UPDATE sitemap_last_modified=%s,dist=1""",
                                (curl, curl, page.last_modified, page.last_modified))
        except pymysql.err.DataError as e:
            logging.error("e=%s url=%s",str(e),canonicalize_url(page.url))
            raise

    def update_url_content( self, response ):
        """Stores the response into the articles table.
        Sets dateDownloaded() to indicate that we got it.
        Leaves valid because we haven't decided what to do with it yet.
        NOTE: Currently hard-coded not to save PDFs.
        """
        cmd  = f"UPDATE {self.auth.prefix}articles SET dateDownloaded=now(), http_status_code=%s, http_headers=%s"
        args = [response.status_code, json.dumps(response.headers,default=str)]

        if SAVE_HTTP_CONTENT and (response_is_pdf(response)==False or SAVE_PDF_CONTENT) and response.status_code==200:
            compressed_content = zlib.compress(response.content)
            if len(compressed_content) > MAX_SIZE_CONTENT_COMPRESSED:
                logging.warning("%s content length=%s compressed length=%s removing",
                                response.url, len(response.content), len(compressed_content))
                cmd += ", http_content_compressed=NULL"
            else:
                cmd += ", http_content_compressed=%s"
                args.append(compressed_content)
        cmd += " WHERE url=%s"
        args.append(canonicalize_url(response.url))
        logging.debug("url=%s http_status_code=%s",response.url, response.status_code)
        dbfile.DBMySQL.csfr(self.auth, cmd, args)

    def fetch_url(self, url):
        """Fetch a URL, store the result in the articles table, and return the response.
        Currently, a bad response will overwrite a good response. We can add versioning to the table later.
        """
        logging.info("fetch %s",url)
        try:
            response = requests.get(url, allow_redirects=False)
            logging.info("response: %s ",response)
            logging.info("response: %s len(response.content)=%s",response,len(response.content))
            self.update_url_content( response )
            if response.status_code >= 400:
                dbfile.DBMySQL.csfr(self.auth,
                                    f"""UPDATE {self.auth.prefix}articles SET valid={article.VALID_FORBIDDEN}, dateFailed=now() WHERE url=%s""",
                                    (url,))
                return None
            return response
        except (requests.exceptions.ConnectionError,requests.exceptions.MissingSchema) as e:
            """Note in database that an error  resulted"""
            logging.error("url=%s e=%s",url,e)
            dbfile.DBMySQL.csfr(self.auth,
                                f"""UPDATE {self.auth.prefix}articles SET valid=0, dateFailed=now() WHERE url=%s""",
                                (url,))
            return None


    def index_redirect(self, url, response):
        """ Add to links the redirect """
        location = response.headers['Location']
        url2 = canonicalize_url(urllib.parse.urljoin(url, location))
        logging.debug("url=%s location=%s url2=%s",url,location,url2)
        dbfile.DBMySQL.csfr(self.auth,
                            f"""UPDATE {self.auth.prefix}articles SET valid={article.VALID_REDIRECT} where url=%s""",
                            (url,))
        dbfile.DBMySQL.csfr(self.auth,
                            f"""INSERT INTO {self.auth.prefix}links (articleid, url, absoluteurl)
                            VALUES ((select id from {self.auth.prefix}articles where url=%s), %s, %s) """,
                            (url, location, url2))

    def update_article_content(self, url, art):
        datePublished = art.datePublished
        if datePublished is None:
            res = dbfile.DBMySQL.csfr(self.auth,f"SELECT sitemap_last_modified, http_headers from {self.auth.prefix}articles where url=%s",(url,))
            if res:
                datePublished = res[0][0]
                if datePublished is None:
                    headers = json.loads(res[0][1])
                    if 'last-modified' in headers:
                        datePublished = headers['last-modified']
            if datePublished is None:
                datePublished=datetime.datetime.now()
            logging.warning("url=%s datePublished is NONE title=%s using %s",url,art.title,datePublished)

        # Check to see if bodyhash is already in the database. If set, set valid=2 and do not save the body (we may later want to wipe the compressed htpt content
        res = dbfile.DBMySQL.csfr(self.auth,f"SELECT url from {self.auth.prefix}articles where body_hash=%s and url!=%s and valid=1",(art.body_hash,url))
        if res:
            logging.debug("%s already in database as %s",url,res[0][0])
            dbfile.DBMySQL.csfr(self.auth,
                                f"""UPDATE {self.auth.prefix}articles SET valid={article.VALID_DUPLICATE}, http_content_compressed=NULL where url=%s""",(url,))
            raise article.AbortInsert()

        # Update the database
        dbfile.DBMySQL.csfr(self.auth,
                            f"""
                            UPDATE {self.auth.prefix}articles
                            SET datePublished=%s, valid=%s, libmagic_mimetype=%s, libmagic_description=%s, title=%s, author=%s, body=%s, body_hash=%s, words=%s
                            WHERE url=%s
                            """,(datePublished, art.valid, art.libmagic_mimetype, art.libmagic_description, art.title, art.author, art.body, art.body_hash,art.words(),
                             url))


    def update_article_metadata( self, url, art ):
        ret = dbfile.DBMySQL.csfr(self.auth,f"""SELECT id from {self.auth.prefix}articles where url=%s""",(url,))
        if len(ret)!=1:
            logging.error("article URL=%s does not exist", url)
            return

        articleid = ret[0][0]
        cmd  = (f"""INSERT INTO {self.auth.prefix}metadata (articleid,k,v) VALUES """
                   + ",".join(["(%s,%s,%s)"] * art.metadata_count()))
        args = [ (articleid, str(o[0])[0:article.MAX_K], str(o[1]))[0:article.MAX_V] for o in art.metadata.items() ]
        args = flatten( args )

        # Delete the old and insert the new
        dbfile.DBMySQL.csfr(self.auth,
                                f"""DELETE FROM {self.auth.prefix}metadata WHERE articleid = %s """,(articleid,))
        if args:
            try:
                dbfile.DBMySQL.csfr(self.auth, cmd, args)
            except pymysql.err.DataError as e:
                logging.error("e=%s explain: %s",str(e),dbfile.DBMySQL.explain(cmd,args))
                raise

    def update_article_fullnames( self, url, art ):
        ret = dbfile.DBMySQL.csfr(self.auth,f"""SELECT id from {self.auth.prefix}articles where url=%s""",(url,))
        if len(ret)!=1:
            logging.error("article URL=%s does not exist", url)
            return

        articleid = ret[0][0]
        cmd  = (f"""INSERT INTO {self.auth.prefix}fullnames (articleid,fullname) VALUES """
                   + ",".join(["(%s,%s)"] * len(art.fullnames)))
        args = [ (articleid, name) for name in art.fullnames ]
        args = flatten( args )
        # Delete the old and insert the new
        dbfile.DBMySQL.csfr(self.auth,
                                f"""DELETE FROM {self.auth.prefix}fullnames WHERE articleid = %s """,(articleid,))
        if args:
            dbfile.DBMySQL.csfr(self.auth, cmd, args)

    def update_article_links( self, url, art ):
        ret = dbfile.DBMySQL.csfr(self.auth,f"""SELECT id from {self.auth.prefix}articles where url=%s""",(url,))
        if len(ret)!=1:
            logging.error("article URL=%s does not exist", url)
            return

        articleid = ret[0][0]
        cmd  = (f"""INSERT INTO {self.auth.prefix}links (articleid, url, absoluteurl) VALUES """
                   + ",".join([" ( %s, %s, %s ) "] * len(art.links)))
        args = [ (articleid, link, clean_link(url,link)) for link in art.links ]
        args = flatten( args )
        # Delete the old and insert the new
        dbfile.DBMySQL.csfr(self.auth,
                                f"""DELETE FROM {self.auth.prefix}links WHERE articleid = %s """,(articleid,))
        if args:
            dbfile.DBMySQL.csfr(self.auth, cmd, args)

    def index_response(self, url, response ):
        """ If we have a valid response (code 200), process the response """
        art      = article.FromResponse( response )
        try:
            self.update_article_content( url, art )
            self.update_article_metadata( url, art )
            self.update_article_fullnames( url, art )
            self.update_article_links( url, art )
        except article.AbortInsert:
            pass


    def index_url(self, url, add_url=True):
        """ Given a URL:
        1 - Add to the database if not present (if add_url is True)
        2 - Fetch the URL
        3 - Decode the response.
        4 - update the metadata in the database
        """
        logging.info("index url=%s add_url=%s",url,add_url)
        if add_url:
            self.add_sitemap_page( FakeSitemap(url=url, last_modified = datetime.datetime.now()))
        response = self.fetch_url( url )
        if response is None:
            return
        if response.status_code in [200]:
            self.index_response( url, response )
        elif response.status_code in [301,302,303]:
            self.index_redirect( url, response )
        else:
            raise RuntimeError("response="+str(response))
        #self.index_error( url, response )


    def reindex(self, homepage):
        """Downloads a new sitemap"""
        logging.info("==reindex==")

        # Generate initial stats
        (start_total,start_downloaded)  = dbfile.DBMySQL.csfr(self.auth,
                                       f"""SELECT COUNT(*),
                                                  SUM( IF (dateDownloaded is not null,1,0))
                                           FROM {self.auth.prefix}articles
                                        """)[0]
        start_downloaded = safe_int(start_downloaded)
        msg1 = f"At start: start_total={start_total} start_downloaded={start_downloaded}"
        tree = sitemap_tree_for_homepage(homepage)
        pages_added = 0

        # Get the start count of URLs in the articles

        # get a list of URLs that don't need to be refreshed. This may need a LIMIT statement at some point?
        existing_sitemap = {row[0]:row[1] for row in dbfile.DBMySQL.csfr(self.auth, f"""SELECT url,sitemap_last_modified FROM {self.auth.prefix}articles """)}

        tree = sitemap_tree_for_homepage(homepage)
        # A damaged its sitemap and had multiple entries for each URL, all with different last_modified.
        # So simplify the sitemap
        duplicates_in_sitemap = 0
        all_pages = dict()
        for page in tree.all_pages():
            url = canonicalize_url(page.url)
            if url in all_pages:
                duplicates_in_sitemap += 1
            if (url not in all_pages) or (page.last_modified > all_pages[url].last_modified):
                all_pages[url] = page

        skip_count = 0
        if len(all_pages)==0:
            print("Sitemap is null. adding home page:")
            all_pages[homepage] = FakeSitemap(url=homepage, last_modified=datetime.datetime.now())

        for page in all_pages.values():
            try:
                # if the sitemap in our database has a date the same or greater than the one in the current sitemap, ignore it.
                if page.last_modified.replace(tzinfo=None) <= existing_sitemap[canonicalize_url(page.url)]:
                    logging.debug("skip page=%s",page)
                    skip_count += 1
                    continue
            except (AttributeError,KeyError) as e:
                pass
            self.add_sitemap_page(page)
            pages_added += 1

        # Generate end stats
        (end_total,end_downloaded) = dbfile.DBMySQL.csfr(self.auth,
                                      f"""SELECT COUNT(*), SUM( IF (dateDownloaded is not null,1,0))
                                          FROM {self.auth.prefix}articles""")[0]
        end_downloaded = safe_int(end_downloaded)
        msg2 = f"At end: end_total={end_total} end_downloaded={end_downloaded}"
        if start_total != end_total and not self.quiet:
            print(f"New pages found in sitemap for {homepage}")
            print(msg1)
            print(msg2)

    def refresh(self, *, limit=0):
        logging.info("==refresh==")
        refreshed = set()
        """For all URLs in the database that need to be processed, fetch the page, parse the page, and update the database """
        REFRESH_WHERE = """
              (valid is NULL)
           OR (sitemap_last_modified < NOW() and dateDownloaded < sitemap_last_modified)
           """
        to_refresh = dbfile.DBMySQL.csfr(self.auth,
                                             f"""SELECT count(*) FROM {self.auth.prefix}articles
                                                 WHERE {REFRESH_WHERE}""")[0][0]

        count = 0
        logging.info("to_refresh count=%s",to_refresh)
        prev_url = None
        while True:
            # TODO: Get more than 1 at a time and batch them to multiple threads
            urls = dbfile.DBMySQL.csfr(self.auth,
                                           f"""SELECT url FROM {self.auth.prefix}articles
                                               WHERE {REFRESH_WHERE}
                                               ORDER BY dateFailed limit 1
                                            """)
            if not urls:
                logging.info("end of search")
                break
            url = urls[0][0]
            logging.info("refresh %s",url)
            if not self.quiet:
                print(url)
            if url in refreshed:
                raise RuntimeError("repeated url="+url)
            refreshed.add(url)
            count += 1
            self.index_url( url, add_url=False)
            if limit>0 and count>=limit:
                logging.warning("Limit reached")
                break

    def reparse(self, *, limit=0):
        logging.info("==reparse==")
        count = 0
        urls = dbfile.DBMySQL.csfr(self.auth,
                                       f"""SELECT url FROM {self.auth.prefix}articles
                                       WHERE url IS NOT NULL AND http_content_compressed IS NOT NULL""")
        print(f"total urls: {len(urls)}")
        for (count,(url,)) in enumerate(urls,1):
            rows = dbfile.DBMySQL.csfr(self.auth,
                                       f"""SELECT http_status_code,http_headers,http_content_compressed
                                       FROM {self.auth.prefix}articles where url=%s""",
                                       (url,))
            if len(rows)!=1:
                logging.error("Could not fetch url=%s",url)
                continue
            (http_status_code,http_headers,http_content_compressed) = rows[0]
            if not self.quiet:
                print(f"{count}/{len(urls)} {url}")
            self.index_response( url, FakeResponse( status_code=http_status_code,headers=http_headers,content=zlib.decompress(http_content_compressed),url=url ))
            if limit>0 and count>=limit:
                logging.warning("Limit reached")
                break

    def spider(self, limit=0):
        logging.info("==spider %d==",limit)
        prefix = self.auth.prefix
        domain = cfg.domain()
        c0 = dbfile.DBMySQL.csfr(self.auth,f"SELECT COUNT(*) from {prefix}articles",())[0][0]
        print(f"Before: {c0}")
        cmd = f"""INSERT INTO {prefix}articles (url, url_sha1, dist)
              SELECT DISTINCT absoluteurl, SHA1(absoluteurl), dist+1
              FROM {prefix}links a LEFT JOIN {prefix}articles b ON a.articleid=b.id
                    WHERE (b.valid IN (1,3))
                          AND (SHA1(absoluteurl) NOT IN (SELECT url_sha1 from {prefix}articles))
                          AND absoluteurl REGEXP '^https?://(www.)?{domain}'
              LIMIT {limit}
        """
        print(cmd)
        dbfile.DBMySQL.csfr(self.auth,cmd,())
        c1 = dbfile.DBMySQL.csfr(self.auth,f"SELECT COUNT(*) from {self.auth.prefix}articles",())[0][0]
        print(f"After: {c1}  delta: {c1-c0}")

def create( auth, table=None, createdb=False ):
    logging.info("== create %s ==",table)

    if createdb:
        # create a sudo mysql subprocess
        cmd = "create database XXX; grant all on search_bbc.* to 'dbwriter'@'%'; grant select on search_bbc.* to 'dbreader'@'%';"


    db = dbfile.DBMySQL( auth )
    creates = []
    lines = []
    CREATE_TABLE  = re.compile('CREATE TABLE `([^`]*)`',re.I)
    REFERENCES = re.compile('REFERENCES `([^`]*)`',re.I)
    CONSTRAINT = re.compile('CONSTRAINT `([^`]*)`',re.I)
    with open(SCHEMA_FILE) as f:
        for line in f:
            for r in [CREATE_TABLE, REFERENCES, CONSTRAINT]:
                m = r.search(line)
                if m:
                    line = line.replace(m.group(1),auth.prefix+m.group(1))
                if m and r==CREATE_TABLE:
                    in_table = m.group(1)
                    print("In table",in_table)
            lines.append(line)
            if ';' in line:
                in_table = None
    new_schema = "".join(lines)
    print( new_schema )
    db.create_schema( new_schema )

def drop( auth ):
    # Need two passes to drop articles last
    logging.warning("== drop %s ==",auth.prefix)
    dropped = set()
    tables = [row[0] for row in dbfile.DBMySQL.csfr(auth, f"show tables like '{auth.prefix}%'")]
    for pass_ in (1,2):
        for table in tables:
            if (('article' in table) and pass_==1) or (table in dropped):
                continue
            cmd = "DROP TABLE "+table
            print(cmd)
            dbfile.DBMySQL.csfr( auth, cmd )
            dropped.add(table)
        time.sleep(1)


def search_demo(auth, query):
    def demo(func, name, q):
        print( name )
        res = func( auth, q )
        print("Results:",len(res))
        for art in res[0:5]:
            print(art)
        print()

    for (f,n) in [ (app.search.author,"author"),
                   (app.search.headline, "headline"),
                   (app.search.body, "body")]:
        demo(f, n, query)

def everyart(auth):
    """Mostly this is for testing"""
    from spacy_ner import spacy_ner
    RE_COMBINE_WHITESPACE = re.compile(r"\s+")
    db = dbfile.DBMySQL( auth )
    WHERE=' where words is null and body is not null'
    db = dbfile.DBMySQL(auth)
    c  = db.cursor(pymysql.cursors.DictCursor)
    c2  = db.cursor(pymysql.cursors.DictCursor)
    c.execute(f"""SELECT * from {auth.prefix}articles {WHERE}""")
    for row in c:
        body = RE_COMBINE_WHITESPACE.sub(" ",row['body']).strip()
        print(row['url'],row['title'])
        #spacy_ner(body)
        #flair_ner(body)
        words = body.count(' ')
        c2.execute(f"""UPDATE {auth.prefix}articles set words=%s where id=%s""",
                       (words,row['id']))


if __name__=="__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Download sitemap recursively', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--reindex', action='store_true', help='Download sitemap and load into MySQL database')
    parser.add_argument('--refresh', help='download the TR articles for which we have no headline', action='store_true')
    parser.add_argument('--reparse', help='for each web page in the database, reparse it', action='store_true')
    parser.add_argument('--decode_file', help='Decode article saved in a file')
    parser.add_argument('--reparse_url', help='Read from database and reparse')
    parser.add_argument('--decode_url', help='Fetch a URL and report its contents')
    parser.add_argument('--index_url', help='Manually add a URL to the index (if not present), download the url and re-index it')
    parser.add_argument('--envfile', help='dbwriter bash environment setting file', default=DBWRITER_FNAME)
    parser.add_argument('--config', help='trsearch config file', default=DEFAULT_CONFIG)
    parser.add_argument('--search', help='Try all search systems')
    parser.add_argument('--get', help='config value to get')
    parser.add_argument('--quiet', help='do not print progress info', action='store_true')
    parser.add_argument('--create', help='Create SQL Schema', action='store_true')
    parser.add_argument('--createdb', help='Also create the database', action='store_true')
    parser.add_argument('--createtable', help='Only create this table')
    parser.add_argument('--site', help='which site we are using', default=DEFAULT_SITE)
    parser.add_argument('--allsites', help='loop for all sites', action='store_true')
    parser.add_argument('--limit', help='specify max # of refresh to do', type=int, default=0)
    parser.add_argument('--everyart', help='run the "everyart" function on every body in the database', action='store_true')
    parser.add_argument('--drop', help='Drop tables for prefix', action='store_true')
    parser.add_argument('--nolock', help='do not lock the script', action='store_true')
    parser.add_argument('--mysql', help='Give me a MySQL prompt with dbwriter', action='store_true')
    parser.add_argument('--spider', help='Select SPIDER links into articles table for primary domain.', type=int, default=0)

    clogging.add_argument(parser, loglevel_default='WARNING')
    args = parser.parse_args()
    clogging.setup(level=args.loglevel)

    if args.decode_file or args.decode_url or args.reparse_url:
        if args.decode_file:
            url = 'file://' + args.decode_file
            response = FakeResponse( fname=args.decode_file, url=url )
        elif args.reparse_url:
            cfg = app.config.TRSConfig( fname=args.config, site=args.site )
            auth = cfg.dbwriter()
            if args.reparse_url[0] in "0123456789":
                row = dbfile.DBMySQL.csfr( auth, f"select * from {auth.prefix}articles limit 1,%s",(int(args.reparse_url),),asDicts=True)[0]
            else:
                row = dbfile.DBMySQL.csfr( auth, f"select * from {auth.prefix}articles where url=%s",(args.reparse_url,),asDicts=True)[0]
            try:
                content = zlib.decompress(row['http_content_compressed'])
            except TypeError as e:
                logging.error("http_content_compressed for %s cannot be decompressed",args.reparse_url)
                raise
            response = FakeResponse( content=content, url=args.reparse_url )
        else:
            response = requests.get(args.decode_url, allow_redirects=False)
        art      = article.FromResponse( response )
        print("art:",art)
        print("title:",art.title)
        print("author:",art.author)
        print("datePublished:",art.datePublished)
        print("METADATA:")
        for (k,v) in sorted(art.metadata.items()):
            print(f"{k:20} ==> {v}")
        print("NAMES:")
        for name in sorted(art.fullnames):
            print(f'  >{name}<  ')
        print("LINKS:")
        for (link) in sorted(art.links):
            print(f"   {link}")
        exit(0)

    cfg = app.config.TRSConfig( fname=args.config, site=args.site )

    if args.get:
        # Just get a piece of the config file (for use in bash scripts)
        print(cfg.expand( args.site ,args.get))
        exit(0)

    if args.drop:
        dbwriter = cfg.dbwriter()
        yes = input('Really drop tables for '+args.site+str(dbwriter))
        if yes[0].lower()=='y':
            drop( dbwriter)

    if args.create or args.createtable:
        create( cfg.dbwriter(), table=args.createtable, createdb=args.createdb )

    # Filter out usp.fetch_parse and usp.helpers
    # https://stackoverflow.com/questions/53249304/how-to-list-all-existing-loggers-using-python-logging-module

    # Disable error reporting in these modules
    # by calling getLogger(), we create the loggers that do not exist at the moment.
    # This is why we do this, rather than just running logger.addFilter()
    # Only do this if loglevel is not INFO or DEBUG
    if args.loglevel not in ['INFO','DEBUG']:
        logging.getLogger("usp.fetch_parse").addFilter( lambda record: False)
        logging.getLogger("usp.helpers").addFilter( lambda record: False)
        logging.getLogger("bs4.dammit").addFilter( lambda record: False)

    if args.search:
        search_demo( cfg.dbreader( args.site ) , args.search)
        exit(0)

    if args.allsites:
        sites = cfg.all_sites()
    else:
        sites = [args.site]

    if not args.nolock:
        ctools.lock.lock_script()

    for site in sites:
        auth = cfg.dbwriter( site )
        logging.debug("site=%s auth=%s",site,auth)
        dbtool = DBTool( cfg=cfg, auth=auth, quiet=args.quiet)

        if args.reindex:
            dbtool.reindex( cfg.get('homepage') )

        if args.spider:
            dbtool.spider( args.spider )

        if args.refresh:
            dbtool.refresh( limit=args.limit )

        if args.reparse:
            dbtool.reparse( limit=args.limit )

        if args.index_url:
            dbtool.index_url( args.index_url)
            exit(0)

        if args.everyart:
            everyart( auth )

        if args.mysql:
            cmd = ['mysql','-u'+auth.user,'-p'+auth.password,'-h'+auth.host,auth.database]
            print(" ".join(cmd))
            subprocess.Popen(cmd,stdin=sys.stdin,stdout=sys.stdout).wait()
