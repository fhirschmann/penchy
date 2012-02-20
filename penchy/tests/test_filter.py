import itertools
import json
import os
from numpy import average, std
from numpy.random import random_integers, random_sample
from operator import attrgetter
from tempfile import NamedTemporaryFile

from penchy.compat import unittest, write
from penchy.jobs.job import Job
from penchy.jobs.filters import *
from penchy.jobs.typecheck import Types
from penchy.util import tempdir
from penchy.tests.util import get_json_data, make_system_composition, MockPipelineElement


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


class AggregateTest(unittest.TestCase):
    def setUp(self):
        self.results = {1: {'a': 42,
                            'b': 32},
                        2: {'b': 0,
                            'c': 21}}

    def test_implicit(self):
        f = Aggregate('a', 'b')
        f._run(results=self.results)
        self.assertEqual(f.out, {'a': 42, 'b': 32})

    def test_explicit(self):
        f = Aggregate((1, 'a'), (2, 'b'))
        f._run(results=self.results)
        self.assertEqual(f.out, {'a': 42, 'b': 0})

    def test_implicit_fail(self):
        f = Aggregate('a', 'd')
        with self.assertRaises(WrongInputError):
            f._run(results=self.results)

    def test_explicit_fail_column(self):
        f = Aggregate((1, 'a'), (2, 'd'))
        with self.assertRaises(WrongInputError):
            f._run(results=self.results)

    def test_explicit_fail_composition(self):
        f = Aggregate((1, 'a'), (3, 'c'))
        with self.assertRaises(WrongInputError):
            f._run(results=self.results)


class CondenseTest(unittest.TestCase):
    def setUp(self):
        self.results = {1: {'a': 42,
                            'b': 32},
                        2: {'b': 0,
                            'c': 21}}

    def test_implicit(self):
        f = Condense([('a', 'id1'), ('b', 'id2')], ('col1', 'col2'))
        f._run(results=self.results)
        self.assertEqual(f.out, {'col1': [42, 32], 'col2': ['id1', 'id2']})

    def test_explicit(self):
        f = Condense([(1, 'a', 'id1'), (2, 'b', 'id2')], ('col1', 'col2'))
        f._run(results=self.results)
        self.assertEqual(f.out, {'col1': [42, 0], 'col2': ['id1', 'id2']})

    def test_implicit_fail(self):
        f = Condense([('a', 'id1'), ('d', 'id2')], ('col1', 'col2'))
        with self.assertRaises(WrongInputError):
            f._run(results=self.results)

    def test_explicit_fail_column(self):
        f = Condense([(1, 'a', 'id1'), (2, 'd', 'id2')], ('col1', 'col2'))
        with self.assertRaises(WrongInputError):
            f._run(results=self.results)

    def test_explicit_fail_composition(self):
        f = Condense([(1, 'a', 'id1'), (3, 'c', 'id2')], ('col1', 'col2'))
        with self.assertRaises(WrongInputError):
            f._run(results=self.results)


class CondensingReceiveTest(unittest.TestCase):
    def setUp(self):
        environment = {'receive': lambda: self.results}
        self.kwargs = {':environment:' : environment}
        self.results = {1: {'a': 42,
                            'b': 32},
                        2: {'b': 0,
                            'c': 21}}

    def test_implicit(self):
        f = CondensingReceive([('a', 'id1'), ('b', 'id2')], ('col1', 'col2'))
        f._run(**self.kwargs)
        self.assertEqual(f.out, {'col1': [42, 32], 'col2': ['id1', 'id2']})

    def test_explicit(self):
        f = CondensingReceive([(1, 'a', 'id1'), (2, 'b', 'id2')], ('col1', 'col2'))
        f._run(**self.kwargs)
        self.assertEqual(f.out, {'col1': [42, 0], 'col2': ['id1', 'id2']})

    def test_implicit_fail(self):
        f = CondensingReceive([('a', 'id1'), ('d', 'id2')], ('col1', 'col2'))
        with self.assertRaises(WrongInputError):
            f._run(**self.kwargs)

    def test_explicit_fail_column(self):
        f = CondensingReceive([(1, 'a', 'id1'), (2, 'd', 'id2')], ('col1', 'col2'))
        with self.assertRaises(WrongInputError):
            f._run(**self.kwargs)

    def test_explicit_fail_composition(self):
        f = CondensingReceive([(1, 'a', 'id1'), (3, 'c', 'id2')], ('col1', 'col2'))
        with self.assertRaises(WrongInputError):
            f._run(**self.kwargs)


class AggregatingReceiveTest(unittest.TestCase):
    def setUp(self):
        environment = {'receive': lambda: self.results}
        self.kwargs = {':environment:' : environment}
        self.results = {1: {'a': 42,
                            'b': 32},
                        2: {'b': 0,
                            'c': 21}}

    def test_implicit(self):
        f = AggregatingReceive('a', 'b')
        f._run(**self.kwargs)
        self.assertEqual(f.out, {'a': 42, 'b': 32})

    def test_explicit(self):
        f = AggregatingReceive((1, 'a'), (2, 'b'))
        f._run(**self.kwargs)
        self.assertEqual(f.out, {'a': 42, 'b': 0})

    def test_implicit_fail(self):
        f = AggregatingReceive('a', 'd')
        with self.assertRaises(WrongInputError):
            f._run(**self.kwargs)

    def test_explicit_fail_column(self):
        f = AggregatingReceive((1, 'a'), (2, 'd'))
        with self.assertRaises(WrongInputError):
            f._run(**self.kwargs)

    def test_explicit_fail_composition(self):
        f = AggregatingReceive((1, 'a'), (3, 'c'))
        with self.assertRaises(WrongInputError):
            f._run(**self.kwargs)


class SendTest(unittest.TestCase):
    def test_send(self):
        a = [1]
        f = Send()
        f._run(payload=42,
               **{':environment:' : {'send' : lambda data: a.__setitem__(0, data)}})
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
        b.run(filename=path, **{':environment:' : {}})

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
        b.run(filename=path, **{':environment:' : {'current_composition' : comp}})

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
            b.run(filename=path, **{':environment:' : {}})


class SaveTest(unittest.TestCase):
    def test_save_relative(self):
        s = "'tis a test string"
        save_file = 'penchy-save-test'
        comp = make_system_composition()
        comp.node_setting.path = '/tmp'
        save_path = os.path.join(comp.node_setting.path, save_file)

        save = Save(save_file)
        save.run(data=s, **{':environment:' : {'current_composition': comp}})
        with open(save_path) as f:
            self.assertEqual(f.read(), s)

        os.remove(save_path)

    def test_save_absolute(self):
        s = "'tis a test string"
        save_path = '/tmp/penchy-save-test'
        save = Save(save_path)
        save.run(data=s, **{':environment:' : {}})
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


class ServerFlowSystemFilterTest(unittest.TestCase):
    def setUp(self):
        self.env = {
            'job' : 'no file',
            'current_composition' : None
        }

    def test_dump(self):
        numbers = [23, 42]
        strings = ['a', 'b', 'c']
        d = Dump()
        d._run(numbers=numbers, strings=strings, **{':environment:' : self.env})

        dump = json.loads(d.out['dump'])
        self.assertIn('job', dump['system'])
        self.assertNotIn('jvm', dump['system'])
        self.assertIn('numbers', dump['data'])
        self.assertIn('strings', dump['data'])
        self.assertItemsEqual(numbers, dump['data']['numbers'])
        self.assertItemsEqual(strings, dump['data']['strings'])

    def test_save_and_backup(self):
        data = "'tis the end"
        with tempdir(delete=True):
            s = Save('save')
            s._run(data=data, **{':environment:' : self.env})
            b = BackupFile('backup')
            b._run(filename='save', **{':environment:' : self.env})
            with open('save') as f:
                self.assertEqual(f.read(), data)
            with open('backup') as f:
                self.assertEqual(f.read(), data)


class StandardDeviationTest(unittest.TestCase):
    def test_against_numpy_integes(self):
        rnd = random_integers(-20, 20, 50)
        f = StandardDeviation(ddof=1)
        f._run(values=rnd)
        self.assertAlmostEqual(f.out['standard_deviation'], std(rnd, ddof=1))

    def test_against_numpy_floats(self):
        rnd = random_sample(20)
        f = StandardDeviation(ddof=1)
        f._run(values=rnd)
        self.assertAlmostEqual(f.out['standard_deviation'], std(rnd, ddof=1))
