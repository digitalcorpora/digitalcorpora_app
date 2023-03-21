#!/usr/bin/env python3

# Portions of this file contributed by NIST are governed by the following
# statement:
#
# This software was developed at the National Institute of Standards
# and Technology by employees of the Federal Government in the course
# of their official duties. Pursuant to title 17 Section 105 of the
# United States Code this software is not subject to copyright
# protection and is in the public domain. NIST assumes no
# responsibility whatsoever for its use by other parties, and makes
# no guarantees, expressed or implied, about its quality,
# reliability, or any other characteristic.
#
# We would appreciate acknowledgement if the software is used.

import csv
import io


def test_sv_nulls(delimiter: str, expected: str) -> None:
    """
    Confirm expected content form of TSV output with null records.

    Line separator is \\r\\n because of default dialect of Excel.

    Sample data adapted from:
    https://docs.python.org/3/library/csv.html#csv.DictWriter
    """
    with io.StringIO() as f:
        fieldnames = ['first_name', 'last_name']
        writer = csv.DictWriter(f, delimiter=delimiter, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({'first_name': 'Wonderful', 'last_name': 'Spam'})
        writer.writerow({'first_name': 'OnlyFirst'})
        writer.writerow({'first_name': 'ExplicitNullLast', 'last_name': None})
        writer.writerow({'last_name': 'OnlyLast'})
        # Next row is also out of dict key order.
        writer.writerow({'last_name': 'ExplicitNullFirst', 'first_name': None})
        computed = f.getvalue()
        assert expected == computed


def test_csv_nulls() -> None:
    expected = "first_name,last_name\r\nWonderful,Spam\r\nOnlyFirst,\r\nExplicitNullLast,\r\n,OnlyLast\r\n,ExplicitNullFirst\r\n"
    _test_sv_nulls(",", expected)


def test_tsv_nulls() -> None:
    expected = "first_name\tlast_name\r\nWonderful\tSpam\r\nOnlyFirst\t\r\nExplicitNullLast\t\r\n\tOnlyLast\r\n\tExplicitNullFirst\r\n"
    _test_sv_nulls("\t", expected)
