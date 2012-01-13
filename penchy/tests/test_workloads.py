import unittest2

from penchy.jobs.workloads import Dacapo, ScalaBench


class DacapoWorkloadTest(unittest2.TestCase):
    def test_invalid_benchmark(self):
        w = Dacapo('scalac')
        self.assertFalse(w.check())

    def test_correct_benchmark(self):
        w = Dacapo('batik')
        self.assertTrue(w.check())

    def test_arguments(self):
        w = Dacapo('batik')
        self.assertListEqual(w.arguments,
                             'Harness -n 1 batik'.split())
        w = Dacapo('fop', 10, '-s small')
        self.assertListEqual(w.arguments,
                             'Harness -n 10 -s small fop'.split())
        w = Dacapo('jython', args='--callback foo')
        self.assertListEqual(w.arguments,
                             'Harness -n 1 --callback foo jython'.split())


class ScalabenchWorkloadTest(unittest2.TestCase):
    def test_invalid_benchmark(self):
        w = ScalaBench('baz')
        self.assertFalse(w.check())

    def test_correct_benchmark(self):
        w = ScalaBench('scalac')
        self.assertTrue(w.check())
