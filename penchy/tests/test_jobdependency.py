from penchy.compat import unittest
from penchy.jobs.dependency import edgesort, build_keys, Edge
from penchy.tests.util import make_edge, MockPipelineElement


class EdgeSortTest(unittest.TestCase):

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


class BuildKeysTest(unittest.TestCase):
    def test_multi_sinks(self):
        edges = [make_edge(1, (('foo', 'bar'),
                               ('baz', 'bad'))),
                 make_edge(2, (('foz', 'bas'),
                               ('boz', 'bat')))]
        with self.assertRaises(AssertionError):
            build_keys(edges, False)

    def test_single_edge(self):
        edges = [make_edge(1, (('foo', 'bar'),
                               ('baz', 'bad')))]
        self.assertDictEqual(build_keys(edges, False),
                             {'bar' : 42,
                              'bad' : 42})

    def test_multi_edge(self):
        edges = [make_edge(1, (('foo', 'bar'),
                               ('baz', 'bad'))),
                 make_edge(1, (('foz', 'bas'),
                               ('boz', 'bat')))]
        self.assertDictEqual(build_keys(edges, False),
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

        self.assertDictEqual(build_keys(edges, False),
                             {'foo' : 42,
                              'baz' : 42,
                              'foz' : 42,
                              'boz' : 42})


class SugaredPipelineTest(unittest.TestCase):
    def setUp(self):
        self.elem1 = MockPipelineElement('a')
        self.elem2 = MockPipelineElement('b')
        self.elem3 = MockPipelineElement('c')
        self.elem4 = MockPipelineElement('d')

    def test_pipeline_building(self):
        pipe = self.elem1 >> self.elem2 >> self.elem3 >> self.elem4
        self.assertListEqual(pipe.edges, [Edge(self.elem1, self.elem2),
                                          Edge(self.elem2, self.elem3),
                                          Edge(self.elem3, self.elem4)])

    def test_edge_to_pipeline(self):
        e = Edge(self.elem1, self.elem2)
        pipe = e >> self.elem3 >> self.elem4
        self.assertListEqual(pipe.edges, [e,
                                          Edge(self.elem2, self.elem3),
                                          Edge(self.elem3, self.elem4)])

    def test_edge_edges(self):
        e = Edge(self.elem1, self.elem2)
        self.assertItemsEqual(e.edges, [e])

    def test_tuple_mapping(self):
        p = self.elem1 >> ('a', 'b') >> self.elem2
        e = Edge(self.elem1, self.elem2, [('a', 'b')])
        self.assertItemsEqual(e.edges, [e])

    def test_string_mapping(self):
        p = self.elem1 >> 'a' >> self.elem2
        e = Edge(self.elem1, self.elem2, [('a', 'a')])
        self.assertItemsEqual(e.edges, [e])

    def test_list_string_mapping(self):
        p = self.elem1 >> ['a', 'b'] >> self.elem2
        e = Edge(self.elem1, self.elem2, [('a', 'a'), ('b', 'b')])
        self.assertItemsEqual(e.edges, [e])
        p = self.elem1 >> [('a', 'a'), 'b'] >> self.elem2
        self.assertItemsEqual(e.edges, [e])

    def test_explicit_mapping(self):
        map_ = [('a', 'b')]
        pipe = self.elem1 >> map_ >> self.elem2
        e = Edge(self.elem1, self.elem2, map_)
        self.assertListEqual(pipe.edges, [e])

        pipe = e >> self.elem3
        self.assertListEqual(pipe.edges, [e,
                                          Edge(self.elem2, self.elem3)])
