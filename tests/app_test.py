import pytest
import sys
import os
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

def test_template(client):
    response = client.get('/test_template')
    assert response.status_code == 200
    data = response.data.decode('utf-8')
    print(data)
    assert "Search Wordpress Site" in data
    assert "Search Corpus" in data
    assert "SHA2-256" in data

def test_errors(client):
    response = client.get('/downloads/nothing-here')
    assert response.status_code == 404
