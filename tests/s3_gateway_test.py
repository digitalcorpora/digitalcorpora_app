import pytest
import sys
import os

from os.path import abspath,dirname

sys.path.append( dirname(dirname(abspath(__file__))))

from s3_gateway import *
import bottle_app

def test_s3_gateway_files():
    assert INDEX_S3 is not None
    assert ERROR_404 is not None

@pytest.fixture
def dirs_and_files():
    (dirs,files) = s3_get_dirs_files("digitalcorpora","tests/")
    return (dirs,files)

def test_s3_get_dirs_files_test(dirs_and_files):
    (dirs,files) = dirs_and_files
    assert dirs==[{'Prefix': 'tests/subdir with-space/'},
                  {'Prefix': 'tests/subdir1/'}]
    keys = list(sorted([obj['Key'] for obj in files]))
    assert 'tests/file1.txt' in keys
    assert 'tests/file2.txt' in keys
    assert 'tests/hello_world.txt' in keys

def test_s3_to_link(dirs_and_files):
    (dirs,files) = dirs_and_files
    gtw_url = 'http://127.0.0.1/'
    aws_url = 'https://digitalcorpora.s3.amazonaws.com/'
    assert s3_to_link(gtw_url, dirs[0])  == gtw_url + 'subdir%20with-space/'
    assert s3_to_link(gtw_url, dirs[1])  == gtw_url + 'subdir1/'
    assert s3_to_link(gtw_url, files[0]) == aws_url + 'tests/file1.txt'

def test_redirect():
    """A direct download should instead redirect to Amazon"""

def test_annotate_s3files():
    objs = []
    annotate_s3files(None,objs)
    assert objs==[]

TEST_PATHS = ['corpora/files/CC-MAIN-2021-31-PDF-UNTRUNCATED/',
              'corpora/files/CC-MAIN-2021-31-PDF-UNTRUNCATED'
              ]
def test_s3_list_prefixes():
    """ Right now we are just checking to make sure it doesn't crash """
    dbreader = bottle_app.get_dbreader()
    for path in TEST_PATHS:
        ret = s3_list_prefix(DEFAULT_BUCKET, path)
        url = f'https://downloads.digitalcorpora.org/{path}'
        ret = s3_app(bucket=DEFAULT_BUCKET, quoted_prefix=urllib.parse.quote(path), url=url, auth=dbreader)
