from tempfile import NamedTemporaryFile
from xml.etree.ElementTree import ElementTree as ET
from random import randint

from penchy.maven import *
from penchy.tests.unit import unittest


class PomTest(unittest.TestCase):
    """
    A POM generated by :class:`POM` should look something like::

        <project>
          <dependencies>
            <dependency>
              <version>version</version>
              <groupId>groupId</groupId>
              <artifactId>artifactId</artifactId>
            </dependency>
          </dependencies>
          <repositories>
            <repository>
              <url>repo</url>
              <id>repo</id>
            </repository>
          </repositories>
          <modelVersion>4.0.0</modelVersion>
        </project>

    """
    def test_pom_attribs(self):
        for attrib in ('groupId', 'artifactId', 'version', 'repo'):
            with NamedTemporaryFile() as tf:
                rand = str(randint(0, 1000))
                p = POM(**{attrib: rand})
                p.write(tf.name)
                tree = ET()
                tree.parse(tf.name)
                self.assertEqual(tree.getroot().find(attrib).text, rand)

    def test_pom_dependency(self):
        dep = MavenDependency('groupId', 'artifactId', 'version', 'repo')

        with NamedTemporaryFile() as tf:
            p = POM()
            p.add_dependency(dep)
            p.write(tf.name)
            tree = ET()
            tree.parse(tf.name)
            root = tree.getroot()
            xdep = root.find('dependencies/dependency')
            for attrib in ('groupId', 'artifactId', 'version'):
                self.assertEqual(xdep.find(attrib).text, attrib)

            self.assertEqual(root.find('repositories/repository/url').text, 'repo')

    def test_bootstrap_pom(self):
        with NamedTemporaryFile() as tf:
            p = BootstrapPOM()
            p.write(tf.name)
            tree = ET()
            tree.parse(tf.name)
            root = tree.getroot()
            from penchy import __version__ as penchy_version

            self.assertEqual(root.find('artifactId').text, 'penchy-bootstrap')
            self.assertEqual(root.find('version').text, penchy_version)


class MavenTest(unittest.TestCase):
    def setUp(self):
        self.d1 = MavenDependency(
                'org.scalabench.benchmarks',
                'scala-benchmark-suite',
                '0.1.0-20110908.085753-2',
                'http://repo.scalabench.org/snapshots/')

        self.d2 = MavenDependency(
                'org.scalabench.benchmarks',
                'scala-benchmark-suite',
                '0.1.0-20110908.085753-2',
                'http://repo.scalabench.org/snapshots/')

        self.d3 = MavenDependency(
                'org.scalabench.benchmarks',
                'scala-benchmark-suite2',
                '0.1',
                'http://repo.scalabench.org/snapshots/')

    def test_mavendep_equal(self):
        self.assertEquals(self.d1, self.d2)

    def test_mavendep_duplicates(self):
        p = POM()
        p.add_dependency(self.d1)
        p.add_dependency(self.d2)
        self.assertEquals(p.dependency_list, set((self.d1,)))

    def test_mavendep_repo_duplicates(self):
        p = POM()
        p.add_repository('foo')
        p.add_repository('foo')
        self.assertEquals(p.repository_list, set(('foo',)))

        p = POM()
        p.add_dependency(self.d1)
        p.add_dependency(self.d2)
        self.assertEquals(p.repository_list, set((self.d1.repo,)))
