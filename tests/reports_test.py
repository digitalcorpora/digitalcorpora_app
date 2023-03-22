import pytest
import sys
import os

from os.path import abspath,dirname

sys.path.append( dirname(dirname(abspath(__file__))))

import s3_reports
import test_dbreader

def test_report_count():
    assert s3_reports.report_count = len(s3_reports.REPORTS)

def test_reports_generate():
    dbreader = bottle_app.get_dbreader()
    ret = s3_reports.report_generate(auth=dbreader, num=0)
    assert 'title' in ret
    assert 'sql' in ret
    assert 'column_names' in ret
    assert 'rows' in ret
