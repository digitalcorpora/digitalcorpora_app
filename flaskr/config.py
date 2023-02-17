################################################################
## config file management

import sys
import os
import configparser
import re
from urllib.parse import urlparse



from . import ROOT_DIR

import ctools
import ctools.env
import ctools.dbfile

GETBASH_RE = re.compile(r'GETBASH\((.*),(.*)\)')
class TRSConfig:
    __slots__ = ['fname', 'site', 'config']
    def __init__(self, *, fname, site=None):
        """
        @param fname  - location of trsearch.in file
        @param site - default site to use
        """
        self.fname  = fname
        self.site   = site
        self.config = configparser.ConfigParser()
        self.config.read(fname)

    def __getitem__(self, key):
        return self.config[key]

    def __repr__(self):
        return f"<TRSConfig fname={self.fname} site={self.site}>"

    def sites(self):
        return self.config.sections()

    def expand(self, section, key):
        """look for GETBASH(path,variable)"""
        if section not in self.config.sections():
            print(f"fname: {self.fname} section: {section} available sections: {self.config.sections()}",file=sys.stderr)
            raise KeyError

        value = self.config[section][key]
        m = GETBASH_RE.search(value)
        if not m:
            return value
        bash_fname = m.group(1)
        bash_var   = m.group(2)
        os.environ['ROOT'] = ROOT_DIR        # set up root variable
        fname = os.path.expandvars(bash_fname)
        vars = ctools.env.get_vars( fname ) # get a dictionary with the variables
        return os.path.expandvars(vars[bash_var])

    def get(self, key):
        """Like expand, but assumes the default site"""
        return self.expand( self.site, key)

    def dbreader(self, site=None):
        """ Get the dbreader auth object for the site """
        if site is None:
            site = self.site
        return ctools.dbfile.DBMySQLAuth(
            host     = self.expand(site,'mysql_host'),
            database = self.expand(site,'mysql_database'),
            user     = self.expand(site,'dbreader_user'),
            password = self.expand(site,'dbreader_password'),
            prefix   = self.expand(site,'prefix')
        )

    def dbwriter(self, site=None):
        """ Get the dbwriter auth object for the site """
        if site is None:
            site = self.site
        return ctools.dbfile.DBMySQLAuth(
            host     = self.expand(site,'MYSQL_HOST'),
            database = self.expand(site,'MYSQL_DATABASE'),
            user     = self.expand(site,'DBWRITER_USER'),
            password = self.expand(site,'DBWRITER_PASSWORD'),
            prefix   = self.expand(site,'prefix')
        )

    def domain(self):
        home = self.expand(self.site, 'homepage')
        print("home:",home)
        p = urlparse(home)
        return p.netloc


################################################################
