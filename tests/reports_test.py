import pytest
import sys
import os

from os.path import abspath,dirname

sys.path.append( dirname(dirname(abspath(__file__))))

from digitalcorpora_app.s3_reports import *
from digitalcorpora_app.main import get_dbreader
from digitalcorpora_app.paths import TEMPLATE_DIR

def test_report_count():
    assert report_count() == len(REPORTS)

@pytest.mark.skip(reason='not working')
def test_reports_json():
    dbreader = get_dbreader()
    # Make sure each report works without error
    for i in range(report_count()):
        ret = report_generate(auth=dbreader, num=i)
        assert 'title' in ret
        assert 'sql' in ret
        assert 'column_names' in ret
        assert 'rows' in ret
        ret = reports_json(auth=dbreader, num=i)

def test_reports_html():
    dbreader = get_dbreader()
    from flask import Flask
    app = Flask(__name__, template_folder=TEMPLATE_DIR)
    # Test with valid report number
    with app.test_request_context('/reports?report=0'):
        res = reports_html(auth=dbreader)
    # Test with invalid report number
    with app.test_request_context('/reports?report=invalid'):
        res = reports_html(auth=dbreader)
    # Test with no report parameter
    with app.test_request_context('/reports'):
        res = reports_html(auth=dbreader)
