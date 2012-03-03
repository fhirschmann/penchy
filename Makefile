.PHONY: tests help hooks coverage full-coverage dev latex-doc doc static-analysis

help:
	@echo "Please use \`make <target>', targets:"
	@echo "    - tests: run unittests"
	@echo "    - hooks: install git hooks"
	@echo "    - coverage: gather coverage and produce html about relevant parts"
	@echo "    - full-coverage: gather coverage and produce html output"
	@echo "    - coverage-upload: gather coverage and upload it to 0x0b.de"
	@echo "    - dev: pip install all developmet dependencies"
	@echo "    - doc: generate html documentation"
	@echo "    - static-analysis: static analysis of all code"
	@echo "    - clean: removes all *.pyc *.pyo and logfiles"

tests:
	unit2 discover -s penchy/tests -t .

tests3:
	python -m unittest discover -s penchy/tests -t .

hooks:
	ln -s $(realpath hooks/pre-commit) .git/hooks/pre-commit

coverage: .coverage
	coverage report -i --include='penchy/*'
	coverage html --include='penchy/jobs/*,penchy/log.py,penchy/util.py,penchy/maven.py,penchy/compat.py'
	coverage erase

full-coverage: .coverage
	coverage html --include='penchy/*'
	coverage erase

.DELETE_ON_ERROR:
.coverage:
	coverage run -m unittest2 discover -p '*.py' -s penchy/tests -t .
	coverage run --append bin/penchy -c penchyrc.example --run-locally plans/jobs/dump.job
	coverage run --append bin/penchy -c penchyrc.example --run-locally plans/jobs/valgrind.job

coverage-upload: coverage
	chmod -R 755 htmlcov
	rsync -avz htmlcov bp@0x0b.de:~/docs/

dev:
	pip install coverage pep8 pyflakes pylint sphinx
	pip install http://sourceforge.net/projects/pychecker/files/pychecker/0.8.19/pychecker-0.8.19.tar.gz/download

doc:
	PYTHONPATH=${PYTHONPATH}:`pwd` make -C docs html

latex-doc:
	PYTHONPATH=${PYTHONPATH}:`pwd` make -C docs latex
	make -C docs/_build/latex

static-analysis:
	PYLINTRC=./.pylintrc hooks/pre-commit --all

injection:
	PYTHONPATH=.:dev/injected_modules/ python penchy/apicheck.py

clean:
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.pyo' -delete
	find . -type f -regex '.*.log\(.[0-9]+\)?' -delete
