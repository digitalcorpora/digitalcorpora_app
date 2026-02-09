import pytest
import requests
import logging
import json
import os

# Configure logging for the test
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Load test cases from JSON file
CASES_PATH = os.path.join(os.path.dirname(__file__), 'deployed_service_cases.json')
with open(CASES_PATH, 'r') as f:
    test_cases = json.load(f)

@pytest.mark.parametrize('case', test_cases)
def test_deployed_service(case):
    url = case['url']
    expect = case['expect']
    try:
        # Allow redirects only if expecting direct
        allow_redirects = expect['direct']
        response = requests.get(url, allow_redirects=allow_redirects, timeout=10, verify=True)
        if not expect['direct']:
            # If expecting a redirect, check for 3xx and Location header
            if response.is_redirect or response.is_permanent_redirect:
                logger.info(f"{url}: Correctly redirected (status {response.status_code})")
                # Optionally, follow the redirect and check the final response
                redirected_url = response.headers.get('Location')
                if redirected_url:
                    response2 = requests.get(redirected_url, allow_redirects=True, timeout=10, verify=True)
                    _check_file_response(response2, expect, redirected_url)
                else:
                    logger.error(f"{url}: Redirect expected but no Location header found.")
                    assert False, f"No Location header in redirect for {url}"
            else:
                logger.error(f"{url}: Expected redirect but got status {response.status_code}")
                assert False, f"Expected redirect for {url}"
        else:
            _check_file_response(response, expect, url)
    except Exception as e:
        logger.error(f"{url}: Exception occurred: {e}")
        assert False, f"Exception for {url}: {e}"

def _check_file_response(response, expect, url):
    # Check status code
    if response.status_code != 200:
        logger.error(f"{url}: Expected 200 OK, got {response.status_code}")
        assert False, f"Expected 200 OK for {url}"
    # Check Content-Length
    content_length = int(response.headers.get('Content-Length', -1))
    if content_length != expect['length']:
        logger.error(f"{url}: Content-Length {content_length} != expected {expect['length']}")
        assert False, f"Content-Length mismatch for {url}"
    # Check Content-Type
    content_type = response.headers.get('Content-Type', '').split(';')[0].strip()
    if content_type != expect['mime']:
        logger.error(f"{url}: Content-Type '{content_type}' != expected '{expect['mime']}'")
        assert False, f"Content-Type mismatch for {url}"
    logger.info(f"{url}: Success (length={content_length}, mime={content_type})") 