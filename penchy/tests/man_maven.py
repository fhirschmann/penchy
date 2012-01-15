from tempfile import NamedTemporaryFile

from penchy.maven import *
from penchy.tests.unit import unittest


class MavenTest(unittest.TestCase):
    def setUp(self):
        self.dep = MavenDependency('log4j', 'log4j', '1.2.9')
        self.tf = NamedTemporaryFile()
        self.dep.pom_path = self.tf.name
        self.pom = POM(groupId='a', artifactId='b', version='1')
        self.pom.add_dependency(self.dep)
        self.pom.write(self.tf.name)

    def test_get_classpath(self):
        classpath = get_classpath(self.tf.name)
        self.assertTrue(classpath.endswith('log4j-1.2.9.jar'))

    def test_get_filename(self):
        self.assertTrue(self.dep.filename.endswith('log4j-1.2.9.jar'))

    def test_pom_not_found(self):
        self.assertRaises(OSError, get_classpath, '')
