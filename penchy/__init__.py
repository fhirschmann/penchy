"""
PenchY.

 :copyright: PenchY Developers 2011-2012, see AUTHORS
 :license: MIT License, see LICENSE
"""
import sys

# Version will be replaced by maven!
__version__ = '1.0'

is_server = not sys.argv[0].endswith('penchy_bootstrap')
is_client = not is_server
