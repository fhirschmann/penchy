"""
This module provides the foundation of job elements.
"""

import logging
from collections import defaultdict

log = logging.getLogger('elements')


class PipelineElement(object):
    """
    This class is the base class for all objects participating in the
    transformation pipeline.

    A PipelineElement must have the following attributes:

    - `out`, a dictionary that maps logical names for output to actual.
    - `exports`, a set of names that describes which logical names are valid
                 for the element.

    A PipelineElement must have the following methods:

    - `_run`, to run the element on the parameters.
    - `check`, to check the element configuration for plausibility.
    """
    DEPENDENCIES = set()

    def __init__(self):
        self.out = defaultdict(list)

        self.prehooks = []
        self.posthooks = []

    def run(self, **kwargs):
        """
        Run element with hooks.
        """
        _check_kwargs(self, kwargs)
        for hook in self.prehooks:
            hook()

        self._run(*args, **kwargs)

        for hook in self.posthooks:
            hook()

    def _run(self, **kwargs):
        """
        Run the actual Element on the arguments.
        """
        raise NotImplementedError("PipelineElements must implement this")

    def check(self):
        """
        Check element for plausibility.
        """
        raise NotImplementedError("PipelineElements must implement this")


class NotRunnable(object):
    """
    This represents a pipeline element that can't be run.
    """

    def run(self):
        # TODO: Add logging?
        raise ValueError("{0} can't be run!".format(self.__class__.__name__))


class Filter(PipelineElement):
    """
    This represents a Filter of the pipeline.

    A Filter receives and processes data.
    """
    pass


class Tool(NotRunnable, PipelineElement):
    """
    This represents a Tool of the pipeline.

    A Tool modifies the JVM on which it runs, so that data about that run is
    gathered. Hprof, for example, is a Tool.
    """

    @property
    def arguments(self):
        """
        The arguments the jvm has to include to use the tool.
        """
        raise NotImplementedError("Tools must implement this")


class Workload(NotRunnable, PipelineElement):
    """
    This represents a Workload of the pipeline.

    A Workload is code that the JVM should execute. Typically it provides the
    classpath (via its dependencies) and the complete commandline arguments to
    call it correctly. The DaCapo benchmark suite is a workload (with a
    benchmark specified).

    A workload has at least three exported values:

    - `stdout`, the path to the file that contains the output on stdout
    - `stderr`, the path to the file that contains the output on stderr
    - `exit_code`, the exitcode as int
    """
    exports = set(('stdout', 'stderr', 'exit_code'))

    @property
    def arguments(self):
        """
        The arguments the jvm has to include to execute the workloads.
        """
        raise NotImplementedError("Workloads must implement this")


def _check_kwargs(instance, kwargs):
    """
    Check that all names are in the keyword arguments with the corresponding
    type.

    Raises a :class:`ValueError` if a name is missing or has the wrong type.
    Logs warnings if there are more arguments than the required.

    :param name_types: triple of string names, type and subtype.
    :type name_types: tuple
    """

    for t in instance.inputs:
        length = len(t)
        if length == 2:
            t = (t[0], t[1], object)

        if not all(isinstance(x, y) for x, y in zip(t, (str, type, type))):
            if length == 2:
                msg = 'Malformed type description: {0} is not of form '
                '(str, type, type)'.format(t)
            elif length == 3:
                msg = 'Malformed type description: {0} is not of form'
                '(str, type, type)'.format(t)

            else:
                msg = 'Malformed type description: '
                '{0} is not of form (str, type, type) or (str, type)'.format(t)

            raise AssertionError(msg)

    for t in instance.inputs:
        if len(t) == 3:
            name, type_, subtype = t
        else:
            name, type_ = t
            subtype = None
        if name in kwargs:
            if isinstance(kwargs[name], type_):
                if subtype is not None and any(not isinstance(e, subtype)
                                               for e in kwargs[name]):
                    raise ValueError('Argument {0} has no uniform '
                                     'subtype {1}'.format(name, subtype))
            else:
                raise ValueError('Argument {0} is {1} instead of '
                                 'expected {2}'.format(name,
                                                       type(kwargs[name]),
                                                       type_))
        else:
            raise ValueError('Argument {0} is missing'.format(name))

    for name in set(kwargs) - set(t[0] in instance.inputs):
        log.warn("Unknown input {0}".format(name))
