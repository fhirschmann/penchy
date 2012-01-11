from operator import attrgetter
from tempfile import NamedTemporaryFile

import unittest2

from penchy.tests.util import get_json_data
from penchy.jobs.filters import DacapoHarness


class DacapoHarnessTest(unittest2.TestCase):

    @classmethod
    def setUpClass(cls):
        d = get_json_data('DacapoHarnessFilter')
        cls.multiple_iterations = d['multiple_iterations']
        cls.single_iterations = d['single_iterations']

    def setUp(self):
        super(DacapoHarnessTest, self).setUp()
        self.d = DacapoHarness()
        self.mi_files = []
        self.si_files = []

        for data in DacapoHarnessTest.multiple_iterations:
            f = NamedTemporaryFile(prefix='penchy')
            f.write(data)
            f.seek(0)
            self.mi_files.append(f)

        for data in DacapoHarnessTest.single_iterations:
            f = NamedTemporaryFile(prefix='penchy')
            f.write(data)
            f.seek(0)
            self.si_files.append(f)

    def tearDown(self):
        for f in self.mi_files + self.si_files:
            f.close()

    def test_multi_iteration_path(self):
        invocations = len(self.mi_files)
        exit_codes = [0] * invocations
        stderr = map(attrgetter('name'), self.mi_files)
        self.d._run(exit_code=exit_codes, stderr=stderr)

        self._assert_correct_out(invocations)

    def test_single_iteration_path(self):
        invocations = len(self.si_files)
        exit_codes = [0] * invocations
        stderr = map(attrgetter('name'), self.si_files)
        self.d._run(exit_code=exit_codes, stderr=stderr)
        self._assert_correct_out(invocations)

    def _assert_correct_out(self, invocations):
        self.assertSetEqual(set(self.d.out), self.d._output_names)
        self.assertEqual(len(self.d.out['failures']), invocations)
        self.assertEqual(len(self.d.out['times']), invocations)
        self.assertEqual(len(self.d.out['valid']), invocations)
