.PHONY: tests help hooks coverage dev

help:
	@echo "Please use \`make <target>', target in {tests,hooks,coverage}"
	@echo "    - tests: run unittests"
	@echo "    - hooks: install git hooks"
	@echo "    - coverage: run unittests, gather coverage and produce html output"

tests:
	unit2 discover -s penchy/tests -t .

hooks:
	ln -s $(realpath hooks/pre-commit) .git/hooks/pre-commit

coverage:
	coverage erase
	coverage run -m unittest2 discover -s penchy/tests -t .
	coverage report
	coverage html

dev:
	pip install coverage pep8 pyflakes pylint
	pip install http://sourceforge.net/projects/pychecker/files/pychecker/0.8.19/pychecker-0.8.19.tar.gz/download
