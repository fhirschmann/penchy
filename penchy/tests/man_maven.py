from tempfile import NamedTemporaryFile

from penchy.maven import *
from penchy.tests.unit import unittest


class MavenTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dep = MavenDependency('log4j', 'log4j', '1.2.9',
                checksum='55856d711ab8b88f8c7b04fd85ff1643ffbfde7c')
        cls.tf = NamedTemporaryFile()
        cls.dep.pom_path = cls.tf.name
        cls.pom = POM(groupId='a', artifactId='b', version='1')
        cls.pom.add_dependency(cls.dep)
        cls.pom.write(cls.tf.name)

    def setUp(self):
        self.dep.pom_path = self.tf.name
        self.dep.filename = None

    def test_get_classpath(self):
        classpath = get_classpath(self.tf.name)
        self.assertTrue(classpath.endswith('log4j-1.2.9.jar'))

    def test_get_filename(self):
        self.assertTrue(self.dep.filename.endswith('log4j-1.2.9.jar'))

    def test_get_filename2(self):
        self.dep.filename = 'log4j-1.2.9.jar'
        self.assertTrue(self.dep.filename.endswith('log4j-1.2.9.jar'))

    def test_get_incorrect_filename(self):
        self.dep.filename = 'foo.jar'
        self.assertRaises(LookupError, lambda: self.dep.filename)

    def test_pom_not_found(self):
        self.assertRaises(OSError, get_classpath, '')

    def test_checksum(self):
        self.assertEquals(self.dep.actual_checksum,
                '55856d711ab8b88f8c7b04fd85ff1643ffbfde7c')

    def test_checksum2(self):
        self.assertTrue(self.dep.check_checksum())

    def test_checksum3(self):
        with NamedTemporaryFile() as tf:
            dep = MavenDependency('log4j', 'log4j', '1.2.9',
                    checksum='asdf')
            dep.pom_path = tf.name
            pom = POM(groupId='a', artifactId='b', version='1')
            pom.add_dependency(dep)
            pom.write(tf.name)
            self.assertRaises(IntegrityError, dep.check_checksum)
