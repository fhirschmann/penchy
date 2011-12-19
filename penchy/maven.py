#!/usr/bin/env python

import logging

from xml.dom.minidom import Document
from collections import namedtuple
from subprocess import Popen, PIPE

from penchy import __version__ as penchy_version
from penchy.util import memoized


@memoized
def get_classpath():
    """
    Returns the Java classpath with the help of Maven

    :returns: java classpath
    :rtype: string
    """
    proc2 = Popen(['mvn', 'dependency:build-classpath'], stdout=PIPE)
    stdout, _ = proc2.communicate()
    for line in stdout.split("\n"):
        if not line.startswith("["):
            return line


class MavenDependency(object):
    """
    This class represents a Maven Dependency
    """
    def __init__(self, groupId, artifactId, version, repo=None,
            classifier=None, artifact_type=None):
        self.groupId = groupId
        self.artifactId = artifactId
        self.version = version
        self.repo = repo
        self.classifier = classifier
        self.type = artifact_type

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class POM(object):
    """
    This class represents a basic Maven POM.

    This is kind of a lazy implementation. The full XML file won't be
    build until you call `get_xml`.

    Duplicates are discarded, so no repository or dependency will
    be defined twice in the POM.
    """
    def __init__(self):
        self.repository_list = set()
        self.dependency_list = set()

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
            if not v:
                continue

            attrib = parent.ownerDocument.createElement(k)
            attrib.appendChild(parent.ownerDocument.createTextNode(v))
            parent.appendChild(attrib)

    def add_dependency(self, dep):
        """
        Adds a given dependency to the POM.

        :param dep: the dependency
        :type dep: MavenDependency
        """

        self.dependency_list.add(dep)

        if dep.repo:
            self.add_repository(dep.repo)

    def add_repository(self, url):
        """
        Adds a repository to the POM.

        :param identifier: an identifier for the repository
        :type identifier: string
        :param url: the URL of the repository
        :type url: string
        """
        self.repository_list.add(url)

    def get_xml(self):
        """
        Returns the BootstrapPOM formatted as XML.
        """
        xml = Document()
        project = xml.createElement('project')
        xml.appendChild(project)

        self.dict2xml(project, BootstrapPOM.ATTRIBS)

        # Repositories
        repositories = xml.createElement('repositories')
        project.appendChild(repositories)
        for repo in self.repository_list:
            xrepo = xml.createElement('repository')
            repositories.appendChild(xrepo)

            self.dict2xml(xrepo, {'id': repo, 'url': repo})

        # Dependencies
        dependencies = xml.createElement('dependencies')
        project.appendChild(dependencies)
        for dep in self.dependency_list:
            xdep = xml.createElement('dependency')
            dependencies.appendChild(xdep)

            self.dict2xml(xdep, dep.__dict__, lambda r: r != 'repo')

        return xml.toprettyxml(indent="  ")


class BootstrapPOM(POM):
    """
    This class represents a bootstrap POM which is used to deploy
    PenchY and its dependencies.
    """
    ATTRIBS = {
            'groupId': 'de.tu_darmstadt.penchy',
            'artifactId': 'penchy-bootstrap',
            'name': 'penchy-bootstrap',
            'url': 'http://www.tu-darmstadt.de',
            'version': penchy_version,
            'modelVersion': '4.0.0',
            'packaging': 'jar',  # won't work with pom
            }

    def __init__(self):
        POM.__init__(self)
        self.dependency_list.add(MavenDependency(
            groupId='de.tu_darmstadt.penchy',
            artifactId='penchy',
            version=penchy_version,
            classifier='py',
            artifact_type='zip'))
