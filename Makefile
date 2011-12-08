.PHONY: deploy deploy-booster deploy-pia deploy-poa deploy-all upload install

help:
	@echo "Please use \`make <target>'"

deploy:
	mvn deploy

deploy-all: deploy lib/booster/booster-2.0.0.0.jar lib/pia/pia-2.0.0.0.jar lib/poa/poa-2.0.0.0.jar
	cd lib && mvn deploy

lib/booster/booster-2.0.0.0.jar:
	wget http://tamiflex.googlecode.com/files/booster-2.0.0.0.jar -O lib/booster/booster-2.0.0.0.jar

lib/pia/pia-2.0.0.0.jar:
	wget http://tamiflex.googlecode.com/files/pia-2.0.0.0.jar -O lib/pia/pia-2.0.0.0.jar

lib/poa/poa-2.0.0.0.jar:
	wget http://tamiflex.googlecode.com/files/poa-2.0.0.0.jar -O lib/poa/poa-2.0.0.0.jar

install:
	mvn install

upload:
	rsync -avz --delete repo/* */repo/* bp@0x0b.de:/var/www/mvn.0x0b.de/htdocs

tests:
	unit2 discover -s penchy/tests 
