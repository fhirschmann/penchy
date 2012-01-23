from hashlib import sha1
from tempfile import TemporaryFile
from contextlib import contextmanager

from penchy.compat import unittest, nested, update_hasher


class NestedTest(unittest.TestCase):
    def test_reraising_exception(self):
        e = Exception('reraise this')
        with self.assertRaises(Exception) as raised:
            with nested(TemporaryFile(), TemporaryFile()) as (a, b):
                raise e

        self.assertEqual(raised.exception, e)

    def test_raising_on_exit(self):
        @contextmanager
        def raising_cm(exception):
            yield
            raise exception

        on_exit = Exception('throw on exit')
        with self.assertRaises(Exception) as raised:
            with nested(raising_cm(on_exit)):
                pass
        self.assertEqual(raised.exception, on_exit)


class HasherTest(unittest.TestCase):
    def setUp(self):
        self.control = sha1()
        self.h = sha1()

    def test_str_hash(self):
        s = 'foo'
        self.control.update(s)
        update_hasher(self.h, s)
        self.assertEqual(self.control.hexdigest(),
                         self.h.hexdigest())

    def test_unicode_hash(self):
        u = u'foo'
        self.control.update(u.encode('utf8'))
        update_hasher(self.h, u)
        self.assertEqual(self.control.hexdigest(),
                         self.h.hexdigest())
