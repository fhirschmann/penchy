from penchy.compat import unittest
from penchy.jobs.workloads import Dacapo, ScalaBench


class DacapoWorkloadTest(unittest.TestCase):
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

    def test_argument_check(self):
        w = Dacapo('fop', 1, '--foo')
        self.assertFalse(w.check())

        w = Dacapo('fop', 1, '-s')
        self.assertTrue(w.check())


class ScalabenchWorkloadTest(unittest.TestCase):
    def test_invalid_benchmark(self):
        w = ScalaBench('baz')
        self.assertFalse(w.check())

    def test_correct_benchmark(self):
        w = ScalaBench('scalac')
        self.assertTrue(w.check())
