MYFILES=$(shell /bin/ls *.py  | grep -v bottle.py)

touch:
	@echo verify syntax and then restart
	pylint $(MYFILES)
	touch tmp/restart.txt

pylint:
	pylint $(MYFILES)

install:
	if [ -r requirements.txt ]; then pip3 install --user -r requirements.txt ; fi
	if [ -r requirements-dev.txt ]; then pip3 install --user -r requirements-dev.txt ; fi
