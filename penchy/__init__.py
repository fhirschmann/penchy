# Version will be replaced by maven!
__version__ = '0.1'

import sys


if sys.version_info > (3, 0):
    from . import log
else:
    import log

log.configure()

del log
del sys
