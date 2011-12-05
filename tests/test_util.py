import unittest2

from penchy import util

class TopSortTest(unittest2.TestCase):
    def test_error(self):
        a,b = range(2)
        deps = [(a,b), (b,a)]
        with self.assertRaises(ValueError):
            util.topological_sort([], deps)

    def test_multi_deps(self):
        a,b,c,d = range(4)
        start = [a,b]
        deps = [([a,b], c),
                (c, d)]
        self.assertTrue(util.topological_sort(start, deps) in ([a,b,c,d],
                                                              [b,a,c,d]))
    def test_linear_deps(self):
        a,b,c,d = range(4)
        start = [a]
        deps = [(a,b),(b,c),(c,d)]
        self.assertListEqual(util.topological_sort(start, deps), range(4))
