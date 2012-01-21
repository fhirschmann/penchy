import os
import sys
from random import randint
from tempfile import NamedTemporaryFile

from penchy import util
from penchy.compat import unittest


class ClasspathTest(unittest.TestCase):

    def test_valid_options(self):
        expected = 'foo:bar:baz'
        options = ['-cp', expected]
        self.assertEquals(util.extract_classpath(options), expected)
        expected = 'foo:bar:baz'
        options = ['-classpath', expected]
        self.assertEquals(util.extract_classpath(options), expected)

    def test_multiple_classpaths(self):
        expected = 'foo:bar:baz'
        options = ['-cp', 'com:org:de', '-cp', expected]
        self.assertEquals(util.extract_classpath(options), expected)

    def test_only_option(self):
        options = ['-cp']
        self.assertEquals(util.extract_classpath(options), '')


class TempdirTest(unittest.TestCase):
    def test_change(self):
        cwd = os.getcwd()
        with util.tempdir():
            self.assertNotEquals(cwd, os.getcwd())
        self.assertEquals(cwd, os.getcwd())


class HashTest(unittest.TestCase):
    def test_sha1sum(self):
        with NamedTemporaryFile(delete=False) as tf:
            tf.write('sha1 checksum test')
            tf.flush()
            self.assertEquals(util.sha1sum(tf.name),
                    '14eb73d6e6e404471f7c71dc2ad114609c51c579')


class MemoizedTest(unittest.TestCase):
    def test_cache(self):
        @util.memoized
        def func():
            return randint(0, 1000)

        self.assertEquals(func(), func())

    def test_docstring(self):
        @util.memoized
        def func():
            """this is a docstring"""
            pass

        self.assertEquals(func.__doc__, "this is a docstring")

    def test_invalid_argument(self):
        @util.memoized
        def func(lst):
            return lst

        self.assertEquals(func([1, 2]), [1, 2])
        self.assertEquals(func([1, 2]), [1, 2])


class MiscTest(unittest.TestCase):
    def test_dict2string(self):
        self.assertEquals(util.dict2string({'foo': 'bar'}), "foo=bar")

    def test_find_bootstrap_client(self):
        self.assertTrue(util.find_bootstrap_client().endswith('penchy_bootstrap'))


class ImportTest(unittest.TestCase):
    def test_load_config(self):
        i = 5
        self.assertFalse('config' in sys.modules)
        with NamedTemporaryFile() as tf:
            # save for writing after close, assures file does not exist
            fname = tf.name
            tf.write('foo = %s' % i)
            tf.write(os.linesep)
            tf.flush()
            config = util.load_config(tf.name)
            self.assertEquals(config.foo, i)

        self.assertTrue('config' in sys.modules)
        with self.assertRaises(IOError):
            util.load_config(fname)

    def test_load_job(self):
        j = 'world dominance'
        with NamedTemporaryFile() as tf:
            tf.write('job = "%s"' % j)
            tf.write(os.linesep)
            tf.flush()
            job = util.load_job(tf.name)
            self.assertEquals(job.job, j)

    def test_load_job_without_config(self):
        if 'config' in sys.modules:
            del sys.modules['config']

        with self.assertRaises(AssertionError):
            self.test_load_job()
