PYLINT_FILES=$(shell /bin/ls *.py  | grep -v bottle.py | grep -v app_wsgi.py)

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
	pylint --rcfile .pylintrc --verbose $(PYLINT_FILES)

flake8:
	flake8 $(PYLINT_FILES)

# These are used by the CI pipeline:
install-dependencies:
	if [ -r requirements.txt ]; then pip3 install --user -r requirements.txt ; else echo no requirements.txt ; i

pytest:
	pytest .

coverage:
	python3 -m pip install pytest pytest_cov
	python3 -m pytest -v --cov=. --cov-report=xml tests

clean:
	find . -name '*~' -exec rm {} \;
