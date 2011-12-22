"""
This module provides the foundation of job elements.
"""


class PipelineElement(object):
    """
    This class is the base class for all objects participating in the
    transformation pipeline.
    """
    def __init__(self):
        self.out = {}

        self.prehooks = []
        self.posthooks = []


class NotRunnable(object):
    """
    This represents a pipeline element that can't be run.
    """
    def run(self):
        # TODO: Add logging?
        raise ValueError("{0} can't be run!".format(self.__class__.__name__))


class Filter(PipelineElement):
    pass


class Tool(NotRunnable, PipelineElement):
    """
    This represents a Tool of the pipeline
    """
    @property
    def arguments(self):
        """
        The arguments the jvm has to include to use the tool.
        """
        raise NotImplementedError("Tools must implement this")


class Workload(NotRunnable, PipelineElement):
    exports = set(('stdout', 'stderr', 'exit code'))
    @property
    def arguments(self):
        """
        The arguments the jvm has to include to execute the workloads.
        """
        raise NotImplementedError("Workloads must implement this")