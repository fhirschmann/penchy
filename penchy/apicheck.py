"""
Provides methods which detect changes in PenchY's dependencies.

If this module causes errors, they are most likely caused by
api changes in PenchY's dependencies.
"""
import logging
import inspect
from inspect import ArgSpec

from penchy.util import die

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
    try:
        package = '' if not mod.__package__ else 'in package %s' % mod.__package__
    except AttributeError:
        package = ''
    if not hasattr(mod, attr):
        die('%s%s has no %s attribute, which was expected' %
            (mod.__name__, package, attr))


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
        die('Could not import paramiko - did you install it?')

    checkattrs([
        (paramiko, ['Transport', 'SSHClient', 'SFTPClient'])
    ])
    checkattrs([
        (paramiko.Transport, 'is_active'),
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


def check_matplotlib():
    """
    Check for API changes in matplotlib.
    """
    log.debug('Checking for API changes in matplotlib')
    try:
        import matplotlib
        import matplotlib.figure
        import matplotlib.pyplot
    except ImportError:
        die('Could not import matplotlib - did you install it?')

    checkattrs([
        (matplotlib.pyplot, 'figure'),
        (matplotlib.figure, 'Figure'),
        ])

    expected = ArgSpec(args=['num', 'figsize', 'dpi', 'facecolor',
        'edgecolor', 'frameon', 'FigureClass'], varargs=None,
        keywords='kwargs', defaults=(None, None, None, None,
            None, True, matplotlib.figure.Figure))
    compare_argspec(matplotlib.pyplot.figure, expected)


def check_scipy():
    """
    Check for API changes in scipy.
    """
    log.debug('Checking for API changes in scipy')
    try:
        from scipy.stats import t, norm
    except ImportError:
        die('Could not import scipy - did you install it?')

    checkattrs([
        (t, 'ppf'),
        (norm, 'ppf'),
        ])

    expected = ArgSpec(args=['self', 'q'], varargs='args', keywords='kwds',
            defaults=None)
    compare_argspec(t.ppf, expected)
    compare_argspec(norm.ppf, expected)


def check_all():
    check_paramiko()
    check_matplotlib()
    check_scipy()


if __name__ == '__main__':
    logging.basicConfig()
    check_all()
