"""
This module provides the foundation of job elements.

 .. moduleauthor:: Michael Markert <markert.michael@googlemail.com>

 :copyright: PenchY Developers 2011-2012, see AUTHORS
 :license: MIT License, see LICENSE
"""
import logging
from collections import defaultdict

from penchy.compat import str, unicode, path
from penchy.jobs.dependency import Pipeline
from penchy.jobs.typecheck import Types


log = logging.getLogger(__name__)


class PipelineElement(object):
    """
    This class is the base class for all objects participating in the
    transformation pipeline.

    A PipelineElement must have the following attributes:

    - ``out``, a dictionary that maps logical names for output to actual.
    - ``inputs`` a :class:`~penchy.jobs.typecheck.Types` that describes the
                 necessary inputs and their types for the element
    - ``outputs`` a :class:`~penchy.jobs.typecheck.Types` that describes the
                  output with a logical name and its types

    A PipelineElement must have the following methods:

    - ``_run(**kwargs)``, to run the element on kwargs, kwargs has to have the
                          types that ``input`` describes

    A :class:`PipelineElement` must call ``PipelineElement.__init__`` on its
    initialization.
    """
    DEPENDENCIES = set()
    inputs = Types()
    outputs = Types()

    def __init__(self):
        self.reset()

        self.hooks = []

    def run(self, **kwargs):
        """
        Run element with hooks.
        """
        self.inputs.check_input(kwargs)
        for hook in self.hooks:
            hook.setup()

        self._run(**kwargs)

        for hook in self.hooks:
            hook.teardown()

    def reset(self):
        """
        Reset state of element.

        Resets
          - element.out
        """
        self.out = defaultdict(list)

    def __rshift__(self, other):
        p = Pipeline(self)
        return p >> other

    def _run(self, **kwargs):  # pragma: no cover
        """
        Run the actual Element on the arguments.
        """
        raise NotImplementedError("PipelineElements must implement this")

    @property
    def _output_names(self):
        """
        Return the set of output names

        :returns: the output names
        :rtype: set
        """
        return self.outputs.names

    def __repr__(self):
        return self.__class__.__name__


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


class SystemFilter(Filter):
    """
    This represents a Filter of the pipeline that needs access to the system.

    Additionally to :class:`Filter` it receives additionally an input named
    ``:environment:`` that describes the execution environment.
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
    outputs = Types(('stdout', list, path),
                    ('stderr', list, path),
                    ('exit_code', list, int))

    def __init__(self, timeout=0):
        """
        :param timeout: timeout (in seconds) after which this workload should
                        be terminated
        :type timeout: int
        """
        super(Workload, self).__init__()
        self.timeout = timeout

    @property
    def arguments(self):  # pragma: no cover
        """
        The arguments the jvm has to include to execute the workloads.
        """
        raise NotImplementedError("Workloads must implement this")
