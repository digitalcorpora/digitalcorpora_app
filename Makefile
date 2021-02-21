PYLINT_FILES=$(shell /bin/ls *.py  | grep -v bottle.py | grep -v app_wsgi.py)

touch:
	@echo verify syntax and then restart
	make pylint
	touch tmp/restart.txt

pylint:
	pylint $(PYLINT_FILES)

install:
	if [ -r requirements.txt ]; then pip3 install --user -r requirements.txt ; fi
	if [ -r requirements-dev.txt ]; then pip3 install --user -r requirements-dev.txt ; fi
