.PHONY: mvn-deploy mvn-install egg

help:
	@echo "Please use \`make <target>'"

mvn-deploy:
	mvn deploy

mvn-install:
	mvn install

egg:
	python setup.py bdist_egg
