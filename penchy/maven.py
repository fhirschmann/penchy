#!/usr/bin/env python

from xml.dom.minidom import Document
from collections import namedtuple

MavenDependency = namedtuple('MavenDependency', ['groupId', 'artifactId', 'version', 'repo'])


class BootstrapPOM(object):
    """
    This class represents a bootstrap POM which is used to deploy 
    PenchY and its dependencies
    """
    ATTRIBS = {
            'groupId': 'de.tu_darmstadt.penchy',
            'artifactId': 'penchy-bootstrap',
            'name': 'penchy-bootstrap',
            'url': 'http://www.tu-darmstadt.de',
            'modelVersion': '4.0.0',
            'packaging': 'jar', # won't work with pom
    }

    def __init__(self):
        self.xml = Document()
        self.project = self.xml.createElement('project')
        self.xml.appendChild(self.project)

        self.dict2xml(self.project, BootstrapPOM.ATTRIBS)

        self.repositories = self.xml.createElement('repositories')
        self.project.appendChild(self.repositories)

        self.dependencies = self.xml.createElement('dependencies')
        self.project.appendChild(self.dependencies)

    def dict2xml(self, parent, childs, filterfunc=None):
        """
        Turns a dictionary into XML and append it to the parent.

        :param parent: the parent to append to
        :type parent: xml document
        :param child: the childs to append
        :type childs: dict
        """
        for k, v in childs.items():
            if filterfunc:
               if not filterfunc(k):
                   continue

            attrib = self.xml.createElement(k)
            attrib.appendChild(self.xml.createTextNode(v))
            parent.appendChild(attrib)
    
    def add_dependency(self, dep):
        """
        Adds a given dependency to the POM.

        :param dep: the dependency
        :type dep: MavenDependency
        """
        if dep.repo:
            self.add_repository(dep.repo, dep.repo)

        xdep = self.xml.createElement('dependency')
        self.dependencies.appendChild(xdep)

        self.dict2xml(xdep, dep.__dict__, lambda r: r != 'repo')

    def add_repository(self, identifier, url):
        """
        Adds a repository to the POM.

        :param identifier: an identifier for the repository
        :type identifier: string
        :param url: the URL of the repository
        :type url: string
        """
        
        xrepo = self.xml.createElement('repository')
        self.repositories.appendChild(xrepo)

        self.dict2xml(xrepo, {'id': identifier, 'url': identifier})

    def get_xml(self):
        """
        Returns the BootstrapPOM formatted as XML.
        """
        return self.xml.toprettyxml(indent="  ")

if __name__ == "__main__": 
    x = MavenDependency('de.tu_darmstadt.penchy', 'booster', '2.0.0.0', 'http://mvn.0x0b.de')

    p = BootstrapPOM()
    p.add_dependency(x)
    print p.get_xml()
    
