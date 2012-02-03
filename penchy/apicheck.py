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
        log.warning("Arguments for %s have changed:\nExpected:\n%s\nActual:\n%s" % \
                (func, expected, actual))


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

    getattr(paramiko, 'SSHClient')
    getattr(paramiko.SSHClient, 'open_sftp')
    getattr(paramiko.SFTPClient, 'open')

    getattr(paramiko.SSHClient, 'connect')
    expected = ArgSpec(args=['self', 'hostname', 'port', 'username',
        'password', 'pkey', 'key_filename', 'timeout', 'allow_agent',
        'look_for_keys', 'compress'], varargs=None, keywords=None,
        defaults=(22, None, None, None, None, None, True, True, False))
    compare_argspec(paramiko.SSHClient.connect, expected)

    getattr(paramiko.SFTPClient, 'put')
    expected = ArgSpec(args=['self', 'localpath', 'remotepath',
        'callback', 'confirm'], varargs=None, keywords=None,
        defaults=(None, True))
    compare_argspec(paramiko.SFTPClient.put, expected)

    getattr(paramiko.SFTPClient, 'mkdir')
    expected = ArgSpec(args=['self', 'path', 'mode'], varargs=None,
            keywords=None, defaults=(511,))
    compare_argspec(paramiko.SFTPClient.mkdir, expected)
