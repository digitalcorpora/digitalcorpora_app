import pytest
import sys
import os

from os.path import abspath,dirname

sys.path.append( dirname(dirname(abspath(__file__))))
from s3_gateway import *

def test_s3_gateway_files():
    assert os.path.exists(S3_TEMPLATE_FILE)

@pytest.fixture
def dirs_and_files():
    (dirs,files) = s3_get_dirs_files("digitalcorpora","tests/")
    return (dirs,files)

def test_s3_get_dirs_files_test(dirs_and_files):
    (dirs,files) = dirs_and_files
    assert dirs==[{'Prefix': 'tests/subdir with-space/'},
                  {'Prefix': 'tests/subdir1/'}]
    keys = list(sorted([obj['Key'] for obj in files]))
    assert keys==['tests/file1.txt','tests/file2.txt']

def test_s3_to_link(dirs_and_files):
    (dirs,files) = dirs_and_files
    assert s3_to_link(dirs[0])=='http://127.0.0.1/subdir%20with-space/'
    assert s3_to_link(dirs[1])=='http://127.0.0.1/subdir1/'
    assert s3_to_link(files[0])=='https://digitalcorpora.s3.amazonaws.com/tests/file1.txt'

def test_redirect():
    """A direct download should instead redirect to Amazon"""
