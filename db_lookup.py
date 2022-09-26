#!/usr/bin/env python3
"""
db_lookup.py:
Given a list of dictionaries that have Keys, mtimes and etags, see if we can find them in the database
"""

import logging
import ctools.dbfile

def annotate_s3files(auth, objs):
    """Given a dbreader and a set of objects, see if we can find their hash codes in the database"""

    if not objs:
        return

    keys = [obj['Key'] for obj in objs]
    cmd = "select * from downloadable where s3key in (" + ",".join(['%s']*len(keys)) + ")"
    rows = ctools.dbfile.DBMySQL.csfr(auth, cmd, keys, asDicts=True)

    # Re-organize what we got by key...
    rbyk = {row['s3key'] : row for row in rows}
    # Annotate the array
    for obj in objs:
        s3key = obj['Key']
        if s3key in rbyk:
            rk = rbyk[s3key]
            if rk['etag'] == obj['ETag']:
                obj['sha2_256'] = rk['sha2_256']
                obj['sha3_256'] = rk['sha3_256']
