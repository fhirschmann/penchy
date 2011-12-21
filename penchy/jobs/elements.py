"""
This module provides the foundation of job elements.
"""


class PipelineElement(object):
    pass


class NotRunnable(object):
    pass


class Filter(PipelineElement):
    pass


class Tool(PipelineElement, NotRunnable):
    pass


class Workload(PipelineElement, NotRunnable):
    pass
