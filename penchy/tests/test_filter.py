import itertools
import os
from operator import attrgetter
from tempfile import NamedTemporaryFile

from penchy.compat import unittest, write
from penchy.jobs.typecheck import Types, TypeCheckError
from penchy.jobs.filters import *

from penchy.tests.util import get_json_data, make_system_composition


class DacapoHarnessTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        d = get_json_data('DacapoHarnessFilter')
        cls.multiple_iterations = d['multiple_iterations']
        cls.single_iterations = d['single_iterations']
        cls.failed_single = d['failed_single']
        cls.wrong_input = d['wrong_input']

    def setUp(self):
        super(DacapoHarnessTest, self).setUp()
        self.d = DacapoHarness()

        self.mi = write_to_tempfiles(DacapoHarnessTest.multiple_iterations)
        self.si = write_to_tempfiles(DacapoHarnessTest.single_iterations)
        self.failed = write_to_tempfiles(DacapoHarnessTest.failed_single)
        self.wrong_input = write_to_tempfiles(DacapoHarnessTest.wrong_input)

    def tearDown(self):
        for f in itertools.chain(self.mi, self.si, self.failed,
                                 self.wrong_input):
            f.close()

    def test_multi_iteration_path(self):
        invocations = len(self.mi)
        exit_codes = [0] * invocations
        stderr = map(attrgetter('name'), self.mi)
        self.d.run(exit_code=exit_codes, stderr=stderr)

        self._assert_correct_out(invocations)

    def test_single_iteration_path(self):
        invocations = len(self.si)
        exit_codes = [0] * invocations
        stderr = map(attrgetter('name'), self.si)
        self.d.run(exit_code=exit_codes, stderr=stderr)
        self._assert_correct_out(invocations)

    def test_failed(self):
        invocations = len(self.failed)
        exit_codes = [0] * invocations
        stderr = map(attrgetter('name'), self.failed)
        self.d.run(exit_code=exit_codes, stderr=stderr)
        self.assertListEqual(self.d.out['failures'], [1] * invocations)

    def test_wrong_input(self):
        stderr = map(attrgetter('name'), self.wrong_input)
        for e in stderr:
            with self.assertRaises(WrongInputError):
                self.d.run(exit_code=[0], stderr=[e])

    def _assert_correct_out(self, invocations):
        self.assertSetEqual(set(self.d.out), self.d._output_names)
        self.assertEqual(len(self.d.out['failures']), invocations)
        self.assertEqual(len(self.d.out['times']), invocations)
        self.assertEqual(len(self.d.out['valid']), invocations)


class HProfCpuTimesTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        h = get_json_data('HProfCpuTimesFilter')
        cls.single_iterations = h['single_iterations']
        cls.wrong_input = h['wrong_input']

    def setUp(self):
        super(HProfCpuTimesTest, self).setUp()
        self.h = HProfCpuTimes()

        self.si = write_to_tempfiles(HProfCpuTimesTest.single_iterations)
        self.wrong_input = write_to_tempfiles(HProfCpuTimesTest.wrong_input)

    def tearDown(self):
        for f in itertools.chain(self.si, self.wrong_input):
            f.close()

    def test_single_iteration_path(self):
        invocations = len(self.si)
        hprof_file = map(attrgetter('name'), self.si)
        self.h.run(hprof=hprof_file)
        self._assert_correct_out(invocations)

    def test_wrong_input(self):
        hprof_files = map(attrgetter('name'), self.wrong_input)
        for hprof_file in hprof_files:
            with self.assertRaises(WrongInputError):
                self.h.run(hprof=[hprof_file])

    def _assert_correct_out(self, invocations):
        self.assertSetEqual(set(self.h.out), self.h._output_names)
        for k in self.h.out.keys():
            self.assertEqual(len(self.h.out[k]), invocations)


def write_to_tempfiles(data):
    files = []
    for d in data:
        # itentionally not closing, do in tearDown
        f = NamedTemporaryFile(prefix='penchy')
        write(f, d)
        f.seek(0)
        files.append(f)

    return files


class SendTest(unittest.TestCase):
    def test_send(self):
        a = [1]
        f = Send()
        f._run(environment={'send' : lambda data: a.__setitem__(0, data)},
               payload=42)
        self.assertEqual(a, [{'payload': 42}])


class StatisticRuntimeEvaluationTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        t = get_json_data('StatisticRuntimeEvaluationFilter')
        cls.times = t['times']
        cls.expected = t['expected']

    def test_statistics(self):
        f = StatisticRuntimeEvaluation()
        keys = ['averages', 'maximals', 'minimals',
                'positive_deviations', 'negative_deviations']
        for times, results in zip(StatisticRuntimeEvaluationTest.times,
                                 StatisticRuntimeEvaluationTest.expected):
            # output is correctly cleaned up?
            self.assertDictEqual(f.out, {})
            f._run(times=times)
            # contains the right keys?
            self.assertItemsEqual(f.out.keys(), keys)
            for key in keys:
                for actual, expected in zip(f.out[key], results[key]):
                    self.assertAlmostEqual(actual, expected)
            f.reset()


class EvaluationTest(unittest.TestCase):

    def test_default_input(self):
        e = Evaluation(lambda input: {'result' : input})
        e._run(input=42)
        self.assertDictEqual(e.out, {'result' : 42})

    def test_missing_default_input(self):
        e = Evaluation(lambda x: None)
        with self.assertRaises(ValueError):
            e._run()

    def test_missing_input(self):
        e = Evaluation(lambda x: x, Types(('value', int)), Types(('value', int)))
        with self.assertRaises(ValueError):
            e._run()


class BackupTest(unittest.TestCase):
    def test_copy(self):
        s = "'tis a test string"
        with NamedTemporaryFile(delete=False) as f:
            path = f.name
            write(f, s)
        self.assertTrue(os.path.exists(path))
        backup_path = '/tmp/penchy-backup-test'
        b = BackupFile(backup_path)
        b.run(environment={}, filename=path)

        # did backup?
        with open(backup_path) as f:
            self.assertEqual(f.read(), s)

        # did not modify backuped file?
        with open(path) as f:
            self.assertEqual(f.read(), s)

        os.remove(path)
        os.remove(backup_path)

    def test_relative_copy(self):
        s = "'tis a test string"
        comp = make_system_composition()
        comp.node_setting.path = '/tmp'

        with NamedTemporaryFile(delete=False) as f:
            path = f.name
            write(f, s)
        self.assertTrue(os.path.exists(path))
        backup_file = 'penchy-backup-test'
        backup_path = os.path.join(comp.node_setting.path, backup_file)
        b = BackupFile(backup_file)
        b.run(environment={'current_composition' : comp}, filename=path)

        # did backup?
        with open(backup_path) as f:
            self.assertEqual(f.read(), s)

        # did not modify backuped file?
        with open(path) as f:
            self.assertEqual(f.read(), s)

        os.remove(path)
        os.remove(os.path.join(comp.node_setting.path, backup_path))

    def test_not_existing_path(self):
        # create unique not existing path
        with NamedTemporaryFile() as f:
            path = f.name

        b = BackupFile('/tmp/penchy-backup-test')
        with self.assertRaises(WrongInputError):
            b.run(environment={}, filename=path)


class SaveTest(unittest.TestCase):
    def test_save_relative(self):
        s = "'tis a test string"
        save_file = 'penchy-save-test'
        comp = make_system_composition()
        comp.node_setting.path = '/tmp'
        save_path = os.path.join(comp.node_setting.path, save_file)

        save = Save(save_file)
        save.run(environment={'current_composition': comp}, data=s)
        with open(save_path) as f:
            self.assertEqual(f.read(), s)

        os.remove(save_path)

    def test_save_absolute(self):
        s = "'tis a test string"
        save_path = '/tmp/penchy-save-test'
        save = Save(save_path)
        save.run(environment={}, data=s)
        with open(save_path) as f:
            self.assertEqual(f.read(), s)

        os.remove(save_path)


class ReadTest(unittest.TestCase):
    def test_read(self):
        s = "'tis a test string"
        with NamedTemporaryFile() as f:
            write(f, s)
            f.flush()

            r = Read()
            r.run(paths=[f.name])
            self.assertListEqual(r.out['data'], [s])
