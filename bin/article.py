################################################################
## article abstrafction

import sys
import os
import configparser
import re
import hashlib
import logging
import json
import datetime

from collections import defaultdict
from bs4 import BeautifulSoup

counts = defaultdict(int)
MAX_FORBIDDEN = 10
MAX_K = 256
MAX_V = 32768
MAX_URL = 8192
MAX_TITLE = 16777215
MAX_AUTHOR = 16777215
MAX_BODY = 16777215
MAX_LIBMAGIC_DESCRIPTION = 256

DHS_DATEPUBLISHED = 'dhs:datePublished'
DATE_KEYS = ['datePublished', 'article:published_time', 'dateModified',
             'article:modified_time', DHS_DATEPUBLISHED]
AUTHOR_KEYS = ['author','dc:author','DC.creator']

RE_COMBINE_WHITESPACE = re.compile(r"\s+")

from functools import cache

__version___="0.9.0"

## VALID CODES
VALID_NOT_LOADED = None
VALID_NOT_PARSED = 0
VALID_VALID      = 1
VALID_DUPLICATE  = 2
VALID_REDIRECT   = 3
VALID_FORBIDDEN  = 4

## Singleton works with python >= 3.9
@cache
class MyMagic:
    def __init__(self):
        import magic
        self.mgk_description = magic.Magic(uncompress=True)
        self.mgk_mime = magic.Magic(mime=True,uncompress=True)

class AbortInsert(Exception):
    """Do not continuing inserting article into database"""
    pass

class Article:
    __slots__ = ['metadata', '_title', '_author', '_libmagic_description', '_url', '_body', '_datePublished', 'valid', 'body_sha1', 'libmagic_mimetype', 'fullnames', 'links']
    def __init__(self, url=None):
        self.metadata = defaultdict(str)
        self._title = None
        self._author = None
        self._datePublished = None
        self._libmagic_description = None
        self._url    = url
        self._body = None
        self.valid = VALID_NOT_PARSED
        self.body_sha1 = None
        self.libmagic_mimetype = None
        self.fullnames = set()
        self.links = set()

    def __repr__(self):
        if self.body is None:
            blen = -1
        else:
            blen = len(self.body)

        return(f"Article< metadata:{self.metadata} title={self.title} valid={self.valid} len(body)={blen} mimetype={self.libmagic_mimetype}>")

    def __setitem__(self, key, value):
        if key=='body':
            self.body = value
            return
        self.metadata[key] = value

    def __getitem__(self, key):
        if key in self.metadata:
            return self.metadata[key]
        raise KeyError(key)

    ################################################################
    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, title):
        self._title = title[:MAX_TITLE].strip()
        self.valid = VALID_VALID

    @property
    def author(self):
        return self._author

    @author.setter
    def author(self, author):
        self._author = author[:MAX_AUTHOR].strip()
        if self._author.lower().startswith("by "):
            self._author = self._author[3:]

    @property
    def libmagic_description(self):
        return self._libmagic_description

    @libmagic_description.setter
    def libmagic_description(self, libmagic_description):
        self._libmagic_description = libmagic_description[:MAX_LIBMAGIC_DESCRIPTION]

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, url):
        self._url = url[:MAX_URL]

    @property
    def body(self):
        return self._body

    @body.setter
    def body(self, body):
        self._body = body[:MAX_BODY]
        self.valid = VALID_VALID

    @property
    def datePublished(self):
        if self._datePublished:
            return self._datePublished
        for k in DATE_KEYS:
            if k in self.metadata:
                return self.metadata[k]
        return None

    @datePublished.setter
    def datePublished(self, dt):
        self._datePublished = dt

    @property
    def body_hash(self):
        if self.body_sha1 is None and self.body is not None:
            sha1 = hashlib.sha1()
            sha1.update(self.body.encode('utf-8'))
            self.body_sha1 = sha1.hexdigest()
        return self.body_sha1

    ################################################################

    def get(self, key):
        """Return metadata"""
        return self.metadata.get(key)

    def metadata_count(self):
        return len(self.metadata)

    def mimetype(self):
        return self.metadata.get('mimetype',None)

    def set_mimetype(self,mimetype):
        self.metadata['mimetype'] = mimetype

    def del_mimetype(self):
        try:
            del self.metadata['mimetype']
        except (AttributeError,KeyError) as e:
            pass

    ### Parsing Logic
    def parse_yoast( self, soup ):
        """See if there is a yoast object"""
        yoast = None
        yoast = soup.find("script", id="NewsArticle")
        if yoast is None:
            yoast = soup.find("script", attrs={'type':'application/ld+json', 'class':'yoast-schema-graph'})
        if yoast is None:
            return

        thing = json.loads(yoast.text)

        for (key,value) in thing.items():
            if key=='author':
                try:
                    self.metadata['author'] = thing['author']['name']
                    self.author = thing['author']['name']
                except KeyError as e:
                    self.author = str(value)
            else:
                self.metadata[key] = value


        if '@graph' in self.metadata:
            v2 = self.metadata['@graph'][2]
            for (k,v) in v2.items():
                self.metadata[k] = v
            del self.metadata['@graph']

    def parse_DC( self, soup):
        """See if there are doublin core properties"""
        for meta in soup.find_all('meta'):
            logging.debug("meta=%s",meta)
            if 'http-equiv' in meta.attrs:
                continue
            if 'charset' in meta.attrs:
                continue
            if 'content' in meta.attrs and 'itemprop' in meta.attrs:  # https://nsa.gov/ thing
                continue
            key   = meta.attrs.get('property', meta.attrs.get('name', None))
            value = meta.attrs.get('content', meta.attrs.get('scheme',None))
            if (key is None):
                logging.warning("no key in: %s",meta)
            elif (value is None):
                logging.warning("no value in: %s",meta)
                self.metadata[key] = True
            else:
                self.metadata[key] = value

        if self.title is None:
            try:
                if 'og:title' in self.metadata and len(self.metadata['og:title'])>0:
                    self.title = self.metadata['og:title']
            except KeyError:
                pass

    def parse_links( self, soup):
        self.links = set([link.get('href') for link in soup.findAll('a') if link.get('href') is not None])
        logging.debug("%s links found",len(self.links))

    def parse_soup(self, content ):
        try:
            soup = BeautifulSoup( content, 'html.parser' )
        except TypeError:
            return

        logging.debug("parse_soup")
        self.parse_yoast( soup )
        self.parse_DC( soup )
        self.parse_links( soup )

        # See if there is a posted-on class
        tag = soup.find('time', attrs={'class':'published'})
        if tag and ('datePublished' not in self.metadata) and 'datetime' in tag.attrs:
            self.metadata['datePublished'] = tag.attrs['datetime']

        if self.title is None:
            try:
                self.title = soup.find('title').text.strip()
            except AttributeError:
                raise
                pass
        if self.title=="":
            self.title=self.url

        # Look for special content
        content = soup.find("div",id="content--body")
        if content:
            self.body = ' '.join(content.stripped_strings)

        if self.body is None:
            try:
                self.body = ' '.join(soup.body.stripped_strings)
            except AttributeError:
                pass

        for key in AUTHOR_KEYS + [key for key in self.metadata.keys() if 'author' in key.lower()]:
            if (self.author is None) and (key in self.metadata) and isinstance(self.metadata['author'],str):
                self.author = self.metadata[key]
                break

        # Special code for bbcmag.com
        if (self.author is None):
            c1 = soup.find('div',attrs={'class':'article-author'})
            if c1:
                c2 = soup.find('span',attrs={'class':'article-author-byline'})
                if c2:
                    self.author = c1.text.replace(c2.text,'')
                else:
                    self.author = c1.text

        if (self.datePublished is None):
            c1 = soup.find('div',attrs={'class':'article-date'})
            if c1:
                w = c1.text.strip().split()
                try:
                    self.datePublished = datetime.datetime.strptime(w[0]+" "+w[1],"%B %Y")
                except (ValueError,IndexError) as e:
                    pass



        # Special code for DHS.gov
        dhs_date_div = soup.find("div", class_="last-updated")
        if dhs_date_div:
            m = re.search(r"(\d\d)/(\d\d)/(\d\d\d\d)",dhs_date_div.text.replace("\n"," "))
            if m:
                self.metadata[DHS_DATEPUBLISHED] = m.group(3) + '-' + m.group(1) + '-' + m.group(2)

    def parse_response(self, response):
        self.libmagic_description     = MyMagic().mgk_description.from_buffer(response.content)
        self.libmagic_mimetype        = MyMagic().mgk_mime.from_buffer(response.content)

        logging.debug("libmagic_mimetype = %s libmagic_description=%s", self.libmagic_mimetype, self.libmagic_description)

        # If this is text...
        if self.libmagic_mimetype=='text/plain' or self.libmagic_mimetype[0:3] in ['PDF','JPE','JPG','PNG']:
            self.body = self.content
            return

        # See if we can make a soup
        self.parse_soup( response.content )

    def apply_ner(self):
        if self.body is not None:
            from spacy_ner import spacy_ner
            self.fullnames = spacy_ner( self.body, maxlen=63 )
            logging.info("fullnames: %s",self.fullnames)


    RE_COMBINE_WHITESPACE = re.compile(r"\s+")
    def words(self):
        if self.body is None:
            return None
        return self.RE_COMBINE_WHITESPACE.sub(" ",self.body).strip().count(' ')

def FromResponse( response ):
    logging.debug("response=%s",response)
    obj = Article(url=response.url)
    counts[int(response.status_code)] += 1
    if counts[403]>MAX_FORBIDDEN:
        raise RuntimeError("Too many forbidden "+str(counts))
    if response.status_code==200:
        obj.parse_response( response )
        obj.apply_ner()
    return obj
