.PHONY: tests help hooks coverage

help:
	@echo "Please use \`make <target>'"

tests:
	unit2 discover -s penchy/tests -t .

hooks:
	ln -s $(realpath hooks/pre-commit) .git/hooks/pre-commit

coverage:
	coverage run -m unittest2 discover -s penchy/tests -t .
	coverage html
