"""
This module provides the parts to model and resolve dependencies in the flow of
execution.
"""

class Edge(object):
    """
    This class represents edges in the dependency graph.

    """
    def __init__(self, from_, output, to=None, input_=None):
        """
        :param from_:
        :param output:
        :param to:
        :param input_:
        """
        pass