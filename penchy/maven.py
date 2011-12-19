#!/usr/bin/env python

import logging

from collections import namedtuple
from subprocess import Popen, PIPE

from xml.etree.ElementTree import Element, SubElement, ElementTree

from penchy import __version__ as penchy_version
from penchy.util import memoized, tree_pp, dict2tree


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
            classifier=None, artifact_type=None, packaging=None):
        self.groupId = groupId
        self.artifactId = artifactId
        self.version = version
        self.repo = repo
        self.classifier = classifier
        self.type = artifact_type
        self.packaging = packaging

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

    ATTRIBS = {
            'modelVersion': '4.0.0',
    }

    def __init__(self, **kwargs):
        self.repository_list = set()
        self.dependency_list = set()

        self.root = Element('project')
        self.tree = ElementTree(self.root)
        self.dependency_tree = SubElement(self.root, 'dependencies')
        self.repository_tree = SubElement(self.root, 'repositories')

        attribs = POM.ATTRIBS
        attribs.update(kwargs)
        dict2tree(self.root, attribs)

    def add_dependency(self, dep):
        """
        Adds a given dependency to the POM.

        :param dep: the dependency
        :type dep: MavenDependency
        """
        if dep in self.dependency_list:
            return

        if dep.repo:
            self.add_repository(dep.repo)

        clean_dep = dep.__dict__.copy()
        clean_dep.pop('repo')

        e = SubElement(self.dependency_tree, 'dependency')
        dict2tree(e, clean_dep)

        self.dependency_list.add(dep)

    def add_repository(self, url):
        """
        Adds a repository to the POM.

        :param identifier: an identifier for the repository
        :type identifier: string
        :param url: the URL of the repository
        :type url: string
        """
        if url in self.repository_list:
            return

        e = SubElement(self.repository_tree, 'repository')
        dict2tree(e, {'url': url, 'id': url})

        self.repository_list.add(url)

    def write(self, filename, pretty=True):
        """
        Writes the POM to a file.

        :param filename: the filename to write to
        :type filename: string
        :param pretty: pretty-print resulting file
        :type pretty: bool
        """
        if pretty:
            tree_pp(self.root)

        self.tree.write(filename)


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
        POM.__init__(self,
                groupId='de.tu_darmstadt.penchy',
                artifactId='penchy-bootstrap',
                name='penchy-bootstrap',
                url='http://www.tu-darmstadt.de',
                version=penchy_version,
                packaging='jar',  # won't work with pom
                )

        self.add_dependency(MavenDependency(
            groupId='de.tu_darmstadt.penchy',
            artifactId='penchy',
            version=penchy_version,
            classifier='py',
            artifact_type='zip'))
