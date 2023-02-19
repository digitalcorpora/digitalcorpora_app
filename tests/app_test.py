import pytest
import sys
import os
import json
from os.path import abspath,dirname

sys.path.append( dirname(dirname(abspath(__file__))))

from flaskr import create_app
import flaskr.s3_reports as s3_reports

@pytest.fixture()
def app():
    app = create_app()
    app.config.update({"TESTING":True})
    yield app

@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


def test_template(client):
    response = client.get('/test_template')
    assert response.status_code == 200
    data = response.data.decode('utf-8')
    print(data)
    assert "Search Wordpress Site" in data
    assert "Search Corpus" in data
    assert "SHA2-256" in data

def test_misc(client):
    response = client.get('/')
    assert response.status_code == 200

    response = client.get('/ver')
    assert response.status_code == 200
    assert response.data.decode('utf-8').startswith('Python version')

    response = client.get('/robots.txt')
    assert response.status_code == 200

    response = client.get('/corpora/')
    assert response.status_code == 200

    response = client.get('/downloads/')
    assert response.status_code == 200

    response = client.get('/hello/world')
    assert response.status_code == 200

def test_reports(client):
    response = client.get('/reports')
    assert response.status_code == 200

    for report in range(s3_reports.report_count()):
        response = client.get(f'/reports?reports={report}')
        assert response.status_code == 200

def test_search(client):
    response = client.get('/search')
    assert response.status_code == 200
    assert 'Digital Corpora: Search' in response.data.decode('utf-8')

    response = client.get('/search/api?q=dmg')
    assert response.status_code == 200
    data = json.loads(response.data)

    assert isinstance(data,list)
    row0 = [row for row in data if row['s3key']=='corpora/drives/nps-2009-hfsjtest1/image.gen0.dmg']
    assert len(row0) == 1
    gen0 = row0[0]
    GEN0 = { "bytes": 10485760,
             "etag": "\"414b5822f37a295160ed1c43415cfe28-2\"",
             "id": 797,
             "modified": "2022-09-27 16:39:38",
             "mtime": "2020-11-21 16:08:29",
             "present": 1,
             "s3key": "corpora/drives/nps-2009-hfsjtest1/image.gen0.dmg",
             "sha2_256": "3651d06cd28db38995be15ebb94c9486b2c31f4bd340bfa4d2ea6d4023dc3588",
             "sha3_256": "60721e526dbc4b841053c93b5583581014052d7118f60618813f2de4c94e167b"}

    for k in GEN0.keys():
        assert gen0[k] == GEN0[k]



def test_errors(client):
    response = client.get('/downloads/nothing-here')
    assert response.status_code == 404
