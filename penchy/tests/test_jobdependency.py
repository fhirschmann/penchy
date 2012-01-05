import unittest2

from penchy.jobs.dependency import Edge, edgesort


class EdgeSortTest(unittest2.TestCase):

    def test_circ(self):
        edges = [Edge(1, 2), Edge(2, 1)]
        with self.assertRaises(ValueError):
            edgesort(edges)

    def test_linear(self):
        edges = [Edge(0, 1), Edge(1, 2)]
        self.assertListEqual(edgesort(edges), range(3))

    def test_multi_deps(self):
        edges = [Edge(0, 1), Edge(2, 1),
                 Edge(0, 2)]
        self.assertListEqual(edgesort(edges), [0,2,1])