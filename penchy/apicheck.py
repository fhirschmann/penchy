"""
Provides methods which detect changes in PenchY's dependencies.

If this module causes errors, they are most likely caused by
api changes in PenchY's dependencies.
"""
import logging
import inspect
from inspect import ArgSpec

log = logging.getLogger(__name__)


def compare_argspec(func, expected):
    actual = inspect.getargspec(func)
    if not expected == actual:
        log.warning("Arguments for %s in %s have changed:\nExpected:\n%s\nActual:\n%s" % \
                (func.__name__, func.__module__, expected, actual))
        return True
    else:
        return False


def checkattr(func, attr):
    if not hasattr(func, attr):
        log.error("%s in %s no longer has a %s attribute" % (func.__name__,
            func.__module__, attr))
        return True
    else:
        return False


def check_paramiko():
    """
    Check for API changes in paramiko.
    """
    log.debug("Checking for API changes in paramiko")
    try:
        import paramiko
    except ImportError:
        log.error("Could not import paramiko - did you install it?")
        raise

    checkattr(paramiko, 'SSHClient')
    checkattr(paramiko.SSHClient, 'open_sftp')
    checkattr(paramiko.SFTPClient, 'open')
    checkattr(paramiko.SSHClient, 'connect')
    checkattr(paramiko.SFTPClient, 'put')
    checkattr(paramiko.SFTPClient, 'mkdir')

    expected = ArgSpec(args=['self', 'hostname', 'port', 'username',
        'password', 'pkey', 'key_filename', 'timeout', 'allow_agent',
        'look_for_keys', 'compress'], varargs=None, keywords=None,
        defaults=(22, None, None, None, None, None, True, True, False))
    compare_argspec(paramiko.SSHClient.connect, expected)

    expected = ArgSpec(args=['self', 'localpath', 'remotepath',
        'callback', 'confirm'], varargs=None, keywords=None,
        defaults=(None, True))
    compare_argspec(paramiko.SFTPClient.put, expected)

    expected = ArgSpec(args=['self', 'path', 'mode'], varargs=None,
            keywords=None, defaults=(511,))
    compare_argspec(paramiko.SFTPClient.mkdir, expected)
