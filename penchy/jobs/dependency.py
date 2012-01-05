"""
This module provides the parts to model and resolve dependencies in the flow of
execution.
"""

from penchy.util import topological_sort


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


def edgesort(edges):
    """
    Return the topological sorted elements of ``edges``.

    :param edges: Sequence of :class:`Edge`
    :returns: topological sorted :class:`PipelineElement`
    """
    starts = set(edge.source for edge in edges)
    deps = []
    edges = list(edges)
    while edges:
        target = edges[0].sink
        starts.discard(target)
        sources = [edge.source for edge in edges if edge.sink is target]
        deps.append((sources if sources else None, target))
        edges = [edge for edge in edges if edge.sink is not target]
    deps.extend((None, start) for start in starts)
    return topological_sort(deps)