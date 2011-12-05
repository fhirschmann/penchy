.PHONY: deploy deploy-booster deploy-pia deploy-poa deploy-deps upload install

REPO_PATH=target/repo

help:
	@echo "Please use \`make <target>'"

deploy:
	mvn deploy

target/booster-2.0.0.0.jar:
	wget http://tamiflex.googlecode.com/files/booster-2.0.0.0.jar -O target/booster-2.0.0.0.jar

target/pia-2.0.0.0.jar:
	wget http://tamiflex.googlecode.com/files/booster-2.0.0.0.jar -O target/pia-2.0.0.0.jar

target/poa-2.0.0.0.jar:
	wget http://tamiflex.googlecode.com/files/booster-2.0.0.0.jar -O target/poa-2.0.0.0.jar

deploy-booster: target/booster-2.0.0.0.jar
	mvn deploy:deploy-file -Durl=file:${REPO_PATH} \
		-DrepositoryId=penchy \
		-Dfile=target/booster-2.0.0.0.jar \
		-DgroupId=de.tu_darmstadt.penchy \
		-DartifactId=booster \
		-Dpackaging=jar \
		-Dversion=2.0.0.0

deploy-pia: target/pia-2.0.0.0.jar
	mvn deploy:deploy-file -Durl=file:${REPO_PATH} \
		-DrepositoryId=penchy \
		-Dfile=target/pia-2.0.0.0.jar \
		-DgroupId=de.tu_darmstadt.penchy \
		-DartifactId=pia \
		-Dpackaging=jar \
		-Dversion=2.0.0.0

deploy-poa: target/poa-2.0.0.0.jar
	mvn deploy:deploy-file -Durl=file:${REPO_PATH} \
		-DrepositoryId=penchy \
		-Dfile=target/poa-2.0.0.0.jar \
		-DgroupId=de.tu_darmstadt.penchy \
		-DartifactId=poa \
		-Dpackaging=jar \
		-Dversion=2.0.0.0

deploy-deps: deploy-booster deploy-pia deploy-poa

install:
	mvn install

upload:
	rsync -avz --delete target/repo/* bp@0x0b.de:/var/www/mvn.0x0b.de/htdocs

