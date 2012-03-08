"""
This module provides miscellaneous utilities.

 .. moduleauthor:: Fabian Hirschmann <fabian@hirschm.net>
 .. moduleauthor:: Michael Markert <markert.michael@googlemail.com>

 :copyright: PenchY Developers 2011-2012, see AUTHORS
 :license: MIT License, see LICENSE
"""
from __future__ import print_function

import hashlib
import imp
import logging
import os
import shutil
import sys
import tempfile
import inspect
from contextlib import contextmanager
from functools import wraps
from xml.etree import ElementTree
from xml.etree.ElementTree import SubElement
from tempfile import NamedTemporaryFile

from penchy.compat import write
from penchy import bootstrap


log = logging.getLogger(__name__)


def memoized(f):
    """
    Decorator that provides memoization, i.e. a cache that saves the result of
    a function call and returns them if called with the same arguments.

    The function will not be evaluated if the arguments are present in the
    cache.
    """
    cache = {}

    @wraps(f)
    def _memoized(*args, **kwargs):
        key = tuple(args) + tuple(kwargs.items())
        try:
            if key in cache:
                return cache[key]
        except TypeError:       # if passed an unhashable type evaluate directly
            return f(*args, **kwargs)
        ret = f(*args, **kwargs)
        cache[key] = ret
        return ret
    return _memoized


# Copyright (c) 1995-2010 by Frederik Lundh
# <http://effbot.org/zone/element-lib.htm#prettyprint>
# Licensed under the terms of the Historical Permission Notice
# and Disclaimer, see <http://effbot.org/zone/copyright.htm>.
def tree_pp(elem, level=0):
    """
    Pretty-prints an ElementTree.

    :param elem: root node
    :type elem: :class:`~xml.etree.ElementTree.Element`
    :param level: current level in tree
    :type level: int
    """
    i = '\n' + level * '  '
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + '  '
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
    Transform the given dictionary to a ElementTree and
    add it to the given element.

    :param elem: parent element
    :type elem: :class:`xml.etree.ElementTree.Element`
    :param dict_: dict to add to ``elem``
    :type dict_: dict
    """
    for key in dict_:
        if dict_[key]:
            e = SubElement(elem, key)
            if type(dict_[key]) == dict:
                dict2tree(e, dict_[key])
            else:
                e.text = dict_[key]


def sha1sum(filename, blocksize=65536):
    """
    Returns the sha1 hexdigest of a file.
    """
    hasher = hashlib.sha1()

    with open(filename, 'rb') as afile:
        buf = afile.read(blocksize)
        while len(buf) > 0:
            hasher.update(buf)
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


def make_bootstrap_client():
    """
    Returns the temporary filename of a file containing
    the bootstrap client.
    """
    tf = NamedTemporaryFile()
    source = inspect.getsource(bootstrap)
    write(tf, source)
    tf.flush()
    return tf


def load_job(filename):
    """
    Loads a job.

    :param filename: filename of the job
    :type filename: str
    """

    assert 'config' in sys.modules, 'You have to load the penchyrc before a job'

    with disable_write_bytecode():
        job = imp.load_source('job', filename)
    log.info('Loaded job from %s' % filename)
    return job


def load_config(filename):
    """
    Loads the config module from filename.

    :param filename: filename of the config file
    :type filename: str
    """
    with disable_write_bytecode():
        config = imp.load_source('config', filename)

    log.info('Loaded configuration from %s' % filename)
    return config


def get_config_attribute(config, name, default_value):
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
        return default_value


@contextmanager
def disable_write_bytecode():
    """
    Contextmanager to temporarily disable writing bytecode while executing.
    """
    old_state = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    yield
    sys.dont_write_bytecode = old_state


def default(value, replacement):
    """
    Check if ``value`` is ``None`` and then return ``replacement`` or else
    ``value``.

    :param value: value to check
    :param replacement: default replacement for value
    :returns: return the value or replacement if value is None
    """
    return value if value is not None else replacement


def die(msg):
    """
    Print msg to stderr and exit with exit code 1.

    :param msg: msg to print
    :type msg: str
    """
    print(msg, file=sys.stderr)
    sys.exit(1)


def extract_maven_credentials(id_, path=os.path.expanduser('~/.m2/settings.xml')):
    """
    Extracts the username and password for a given ``id_``
    from a maven settings.xml.

    :param id_: id of the remote machine as defined in the settings file
    :type id_: str
    :param filename: path to settings.xml
    :type filename: str
    """
    xmlns = '{http://maven.apache.org/SETTINGS/1.0.0}'  # xml namespace
    tree = ElementTree.parse(path).getroot()
    servers = tree.find('{0}servers'.format(xmlns))
    for server in servers.findall('{0}server'.format(xmlns)):
        if server.find('{0}id'.format(xmlns)).text == id_:
            return server.find('{0}username'.format(xmlns)).text, \
                   server.find('{0}password'.format(xmlns)).text

    raise ValueError("Credentials for '{0}' not found".format(id_))
