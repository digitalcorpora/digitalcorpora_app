"""
Generate reports.
"""

import os
import os.path
import sys
import json
from os.path import dirname
from ctools.dbfile import DBMySQL
from flask import Flask, redirect, request, render_template
from flask import Flask, send_from_directory

REPORT_TEMPLATE_FILENAME  = "reports.html"

REPORTS = [
    ('Last 50 corpora uploads ',
     """SELECT s3key, bytes, mtime, tags
        FROM downloadable
        WHERE present=1
        ORDER BY mtime DESC
        LIMIT 50
     """),

    ('Downloads over past week',
     """SELECT s3key, round(sum(bytes_sent)/max(bytes)) as count, min(dtime) as first,max(dtime) as last
        FROM downloads
        LEFT JOIN downloadable ON downloads.did = downloadable.id
        WHERE dtime > DATE_ADD(NOW(), INTERVAL -7 DAY)
        GROUP BY s3key
        HAVING count>=1
        ORDER BY count DESC
     """),

    ('Downloads in the past 24 hours',
     """SELECT s3key, round(sum(bytes_sent)/max(bytes)) as count
        FROM downloads
        LEFT JOIN downloadable ON downloads.did = downloadable.id
        WHERE dtime > addtime(now(),"-24:00:00")
        GROUP BY s3key
        HAVING count>=1
        ORDER BY count DESC
     """),

    ('Failed downloads in past 24 hours',
     """SELECT s3key, round(sum(bytes_sent)/max(bytes)) as count
        FROM downloads
        LEFT JOIN downloadable ON downloads.did = downloadable.id
        WHERE dtime > addtime(now(),"-24:00:00")
        GROUP BY s3key
        HAVING count<1
        ORDER BY count DESC
     """),

    ('Downloads per day for the past 30 days',
     """
     SELECT ddate as `date`, count(*) as count
     FROM (SELECT date(dtime) ddate,s3key,round(sum(bytes_sent)/max(bytes)) as count
           FROM downloads
           LEFT JOIN downloadable ON downloads.did = downloadable.id
           WHERE dtime > DATE_ADD(NOW(), INTERVAL -30 DAY)
     GROUP BY s3key,date(dtime) HAVING count>=1  ) a
     GROUP BY ddate
     """),
]

def report_count():
    return len(REPORTS)

def report_generate(*, auth, num):
    """Run a specific numbered report and return the result as a JSON object that's easy to render.
    :param auth: authorization
    :param num: which report to generate.
    """
    report = REPORTS[int(num)]
    column_names = []
    rows = DBMySQL.csfr(auth, report[1], [], get_column_names=column_names)
    return {'title':report[0],
            'sql':report[1],
            'column_names':column_names,
            'rows': rows}

def report_app(*, auth):
    if request.args.get('report'):
        rdict = report_generate(auth=auth, num=int(request.args.get('report')))
        try:
            colnum = rdict['column_names'].index('s3key')
        except ValueError:
            colnum = -1
        if colnum>=0:
            # Convert from tuples to lists so that we can change the middle value
            rdict['rows'] = [list(row) for row in rdict['rows']]
            for row in rdict['rows']:
                s3key = row[colnum]
                row[colnum] = f'<a href="/{s3key}">{s3key}</a>'
    else:
        rdict = {}
    rdict['reports'] = reports=[(ct,report[0]) for (ct,report) in enumerate(REPORTS)]
    rdict['sys_version'] = sys.version
    return render_template(REPORT_TEMPLATE_FILENAME, **rdict)
