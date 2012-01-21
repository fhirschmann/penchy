"""
This module contains code that help to be compatible to python2.{6,7} and
python3.x.

If python2 support is no longer needed, the removal of this module is strongly
encouraged.
"""

import sys
from contextlib import contextmanager


if sys.version_info >= (2, 7):  # pragma: no cover
    import unittest
else:
    import unittest2 as unittest


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
    except:
        exc = sys.exc_info()
    finally:
        while exits:
            exit = exits.pop()
            try:
                if exit(*exc):
                    exc = (None, None, None)
            except:
                exc = sys.exc_info()
        if exc != (None, None, None):
            # Don't rely on sys.exc_info() still containing
            # the right information. Another exception may
            # have been raised and caught by an exit method
            raise exc[0], exc[1], exc[2]
