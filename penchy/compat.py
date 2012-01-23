"""
This module contains code that helps to be compatible to python2.{6,7} and
python3.x.

If python2 support is no longer needed, the removal of this module is strongly
encouraged.
"""
import sys
from contextlib import contextmanager


on_python3 = sys.version_info[0] == 3

if on_python3:
    unicode = str
    str = bytes

if sys.version_info >= (2, 7):  # pragma: no cover
    import unittest
else:
    try:
        import unittest2 as unittest
    # allow that python2.6 nodes don't depend on unittest2
    # will lead to errors on running tests if except triggers
    except ImportError:
        import unittest


# Copied from Python 2.6 contextlib
# XXX: this is only necessary for python2.6 after dropping support for python2.6
# you may want to replace this with ``with``-Statements native support for this
@contextmanager
def nested(*managers):
    """Support multiple context managers in a single with-statement.

    Code like this:

        with nested(A, B, C) as (X, Y, Z):
            <body>

    is equivalent to this:

        with A as X:
            with B as Y:
                with C as Z:
                    <body>

    """
    exits = []
    vars = []
    exc = (None, None, None)
    try:
        for mgr in managers:
            exit = mgr.__exit__
            enter = mgr.__enter__
            vars.append(enter())
            exits.append(exit)
        yield vars
    except Exception as e:
        exc = sys.exc_info()
        exception = e
    finally:
        while exits:
            exit = exits.pop()
            try:
                if exit(*exc):
                    exc = (None, None, None)
            except Exception as e:
                exc = sys.exc_info()
                exception = e
        if exc != (None, None, None):
            # Don't rely on sys.exc_info() still containing
            # the right information. Another exception may
            # have been raised and caught by an exit method
            raise exception


def write(file, string, codec='utf8'):
    """
    Write ``string`` to ``file`` encoding with codec.

    :param file: file object to write to
    :type file: file
    :param string: string to write
    :type string: str, unicode, bytes
    :param codec: how to encode unicode types
    """
    if isinstance(string, str):
        file.write(string)
    elif isinstance(string, unicode):
        file.write(string.encode(codec))


def update_hasher(hasher, string, codec='utf8'):
    """
    Update ``hasher`` with ``string``.

    :param string: string to hash
    :type string: str, unicode, bytes
    :param codec: how to encode unicode types
    :returns: updated hasher
    """
    if isinstance(string, str):
        hasher.update(string)
    elif isinstance(string, unicode):
        hasher.update(string.encode(codec))

    return hasher
