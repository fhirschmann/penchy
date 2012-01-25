import os
import sys
import hashlib
from random import randint
from tempfile import NamedTemporaryFile

from penchy import util
from penchy.compat import unittest, write, update_hasher


class TempdirTest(unittest.TestCase):
    def test_change(self):
        cwd = os.getcwd()
        with util.tempdir():
            self.assertNotEquals(cwd, os.getcwd())
        self.assertEquals(cwd, os.getcwd())


class HashTest(unittest.TestCase):
    def test_sha1sum(self):
        text = 'sha1 checksum test'
        hasher = hashlib.sha1()
        with NamedTemporaryFile(delete=False) as tf:
            write(tf, text)
            tf.flush()
            self.assertEqual(util.sha1sum(tf.name),
                             update_hasher(hasher, text).hexdigest())


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
            write(tf, 'foo = %s' % i)
            write(tf, os.linesep)
            tf.flush()
            config = util.load_config(tf.name)
            self.assertEquals(config.foo, i)

        self.assertTrue('config' in sys.modules)
        with self.assertRaises(IOError):
            util.load_config(fname)

    def test_load_job(self):
        j = 'world dominance'
        with NamedTemporaryFile() as tf:
            write(tf, 'job = "%s"' % j)
            write(tf, os.linesep)
            tf.flush()
            job = util.load_job(tf.name)
            self.assertEquals(job.job, j)

    def test_load_job_without_config(self):
        if 'config' in sys.modules:
            del sys.modules['config']

        with self.assertRaises(AssertionError):
            self.test_load_job()
