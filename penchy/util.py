"""
This module provides miscellaneous utilities.
"""

from collections import namedtuple


NodeConfig = namedtuple('NodeConfig', ['host', 'ssh_port', 'username', 'path'])


def topological_sort(start_nodes, dependencies):
    """
    Return a topologically sorted list of :param:`start_nodes` and
    :param:`dependencies`.

    Nodes are checked on identity, not equality.

    Raises a ValueError if no topological sort is possible.

    :param start_nodes: sequence of nodes of graph with no incoming edges
    :param dependencies: sequence of dependency edges; ([dependencies], target),
                         dependencies may be of any sequence or be atomic, if
                         there is no dependency it must be ``None``
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
        dependencies = [(deps, target) for deps, target in dependencies if target not in seen]
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


class memoized(object):
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
