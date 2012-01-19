"""
This module provides the foundation of job elements.
"""

import logging
from collections import defaultdict
from itertools import chain

log = logging.getLogger(__name__)


class PipelineElement(object):
    """
    This class is the base class for all objects participating in the
    transformation pipeline.

    A PipelineElement must have the following attributes:

    - `out`, a dictionary that maps logical names for output to actual.
    - `inputs`, a list of tuples that describe the name and type of the inputs
                for ``run`` and have the form
    - ``(name, type, *types)`` that is: a argument with the name ``name``
                               and type ``type`` and possible subtypes ``types``

    - ``outputs`, a list of tuples that describe the logical name of an output
                 and its type it is built alike ``inputs`` for all output of the
                 element

    A PipelineElement must have the following methods:

    - ``_run(**kwargs)``, to run the element on kwargs, kwargs has to have the
                          types that ``input`` describes
    - `check`, to check the element configuration for plausibility.

    A PipelineElement must call PipelineElement.__init__ on its initialization.
    """
    DEPENDENCIES = set()
    inputs = []
    outputs = []

    def __init__(self):
        self.reset()

        self.prehooks = []
        self.posthooks = []

    def run(self, **kwargs):
        """
        Run element with hooks.
        """
        _check_kwargs(self, kwargs)
        for hook in self.prehooks:
            hook()

        self._run(**kwargs)

        for hook in self.posthooks:
            hook()

    def reset(self):
        """
        Reset state of element.

        Resets
          - element.out
        """
        self.out = defaultdict(list)

    def _run(self, **kwargs):  # pragma: no cover
        """
        Run the actual Element on the arguments.
        """
        raise NotImplementedError("PipelineElements must implement this")

    def check(self):  # pragma: no cover
        """
        Check element for plausibility.
        """
        raise NotImplementedError("PipelineElements must implement this")

    @property
    def _output_names(self):
        """
        Return the set of output names

        :returns: the output names
        :rtype: set
        """
        return set(t[0] for t in self.outputs)


class NotRunnable(object):
    """
    This represents a pipeline element that can't be run.
    """

    def run(self):
        msg = "{0} can't be run!".format(self.__class__.__name__)
        log.error(msg)
        raise ValueError(msg)


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
    def arguments(self):  # pragma: no cover
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
    outputs = [('stdout', list, str),
               ('stderr', list, str),
               ('exit_code', list, int)]

    @property
    def arguments(self):  # pragma: no cover
        """
        The arguments the jvm has to include to execute the workloads.
        """
        raise NotImplementedError("Workloads must implement this")


def _check_kwargs(instance, kwargs):
    """
    Check if ``kwargs`` satisfies the restrictions of ``instance.inputs``.
    That is:
        - All required names are found and
        - have the right type (and subtype)

    Raises a :class:`ValueError` if a name is missing or has the wrong type.
    Raises a :class:`AssertError` if ``instance.inputs`` has a wrong format.

    Logs warnings if there are more arguments than the required.

    :param instance: :PipelineElement: for which to check kwargs
    :type instance: PipelineElement
    :param kwargs: arguments for _run of ``instance``
    :type kwargs: dict
    :returns: count of unused inputs
    :rtype: int
    """

    for t in instance.inputs:
        msg = 'Malformed type description: '
        '{0} is not of form (str, *type) [str, *type]'.format(t)
        if not len(t) > 1:
            raise AssertionError(msg)
        if not isinstance(t, (tuple, list)) or not isinstance(t[0], str):
            raise AssertionError(msg)
        if any(not isinstance(type_, type) for type_ in t[1:]):
            raise AssertionError(msg)

    for t in instance.inputs:
        name, types = t[0], t[1:]
        if name not in kwargs:
            raise ValueError('Argument {0} is missing'.format(name))

        value = [kwargs[name]]  # pack start value in list to reuse loop
        for type_ in types:
            if any(not isinstance(v, type_) for v in value):
                raise ValueError('Argument {0} is not of type {1}'.format(name,
                                                                          types))
            if len(value) > 1:
                value = chain(subvalue for subvalue in value)
            else:
                value = value[0]

    unused_inputs = 0
    for name in set(kwargs) - set(t[0] for t in instance.inputs):
        unused_inputs += 1
        log.warn("Unknown input {0}".format(name))

    return unused_inputs
