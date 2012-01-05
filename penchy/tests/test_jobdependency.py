import unittest2

from penchy.jobs.dependency import Edge, edgesort


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
        self.assertTrue(edge_order in (edges[::-1], [edges[2], edges[0], edges[1]]))