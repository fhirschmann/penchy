.PHONY: tests help

help:
	@echo "Please use \`make <target>'"

tests:
	unit2 discover -s penchy/tests 
