import pytest
import sys
import os
from os.path import abspath,dirname

sys.path.append( dirname(dirname(abspath(__file__))))

from flaskr import create_app

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

def test_ver(client):
    response = client.get('/ver')
    assert response.status_code == 200
    assert response.data.decode('utf-8').startswith('Python version')
