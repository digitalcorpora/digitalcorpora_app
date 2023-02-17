PYLINT_FILES=$(shell /bin/ls *.py  | grep -v app_wsgi.py)

all:
	@echo verify syntax and then restart
	make pylint
	make touch

check:
	make touch
	make pylint
	make pytest


touch:
	touch tmp/restart.txt

lint:
	pylint $(PYLINT_FILES)

# These are used by the CI pipeline:
install-dependencies:
	if [ -r requirements.txt ]; then pip3 install --user -r requirements.txt ; else echo no requirements.txt ; fi

pytest:
	pytest .

coverage:
	python3 -m pip install pytest pytest_cov
	python3 -m pytest --debug -v --cov=. --cov-report=xml tests

clean:
	find . -name '*~' -exec rm {} \;
