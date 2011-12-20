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
    This class represents a Maven Dependency.

    A sample Maven Dependency might look like::

        dep = MavenDependency('de.tu_darmstadt.penchy',
                              'pia', '2.0.0.0', 'http://mvn.0x0b.de')
    """
    def __init__(self, groupId, artifactId, version, repo=None,
            classifier=None, artifact_type=None, packaging=None):
        """
        :param groupId: the maven group id.
        :type groupId: string
        :param artifactId: the maven artifact id.
        :type artifactId: string
        :param version: the version of the artifact.
        :type version: string
        :param repo: the maven repository to use.
        :type repo: string
        :param classifier: the classifier of the artifact.
        :type classifier: string
        :param artifact_type: the type of the artifact.
        :type artifact_type: string
        :param packaging: the packaging of the artifact.
        :type packaging: string
        """
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

    Duplicates are discarded, so no repository or dependency will
    be defined twice in the POM.

    Keywords are directly translated into children of the <project>
    node::

        POM(groupId='de.tu_darmstadt.penchy').write('pom.xml')

    would result in something like::

        <project>
            <groupId>de.tu_darmstadt.penchy</groupId>
        </project>
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
        :type dep: :class:`MavenDependency`
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

    def add_repository(self, url, identifier=None):
        """
        Adds a repository to the POM.

        The identifier of the repository will be equal to
        the url by default.

        :param url: the URL of the repository
        :type url: string
        """
        if url in self.repository_list:
            return
        
        if not identifier:
            identifier = url

        e = SubElement(self.repository_tree, 'repository')
        dict2tree(e, {'url': url, 'id': identifier})

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
