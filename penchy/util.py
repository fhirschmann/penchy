"""
This module provides miscellaneous utilities.

 .. moduleauthor:: Fabian Hirschmann <fabian@hirschm.net>
 .. moduleauthor:: Michael Markert <markert.michael@googlemail.com>

 :copyright: PenchY Developers 2011-2012, see AUTHORS
 :license: MIT License, see LICENSE
"""

import hashlib
import functools
import os
import shutil
import sys
import imp
import logging
import tempfile
import pkg_resources
import signal

from contextlib import contextmanager
from xml.etree.ElementTree import SubElement

from penchy.compat import update_hasher


log = logging.getLogger(__name__)


class _memoized(object):
    """
    Decorator that caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned, and
    not re-evaluated.
    """

    def __init__(self, func):
        self.func = func
        self.cache = {}

    def __call__(self, *args):
        try:
            return self.cache[args]
        except KeyError:
            value = self.func(*args)
            self.cache[args] = value
            return value
        except TypeError:
            # uncachable -- for instance, passing a list as an argument.
            # Better to not cache than to blow up entirely.
            return self.func(*args)

    def __repr__(self):  # pragma: no cover
        """Return the function's docstring."""
        return self.func.__doc__

    def __get__(self, obj, objtype):
        """Support instance methods."""
        return functools.partial(self.__call__, obj)


def memoized(f):
    """
    Wraps the _memoized decorator using functools so that,
    for example, the correct docstring will be used.

    :param f: function to memoize
    :type f: function
    :return: memoized function
    :rtype: function
    """
    memoize = _memoized(f)

    @functools.wraps(f)
    def helper(*args, **kwargs):
        return memoize(*args, **kwargs)

    return helper


def tree_pp(elem, level=0):
    """
    Pretty-prints an ElementTree.

    :param elem: root node
    :type elem: :class:`~xml.etree.ElementTree.Element`
    :param level: current level in tree
    :type level: int
    """
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            tree_pp(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def dict2tree(elem, dict_):
    """
    Add the content of ``dict_`` to ``elem`` aus subelements.

    :param elem: parent element
    :type elem: :class:`xml.etree.ElementTree.Element`
    :param dict_: dict to add to ``elem``
    :type dict_: dict
    """
    for key in dict_:
        if dict_[key]:
            e = SubElement(elem, key)
            e.text = dict_[key]


def dict2string(dict_, attribs=None):
    """
    PrettyPrints a dictionary as string.

    :param dict_: dict to print
    :type dict_: dict
    :returns: dict_ as string
    :rtype: str
    """
    return ", ".join("{0}={1}".format(key, dict_[key]) for key in dict_
                     if attribs is None or key in attribs)


def sha1sum(filename, blocksize=65536):
    """
    Returns the sha1 hexdigest of a file.
    """
    hasher = hashlib.sha1()

    with open(filename, 'r') as afile:
        buf = afile.read(blocksize)
        while len(buf) > 0:
            update_hasher(hasher, buf)
            buf = afile.read(blocksize)

    return hasher.hexdigest()


@contextmanager
def tempdir(prefix='penchy-invocation', delete=False):
    """
    Contextmanager to execute in new created temporary directory.

    :param prefix: prefix of the temporary directory
    :type prefix: str
    :param delete: delete the temporary directory afterwards
    :type delete: bool
    """
    fwd = os.getcwd()
    cwd = tempfile.mkdtemp(prefix=prefix)
    os.chdir(cwd)
    yield
    os.chdir(fwd)
    if delete:
        shutil.rmtree(cwd)


def find_bootstrap_client():
    """
    Returns the path of the penchy bootstrap client.

    :returns: path of bootstrap client
    :rtype: str
    """
    import penchy
    return pkg_resources.resource_filename('penchy',
            os.path.join('../', 'bin', 'penchy_bootstrap'))


def load_job(filename):
    """
    Loads a job.

    :param filename: filename of the job
    :type filename: str
    """

    assert 'config' in sys.modules, "You have to load the penchyrc before a job"

    with disable_write_bytecode():
        job = imp.load_source('job', filename)
    log.info("Loaded job from %s" % filename)
    return job


def load_config(filename):
    """
    Loads the config module from filename. Looks
    in the current working directory as well.

    :param filename: filename of the config file
    :type filename: str
    """
    try:
        with disable_write_bytecode():
            config = imp.load_source('config', filename)
    except IOError:
        raise IOError("Config file could not be loaded from: %s" % filename)

    log.info("Loaded configuration from %s" % filename)
    return config


def get_config_attribute(config, name, default):
    """
    Returns an attribute of a config module or the
    default value.

    :param config: config module to use
    :param name: attribute name
    :type name: str
    :param default: default value
    """
    if hasattr(config, name):
        return getattr(config, name)
    else:
        return default


@contextmanager
def disable_write_bytecode():
    """
    Contextmanager to temporarily disable writing bytecode while executing.
    """
    old_state = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    yield
    sys.dont_write_bytecode = old_state


def pass_signal_to_child(proc):
    """
    This will register a signal handler for SIGTERM for
    a givem :class:`subprocess.Popen` object.

    :param proc: Process to register signal for
    :type proc: :class:`subprocess.Popen`
    """
    signal_handler = lambda num, frame: proc.send_signal(num)
    signal.signal(signal.SIGTERM, signal_handler)
