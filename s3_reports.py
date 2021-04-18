"""
Generate reports.
"""

import os
import os.path
import sys

from os.path import dirname

import bottle

REPORT_TEMPLATE_FILENAME  = os.path.join(dirname(__file__), "templates/report.tpl")
REPORT = bottle.SimpleTemplate( open( REPORT_TEMPLATE_FILENAME ).read())


REPORTS = [
    ('Downloads over past week',
     """SELECT s3key,sum(bytes_sent)/max(bytes) as count,min(dtime) as first,max(dtime) as last,
        FROM downloads
        RIGHT JOIN downloadable ON downloads.did = downloadable.id
        WHERE dtime > DATE_ADD(NOW(), INTERVAL -7 DAY)
        GROUP BY s3key
        HAVING count>=1
        ORDER BY count DESC
     """),

    ('Downloads in past 24 hours',
     """SELECT s3key,sum(bytes_sent)/max(bytes) as count
        FROM downloads
        RIGHT JOIN downloadable ON downloads.did = downloadable.id
        WHERE dtime > addtime(now(),"-24:00:00")
        GROUP BY s3key
        HAVING count>=1
        ORDER BY count DESC
     """),

    ('Failed downloads in past 24 hours',
     """SELECT s3key,sum(bytes_sent)/max(bytes) as count
        FROM downloads
        RIGHT JOIN downloadable ON downloads.did = downloadable.id
        WHERE dtime > addtime(now(),"-24:00:00")
        GROUP BY s3key
        HAVING count<1
        ORDER BY count DESC
     """),
]

def report_app(auth):
    """Run from bottle."""
    print(auth,file=sys.stderr)
    return REPORT.render(reports=['first','second','third'],report='',sys_version=sys.version)
#Don't forget time_zone = gmt
