import sys

# Version will be replaced by maven!
__version__ = '0.1'

if sys.argv[0].endswith('penchy'):
    is_server = True
else:
    is_server = False

is_client = not is_server
