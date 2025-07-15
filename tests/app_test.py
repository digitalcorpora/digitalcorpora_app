import pytest
import sys
import os
import warnings
import json

from os.path import abspath,dirname

# Flask testing patterns
from flask.testing import FlaskClient

sys.path.append( dirname(dirname(abspath(__file__))))

from digitalcorpora_app.main import app
from digitalcorpora_app.paths import STATIC_DIR

@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_version(client):
    """Test the version endpoint"""
    response = client.get('/ver')
    assert response.status_code == 200
    assert '1.0.0' in response.get_data(as_text=True)

def test_static_path(client):
    """Test static file serving"""
    response = client.get('/static/test.txt')
    assert response.status_code == 200
    expected_content = open(os.path.join(STATIC_DIR, 'test.txt'), 'rb').read()
    assert response.data == expected_content

def test_reports(client):
    """Test reports endpoint"""
    response = client.get('/reports')
    assert response.status_code == 200

def test_search(client):
    """Test search endpoint"""
    response = client.get('/search')
    assert response.status_code == 200

def test_index_tsv(client):
    """Test index.tsv endpoint"""
    response = client.get('/index.tsv?row_count=5&offset=0')
    assert response.status_code == 200
    lines = response.get_data(as_text=True).split('\n')
    assert len(lines) >= 1  # At least header line

def test_search_api(client):
    """Test search API endpoint"""
    response = client.get('/search/api?q=dmg')
    assert response.status_code == 200
    data = json.loads(response.get_data(as_text=True))
    assert isinstance(data, list)

    response = client.get('/search/api?q=dmg&row_count=1&offset=0')
    assert response.status_code == 200
    data = json.loads(response.get_data(as_text=True))
    assert isinstance(data, list)
