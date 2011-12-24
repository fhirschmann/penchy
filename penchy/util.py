"""
This module provides miscellaneous utilities.
"""

import hashlib
import functools

from collections import namedtuple
from xml.etree.ElementTree import SubElement


NodeConfig = namedtuple('NodeConfig', ['host', 'ssh_port', 'username', 'path'])


def topological_sort(start_nodes, dependencies):
    """
    Return a topologically sorted list of :param:`start_nodes` and
    :param:`dependencies`.

    Nodes are checked on identity, not equality.

    Raises a ValueError if no topological sort is possible.

    :param start_nodes: sequence of nodes of graph with no incoming edges
    :param dependencies: sequence of dependency edges
                         ([dependencies], target), dependencies may be of any
                         sequence or be atomic, if there is no dependency it
                         must be ``None``
    :returns: topologically sorted nodes
    :rtype: list of nodes
    """
    seen = set(start_nodes)
    for deps, target in dependencies:
        if deps is None:
            seen.add(target)
    order = list(seen)
    old_dependencies = []
    while True:
        dependencies = [(deps, target) for deps, target in dependencies
                        if target not in seen]
        if not dependencies:
            return order
        if old_dependencies == dependencies:
            raise ValueError("no topological sort possible")

        for deps, target in dependencies:
            # test for sequences
            try:
                deps = iter(deps)
            # atomic object
            except TypeError:
                deps = [deps]
            if all(dep in seen for dep in deps):
                order.append(target)
                seen.add(target)
        # copy dependencies to check progress
        old_dependencies = list(dependencies)


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

    def __repr__(self):
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
                # XXX: maybe use logging? or handle exception in caller?
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


def dict2string(d, attribs):
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
    afile = file(filename, 'r')
    hasher = hashlib.sha1()

    buf = afile.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = afile.read(blocksize)
    afile.close()
    return hasher.hexdigest()
