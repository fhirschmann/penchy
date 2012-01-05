"""
This module provides the parts to model and resolve dependencies in the flow of
execution.
"""


class Edge(object):
    """
    This class represents edges in the dependency graph.
    """

    def __init__(self, source, sink=None, map=None):
        """
        :param source: source of data
        :param sink: sink of data
        :param map: sequence of name pairs that map source exits to sink
                    entrances
        """
        self.source = source
        self.sink = sink
        self.map = map
