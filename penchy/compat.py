"""
This module contains code that help to be compatible to python2.{6,7} and
python3.x.

If python2 support is no longer needed, the removal of this module is strongly
encouraged.
"""

import sys


if sys.version_info >= (2, 7):  # pragma: no cover
    import unittest
else:
    import unittest2 as unittest
