import unittest2

from penchy import util


class TopSortTest(unittest2.TestCase):

    def test_circle(self):
        a, b = range(2)
        deps = [(a, b), (b, a)]
        with self.assertRaises(ValueError):
            util.topological_sort(deps)

    def test_multi_deps(self):
        a, b, c, d = range(4)
        start = [a, b]
        deps = [(None, a),
                (None, b),
                ([a, b], c),
                (c, d)]
        self.assertTrue(util.topological_sort(deps) in ([a, b, c, d],
                                                       [b, a, c, d]))

    def test_linear_deps(self):
        a, b, c, d = range(4)
        deps = [(None, a), (a, b), (b, c), (c, d)]
        self.assertListEqual(util.topological_sort(deps), range(4))


class ClasspathTest(unittest2.TestCase):

    def test_valid_options(self):
        expected = 'foo:bar:baz'
        options = ['-cp', expected]
        self.assertEquals(util.extract_classpath(options), expected)
        expected = 'foo:bar:baz'
        options = ['-classpath', expected]
        self.assertEquals(util.extract_classpath(options), expected)

    def test_multiple_classpaths(self):
        expected = 'foo:bar:baz'
        options = ['-cp', 'com:org:de', '-cp', expected]
        self.assertEquals(util.extract_classpath(options), expected)

    def test_only_option(self):
        options = ['-cp']
        self.assertEquals(util.extract_classpath(options), '')
