import pytest
import sys
import os

from os.path import abspath,dirname

sys.path.append( dirname(dirname(abspath(__file__))))

from boddle import boddle

import s3_reports
import bottle_app

def test_report_count():
    assert s3_reports.report_count() == len(s3_reports.REPORTS)

@pytest.mark.skip(reason='not working')
def test_reports_json():
    dbreader = bottle_app.get_dbreader()
    # Make sure each report works without error
    for i in range(s3_reports.report_count()):
        ret = s3_reports.report_generate(auth=dbreader, num=i)
        assert 'title' in ret
        assert 'sql' in ret
        assert 'column_names' in ret
        assert 'rows' in ret
        ret = s3_reports.reports_json(auth=dbreader, num=i)

def test_reports_html():
    dbreader = bottle_app.get_dbreader()
    with boddle(params={'report':'0'}):
        res = s3_reports.reports_html(auth=dbreader)

    with boddle(params={'report':'invalid'}):
        res = s3_reports.reports_html(auth=dbreader)

    with boddle(params={}):
        res = s3_reports.reports_html(auth=dbreader)
