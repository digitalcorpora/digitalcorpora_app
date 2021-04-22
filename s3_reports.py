"""
Generate reports.
"""

import os
import os.path
import sys
import json

from os.path import dirname

from ctools.dbfile import DBMySQL
import bottle

REPORT_TEMPLATE_FILENAME  = os.path.join(dirname(__file__), "templates/reports.tpl")
REPORT = bottle.SimpleTemplate( open( REPORT_TEMPLATE_FILENAME ).read())


REPORTS = [
    ('Downloads over past week',
     """SELECT s3key,round(sum(bytes_sent)/max(bytes)) as count,min(dtime) as first,max(dtime) as last,
        FROM downloads
        LEFT JOIN downloadable ON downloads.did = downloadable.id
        WHERE dtime > DATE_ADD(NOW(), INTERVAL -7 DAY)
        GROUP BY s3key
        HAVING count>=1
        ORDER BY count DESC
     """),

    ('Downloads in the past 24 hours',
     """SELECT s3key,round(sum(bytes_sent)/max(bytes)) as count
        FROM downloads
        LEFT JOIN downloadable ON downloads.did = downloadable.id
        WHERE dtime > addtime(now(),"-24:00:00")
        GROUP BY s3key
        HAVING count>=1
        ORDER BY count DESC
     """),

    ('Failed downloads in past 24 hours',
     """SELECT s3key,round(sum(bytes_sent)/max(bytes)) as count
        FROM downloads
        LEFT JOIN downloadable ON downloads.did = downloadable.id
        WHERE dtime > addtime(now(),"-24:00:00")
        GROUP BY s3key
        HAVING count<1
        ORDER BY count DESC
     """),

    ('Downloads per day for the past 30 days',
     """
     SELECT ddate,count(*)
     FROM (SELECT date(dtime) ddate,s3key,round(sum(bytes_sent)/max(bytes)) as count
           FROM downloads
           LEFT JOIN downloadable ON downloads.did = downloadable.id
           WHERE dtime > DATE_ADD(NOW(), INTERVAL -30 DAY)
     GROUP BY s3key,date(dtime) HAVING count>=1  ) a
     GROUP BY ddate
     """),
]

def report_json(*,auth,num):
    """Run a specific numbered report and return the result as a JSON object that's easy to render.
    :param auth: authorization
    :param num: which report to generate.
    """
    report = REPORTS[round(num)]
    column_names = []
    rows = DBMySQL.csfr(auth, report[1], [], time_zone='GMT', get_column_names=column_names)
    return json.dumps({'title':report[0],
                       'sql':report[1],
                       'column_names':column_names,
                       'rows': rows},default=str)

def report_app(auth):
    """Run from bottle."""
    print(auth,file=sys.stderr)
    return REPORT.render(reports=[report[0] for report in REPORTS],sys_version=sys.version)

#Don't forget time_zone = gmt
