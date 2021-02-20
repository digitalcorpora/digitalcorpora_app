touch:
	touch tmp/restart.txt

flake8:
	flake8 *.py

install:
	if [ -r requirements.txt ]; then pip3 install --user -r requirements.txt ; fi
	if [ -r requirements-dev.txt ]; then pip3 install --user -r requirements-dev.txt ; fi
