import pytest
import sys
import os

from os.path import abspath,dirname

sys.path.append( dirname(dirname(abspath(__file__))))
import app.db_lookup

def test_db_lookup():
    objs = []
    db_lookup.annotate_s3files(None,objs)
    assert objs==[]
