import unittest2

from penchy.jobs.dependency import Edge, edgesort, build_keys
from penchy.tests.util import make_edge


class EdgeSortTest(unittest2.TestCase):

    def test_circ(self):
        starts = []
        edges = [Edge(1, 2), Edge(2, 1)]
        with self.assertRaises(ValueError):
            edgesort(starts, edges)

    def test_linear(self):
        starts = [0]
        edges = [Edge(0, 1), Edge(1, 2)]
        self.assertEqual(edgesort(starts, edges),
                         ([1, 2], edges))

    def test_multi_deps(self):
        starts = [0]
        edges = [Edge(0, 1), Edge(2, 1),
                 Edge(0, 2)]
        order, edge_order = edgesort(starts, edges)
        self.assertEqual(order, [2, 1])
        self.assertIn(edge_order, (edges[::-1],
                                   [edges[2], edges[0], edges[1]]))


class BuildKeysTest(unittest2.TestCase):
    def test_multi_sinks(self):
        edges = [make_edge(1, (('foo', 'bar'),
                               ('baz', 'bad'))),
                 make_edge(2, (('foz', 'bas'),
                               ('boz', 'bat')))]
        with self.assertRaises(AssertionError):
            build_keys(edges)

    def test_single_edge(self):
        edges = [make_edge(1, (('foo', 'bar'),
                               ('baz', 'bad')))]
        self.assertDictEqual(build_keys(edges),
                             {'bar' : 42,
                              'bad' : 42})

    def test_multi_edge(self):
        edges = [make_edge(1, (('foo', 'bar'),
                               ('baz', 'bad'))),
                 make_edge(1, (('foz', 'bas'),
                               ('boz', 'bat')))]
        self.assertDictEqual(build_keys(edges),
                             {'bar' : 42,
                              'bad' : 42,
                              'bas' : 42,
                              'bat' : 42})

    def test_complete_copy(self):
        edges = [make_edge(1, (('foo', 'bar'),
                               ('baz', 'bad'))),
                 make_edge(1, (('foz', 'bas'),
                               ('boz', 'bat')))]
        # set edges to None for complete copy
        for edge in edges:
            edge.map_ = None

        self.assertDictEqual(build_keys(edges),
                             {'foo' : 42,
                              'baz' : 42,
                              'foz' : 42,
                              'boz' : 42})
