"""
PenchY.

 :copyright: PenchY Developers 2011-2012, see AUTHORS
 :license: MIT License, see LICENSE
"""
import sys

# Version will be replaced by maven!
__version__ = '0.1'

is_server = sys.argv[0].endswith('penchy')
is_client = not is_server
