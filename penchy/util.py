"""
This module provides miscellaneous utilities.
"""

import hashlib
import functools
import os
import shutil
import sys
import imp
import tempfile
import pkg_resources

from contextlib import contextmanager
from xml.etree.ElementTree import SubElement


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
    """
    memoize = _memoized(f)

    @functools.wraps(f)
    def helper(*args, **kwargs):
        return memoize(*args, **kwargs)

    return helper


def extract_classpath(options):
    """
    Return the jvm classpath from a sequence of option strings.

    :param options: sequence of jvm options to search
    :returns: classpath in options
    :rtype: string
    """
    # a later classpath overwrites previous definitions so we have to search
    # from the end
    options = options[::-1]
    classpath = ''
    for i, x in enumerate(options):
        if x in ('-cp', '-classpath'):
            try:
                # cp is positioned before option because order is reversed,
                # take abs to avoid referencing from end
                cp_index = abs(i - 1)
                classpath = options[cp_index]
            except IndexError, e:
                classpath = ''
            break
    return classpath


def tree_pp(elem, level=0):
    """
    Pretty-prints an ElementTree.
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


def dict2tree(elem, dictionary):
    for k, v in dictionary.items():
        if v:
            e = SubElement(elem, k)
            e.text = v


def dict2string(d, attribs=None):
    """
    PrettyPrints a dictionary as string.
    """
    s = []
    for k, v in d.items():
        if not attribs or k in attribs:
            if v:
                s.append("%s=%s" % (k, v))
    return ", ".join(s)


def sha1sum(filename, blocksize=65536):
    """
    Returns the sha1 hexdigest of a file.
    """
    hasher = hashlib.sha1()

    with open(filename, 'r') as afile:
        buf = afile.read(blocksize)
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(blocksize)

    return hasher.hexdigest()


@contextmanager
def tempdir(prefix='penchy-invocation', delete=False):
    """
    Execute in new created temporary directory.
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
    """
    import penchy
    return pkg_resources.resource_filename('penchy',
            os.path.join('../', 'bin', 'penchy_bootstrap'))


def load_job(filename, config):
    """
    Loads a job.

    :param filename: filename of the job
    :type filename: string
    :param config: config file to export to job namespace
    """
    sys.modules['config'] = config
    job = imp.load_source('job', filename)
    return job


def load_config(filename):
    """
    Loads the config module from filename. Looks
    in the current working directory as well.

    :param filename: filename of the config file
    :type filename: string
    :returns: tuple of (config object, config filename)
    :rtype: tuple
    """
    try:
        config = imp.load_source('config', filename)
        actual_filename = filename
    except IOError:
        try:
            config = imp.load_source('config', 'penchyrc')
            actual_filename = 'penchyrc'
        except IOError:
            raise IOError("Config file could not be loaded from: %s or ./penchyrc" % filename)

    return (config, actual_filename)
