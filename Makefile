PYLINT_FILES=$(shell /bin/ls *.py  | grep -v bottle.py | grep -v app_wsgi.py)

touch:
	@echo verify syntax and then restart
	make pylint
	touch tmp/restart.txt

pylint:
	pylint $(PYLINT_FILES)

# These are used by the CI pipeline:
install-dependencies:
	if [ -r requirements.txt ]; then pip3 install --user -r requirements.txt ; fi

pytest:
	pytest .

coverage:
	echo hello world.
	which pytest
	which coverage
	pytest -v --cov=. --cov-report=xml tests/ || echo pytest failed
	echo ===== test ends ==========
	ls -l
