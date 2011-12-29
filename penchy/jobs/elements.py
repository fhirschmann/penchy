"""
This module provides the foundation of job elements.
"""

from collections import defaultdict


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

    def __init__(self):
        self.out = defaultdict(list)

        self.prehooks = []
        self.posthooks = []

    def run(self, *args, **kwargs):
        """
        Run element with hooks.
        """
        for hook in self.prehooks:
            hook()

        self._run(*args, **kwargs)

        for hook in self.posthooks:
            hook()

    def _run(self, *args, **kwargs):
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
    - `exit code`, the exitcode
    """
    exports = set(('stdout', 'stderr', 'exit code'))

    @property
    def arguments(self):
        """
        The arguments the jvm has to include to execute the workloads.
        """
        raise NotImplementedError("Workloads must implement this")
