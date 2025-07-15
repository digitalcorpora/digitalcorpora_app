# Makefile for local development and testing

REGION=us-west-2
BUCKET=digitalcorpora
PORT=8000
LOCAL_URL=http://localhost:$(PORT)/s3_browser.html
PYLINT_FILES=$(shell find src/ -name "*.py" -not -name "__init__.py")
PYLINT_THRESHOLD=9.5
LOG_LEVEL?=INFO
TEST_CREDENTIALS:=$(CURDIR)/test_credentials.json

################################################################
# Local development
install:
	poetry config virtualenvs.in-project true
	poetry install
	npm install -g live-server

dev:
	cd src && poetry run python -m digitalcorpora_app.main

test-local:
	pytest tests/test_s3_listing.py --base-url=$(LOCAL_URL)

test-prod:
	pytest tests/test_s3_listing.py --base-url=https://$(BUCKET).s3-website-$(REGION).amazonaws.com/

################################################################
# Poetry dependency management
requirements.txt: pyproject.toml
	poetry export -f requirements.txt --output requirements.txt --without-hashes

################################################################
# Testing and quality checks
all:
	@echo verify syntax and then restart
	make pylint
	make touch

check:
	make pylint
	make pytest

touch:
	touch tmp/restart.txt

pylint:
	poetry run pylint --rcfile .pylintrc --fail-under=$(PYLINT_THRESHOLD) --verbose $(PYLINT_FILES)

pytest:
	LOG_LEVEL=$(LOG_LEVEL) TEST_CREDENTIALS=$(TEST_CREDENTIALS) poetry run pytest tests/

pytest-debug:
	LOG_LEVEL=$(LOG_LEVEL) TEST_CREDENTIALS=$(TEST_CREDENTIALS) poetry run pytest -v --log-cli-level=DEBUG tests/

coverage:
	LOG_LEVEL=$(LOG_LEVEL) TEST_CREDENTIALS=$(TEST_CREDENTIALS) poetry run pytest -v --cov=src/digitalcorpora_app --cov-report=xml --cov-report=html tests/

coverage-open:
	open htmlcov/index.html

################################################################
# AWS SAM deployment
sam-build:
	sam build

sam-deploy:
	sam deploy

sam-deploy-dev:
	sam deploy --config-env dev --parameter-overrides DomainName=dev.digitalcorpora.org

sam-deploy-app:
	sam deploy --config-env app --parameter-overrides DomainName=app.digitalcorpora.org

sam-deploy-search:
	sam deploy --config-env search --parameter-overrides DomainName=search.digitalcorpora.org

sam-local:
	DEBUG=true sam local start-api

sam-local-lambda:
	sam local start-lambda

################################################################
# Publish the S3 browser
pub:
	aws --profile=dcwriter s3 cp s3_browser.html s3://digitalcorpora/s3_browser.html

################################################################
# Clean up
clean:
	find . -name '*~' -exec rm {} \;
	find . -name '__pycache__' -type d -exec rm -rf {} +
	find . -name '.pytest_cache' -type d -exec rm -rf {} +
	rm -rf .aws-sam
	rm -rf .venv
