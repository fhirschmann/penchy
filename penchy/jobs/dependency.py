"""
This module provides the parts to model and resolve dependencies in the flow of
execution.
"""
class Edge(object):
    """
    This class represents edges in the dependency graph.
    """

    def __init__(self, source, sink=None, map_=None):
        """
        :param source: source of data
        :param sink: sink of data
        :param map: sequence of name pairs that map source exits to sink
                    entrances
        """
        self.source = source
        self.sink = sink
        self.map_ = map_


def edgesort(starts, edges):
    """
    Return the topological sorted elements of ``edges``.

    ``starts`` won't be included.

    :param starts: Sequence of :class:`PipelineElement` that have no deps
    :param edges: Sequence of :class:`Edge`
    :returns: pair of topological sorted :class:`PipelineElement` and
              sorted list of corresponding :class:`Edge`
    """
    resolved = set(starts)
    order = []
    edge_order = []
    edges = list(edges)
    old_edges = []
    while True:
        if not edges:
            return order, edge_order

        if edges == old_edges:
            raise ValueError("no topological sort possible")

        for target in set(edge.sink for edge in edges):
            current = [edge for edge in edges if edge.sink is target]
            if all(edge.source in resolved for edge in current):
                resolved.add(target)
                order.append(target)
                edge_order.extend(current)

        old_edges = list(edges)
        edges = [edge for edge in edges if edge.sink not in resolved]