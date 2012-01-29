.PHONY: tests help hooks coverage full-coverage dev doc static-analysis

help:
	@echo "Please use \`make <target>', target in {tests,hooks,coverage}"
	@echo "    - tests: run unittests"
	@echo "    - hooks: install git hooks"
	@echo "    - coverage: run unittests, gather coverage and produce html output"

tests:
	unit2 discover -s penchy/tests -t .

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
	coverage run --append bin/penchy -c penchyrc.example --run-locally examples/simple.job
# 	coverage run --append bin/penchy -c penchyrc.example --run-locally examples/valgrind_jvm.job

coverage-upload: coverage
	rsync -avz htmlcov bp@0x0b.de:~/docs/

dev:
	pip install coverage pep8 pyflakes pylint sphinx
	pip install http://sourceforge.net/projects/pychecker/files/pychecker/0.8.19/pychecker-0.8.19.tar.gz/download

doc:
	PYTHONPATH=${PYTHONPATH}:`pwd` make -C docs html

static-analysis:
	hooks/pre-commit --all
