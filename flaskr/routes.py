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
