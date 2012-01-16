#!/usr/bin/env python

import logging
import os
from subprocess import Popen, PIPE
from tempfile import NamedTemporaryFile
from xml.etree.ElementTree import Element, SubElement, ElementTree

from penchy import __version__ as penchy_version
from penchy.util import memoized, tree_pp, dict2tree, dict2string, sha1sum


log = logging.getLogger(__name__)


@memoized
def get_classpath(path=None):
    """
    Returns the Java classpath using Maven.

    This method expects a Maven POM (pom.xml).
    A POM can be generated using the
    :class:`BootstrapPOM` or :class:`POM` class::

        >>> from penchy.maven import BootstrapPOM, get_classpath
        >>> from penchy.jobs.workloads import ScalaBench
        >>> pom = BootstrapPOM()
        >>> for dep in ScalaBench.DEPENDENCIES:
        ...     pom.add_dependency(dep)
        ...
        >>> pom.write()
        >>> get_classpath()
        '/home/fabian/.m2/repository/de/tu_darmstadt/penchy/penchy/0.1/penchy-0.1-py.zip:/home/fabian/.m2/repository/org/scalabench/benchmarks/scala-benchmark-suite/0.1.0-SNAPSHOT/scala-benchmark-suite-0.1.0-SNAPSHOT.jar'

    :param path: path to look for pom.xml in
    :type path: string
    :returns: java classpath
    :rtype: string
    """
    for p in ([path, path + os.sep + 'pom.xml'] if path else []) + ['pom.xml']:
        if os.path.isfile(p):
            path = p
            break

    if not path or not os.path.isfile(path):
        raise OSError("No pom.xml found!")

    log.debug("Using %s" % path)
    proc = Popen(['mvn', '-f', path, 'dependency:build-classpath'], stdout=PIPE)
    stdout, _ = proc.communicate()

    if proc.returncode is not 0:  # pragma: no cover
        log.error(stdout)
        raise MavenError("The classpath could not be determined: ")

    for line in stdout.split("\n"):
        if not line.startswith("["):
            log.debug("Using classpath %s" % line)
            return line

    raise MavenError("The classpath was not in maven's output")  # pragma: no cover


class MavenError(Exception):
    pass


class IntegrityError(Exception):
    pass


class POMError(Exception):
    pass


class MavenDependency(object):
    """
    This class represents a Maven Dependency.

    A sample Maven Dependency might look like::

        dep = MavenDependency('de.tu_darmstadt.penchy',
                              'pia', '2.0.0.0', 'http://mvn.0x0b.de')

    This class will try its best to determine the filename on its own,
    but since it's not always clear what the exact filename will be
    like, it might be neccessary to pass it as keyword argument.
    If the filename cannot be determined, :class:`LookupError` will
    be thrown.

    If the checksum parameter is specified, the file's sha1 checksum
    will be checked against this checksum. An artifact's checksum can
    be computed using::

        $ sha1sum myartifact-0.1.jar

    A real life :class:`MavenDependency` making use of the checksum
    feature would look like::

        MavenDependency(
            'org.scalabench.benchmarks',
            'scala-benchmark-suite',
            '0.1.0-20110908.085753-2',
            'http://repo.scalabench.org/snapshots/',
            filename='scala-benchmark-suite-0.1.0-SNAPSHOT.jar',
            checksum='fb68895a6716cc5e77f62ed7992d027b1dbea355')

    """
    POM_ATTRIBS = ('version', 'groupId', 'artifactId', 'version',
            'classifier', 'packaging', 'type')

    def __init__(self, groupId, artifactId, version, repo=None,
            classifier=None, artifact_type=None, packaging=None,
            filename=None, checksum=None):
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
        :param filename: filename of the artifact; guessed if not specified.
        :type filename: string
        :param checksum: the sha1 checksum of the file.
        :type checksum: string
        """
        self.groupId = groupId
        self.artifactId = artifactId
        self.version = version
        self.repo = repo
        self.classifier = classifier
        self.type = artifact_type
        self.packaging = packaging
        self._filename = filename
        self.wanted_checksum = checksum
        self.pom_path = None

    def __key(self):
        return (self.groupId, self.artifactId, self.version)

    def __eq__(self, other):
        return isinstance(other, MavenDependency) and \
                self.__key() == other.__key()

    def __hash__(self):
        return hash(self.__key())

    def __str__(self):  # pragma: no cover
        return "<%s: %s>" % (self.__class__.__name__,
                dict2string(self.__dict__, MavenDependency.POM_ATTRIBS))

    @property
    def filename(self):
        """
        The full absolute path to this artifact.

        :return: path to artifact
        :rtype: string
        """
        cp = get_classpath(self.pom_path).split(":")

        for artifact in cp:
            if self._filename:
                if os.path.basename(artifact) == self._filename:
                    return artifact
            else:
                if os.path.basename(artifact).startswith("-".join((
                    self.artifactId, self.version))):
                    return artifact

        if not self._filename:  # pragma: no cover
            log.error("Please specify the filename as argument to %s." % self)
        else:
            log.error("Incorrect artifact filename for %s." % self)

        raise LookupError('Artifact filename could not be determined!')

    @filename.setter
    def filename(self, value):
        self._filename = value

    @property
    @memoized
    def actual_checksum(self):
        """
        The actual checksum of this artifact. Will be computed and cached.
        """
        return sha1sum(self.filename)

    def check_checksum(self):
        """
        Checks if the checksum is correct.
        Raises an :class:`IntegrityError` if not.
        """
        if not self.wanted_checksum:
            return True

        if self.wanted_checksum == self.actual_checksum:
            return True
        else:
            raise IntegrityError(
                    "Checksums don't match! Actual %s; Wanted %s" % \
                    (self.actual_checksum, self.wanted_checksum))


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
    REQUIRED_ATTRIBS = set(('artifactId', 'groupId', 'version'))

    def __init__(self, **kwargs):
        if not set(kwargs.keys()).issuperset(self.__class__.REQUIRED_ATTRIBS):
            raise POMError(", ".join(self.__class__.REQUIRED_ATTRIBS) +
                    " are required keywords")
        self.repository_list = set()
        self.dependency_list = set()

        self.root = Element('project')
        self.tree = ElementTree(self.root)
        self.dependency_tree = SubElement(self.root, 'dependencies')
        self.repository_tree = SubElement(self.root, 'repositories')

        attribs = POM.ATTRIBS.copy()
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

        clean_dep = dict((k, v) for k, v in dep.__dict__.items() if k in
                MavenDependency.POM_ATTRIBS and v)

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

    def write(self, filename='pom.xml', pretty=True):
        """
        Writes the POM to a file.

        :param filename: the filename to write to
        :type filename: string
        :param pretty: pretty-print resulting file
        :type pretty: bool
        """
        if pretty:
            tree_pp(self.root)

        if os.path.isdir(filename):  # pragma: no cover
            filename += os.sep + 'pom.xml'

        self.tree.write(filename)


class BootstrapPOM(POM):
    """
    This class represents a bootstrap POM which is used to deploy
    PenchY and its dependencies.

    All it does is extending :class:`POM` so that the POM depends
    on the PenchY client as found in the Maven Repository.
    """
    ATTRIBS = {
            'groupId': 'de.tu_darmstadt.penchy',
            'artifactId': 'penchy-bootstrap',
            'name': 'penchy-bootstrap',
            'url': 'http://www.tu-darmstadt.de',
            'version': penchy_version,
            'packaging': 'jar',  # won't work with pom
            }
    DEPENDENCY = {
            'groupId': 'de.tu_darmstadt.penchy',
            'artifactId': 'penchy',
            'version': penchy_version,
            'classifier': 'py',
            'repo': 'http://mvn.0x0b.de',
            'artifact_type': 'zip'}

    def __init__(self):
        POM.__init__(self, **BootstrapPOM.ATTRIBS)
        self.add_dependency(MavenDependency(**BootstrapPOM.DEPENDENCY))


class PenchyPOM(POM):
    """
    This class represents the POM for PenchY. It is used to install
    PenchY's dependencies.

    This is similar to :class:`BootstrapPOM`
    """
    ATTRIBS = {
            'groupId': 'de.tu_darmstadt.penchy',
            'artifactId': 'penchy',
            'name': 'penchy',
            'url': 'http://www.tu-darmstadt.de',
            'version': penchy_version,
            'packaging': 'jar',  # won't work with pom
            }

    def __init__(self):
        POM.__init__(self, **PenchyPOM.ATTRIBS)


def makeBootstrapPom():
    """
    Creates a Bootstrap POM and returns the temporary
    file it has been written to.
    """
    tf = NamedTemporaryFile()
    pom = BootstrapPOM()
    pom.write(tf.name)
    return tf


def write_penchy_pom(dependencies, path):
    """
    Creates a POM specifying dependencies.

    :param dependencies: dependencies to install
    :type dependencies: Iterable of :class:`MavenDependency`
    :param path: path to write the pom to
    :type path: str
    """
    pom = PenchyPOM()
    for dependency in dependencies:
        pom.add_dependency(dependency)
    pom.write(path)
