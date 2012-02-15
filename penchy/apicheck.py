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
    """
    Compares the specification of the arguments from the given
    function ``func`` with the ``expected`` arguments.

    :param func: function to check
    :type func: callable
    :param expected: expected function signature
    :type expected: :class:`ArgSpec`
    """
    actual = inspect.getargspec(func)
    if not expected == actual:
        log.warning('Arguments for %s in %s have changed:\n'
                'Expected:\n%s\nActual:\n%s' %
                (func.__name__, func.__module__, expected, actual))
        return True
    else:
        return False


def checkattr(mod, attr):
    """
    Checks if the attribute ``attr`` still exists in module
    ``mod``.

    :param mod: module to check
    :type mod: module
    :param attr: attribute to check for
    """
    if not hasattr(mod, attr):
        log.error('%s in %s no longer has a %s attribute' %
                (mod.__name__, mod.__module__, attr))
        return True
    else:
        return False


def checkattrs(seq):
    """
    Checks a sequence of function/attribute pairs using
    `checkattr`.

    :param seq: sequence of a (``func``, ``attr``) or
                (``func``, [``attr``, ``attr``]) pairs
    :type seq: sequence
    """

    for func, attrs in seq:
        if type(attrs) == list:
            for attr in attrs:
                checkattr(func, attr)
        else:
            checkattr(func, attrs)


def check_paramiko():
    """
    Check for API changes in paramiko.
    """
    log.debug('Checking for API changes in paramiko')
    try:
        import paramiko
    except ImportError:
        log.error('Could not import paramiko - did you install it?')
        raise

    checkattrs([
        (paramiko, 'SSHClient'),
        (paramiko.SSHClient, ['open_sftp', 'connect']),
        (paramiko.SFTPClient, ['open', 'put', 'mkdir'])
        ])

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
