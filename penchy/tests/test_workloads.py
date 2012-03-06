from penchy.compat import unittest
from penchy.jobs.workloads import Dacapo


class DacapoWorkloadTest(unittest.TestCase):
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
