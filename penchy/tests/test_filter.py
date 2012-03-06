import itertools
import json
import os
from numpy import average, std
from numpy.random import random_integers, random_sample
from tempfile import NamedTemporaryFile

from penchy.compat import unittest, write
from penchy.jobs.filters import *
from penchy.jobs.typecheck import Types
from penchy.util import tempdir
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
        stderr = [i.name for i in self.mi]
        self.d.run(exit_code=exit_codes, stderr=stderr)

        self._assert_correct_out(invocations)

    def test_single_iteration_path(self):
        invocations = len(self.si)
        exit_codes = [0] * invocations
        stderr = [i.name for i in self.si]
        self.d.run(exit_code=exit_codes, stderr=stderr)
        self._assert_correct_out(invocations)

    def test_failed(self):
        invocations = len(self.failed)
        exit_codes = [0] * invocations
        stderr = [i.name for i in self.failed]
        self.d.run(exit_code=exit_codes, stderr=stderr)
        self.assertListEqual(self.d.out['failures'], [1] * invocations)

    def test_wrong_input(self):
        stderr = [i.name for i in self.wrong_input]
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
        hprof_file = [i.name for i in self.si]
        self.h.run(hprof=hprof_file)
        self._assert_correct_out(invocations)

    def test_wrong_input(self):
        hprof_files = [i.name for i in self.wrong_input]
        for hprof_file in hprof_files:
            with self.assertRaises(WrongInputError):
                self.h.run(hprof=[hprof_file])

    def _assert_correct_out(self, invocations):
        self.assertSetEqual(set(self.h.out), self.h._output_names)
        for k in self.h.out.keys():
            self.assertEqual(len(self.h.out[k]), invocations)


class TamiflexTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        h = get_json_data('TamiflexFilter')
        cls.single_iterations = h['single_iterations']
        cls.wrong_input = h['wrong_input']

    def setUp(self):
        super(TamiflexTest, self).setUp()
        self.h = Tamiflex()

        self.si = write_to_tempfiles(TamiflexTest.single_iterations)
        self.wrong_input = write_to_tempfiles(TamiflexTest.wrong_input)

    def tearDown(self):
        for f in itertools.chain(self.si, self.wrong_input):
            f.close()

    def test_single_iteration_path(self):
        invocations = len(self.si)
        ref_log = [i.name for i in self.si]
        self.h.run(reflection_log=ref_log)
        self._assert_correct_out(invocations)

    def test_wrong_input(self):
        ref_logs = [i.name for i in self.wrong_input]
        for ref_log in ref_logs:
            with self.assertRaises(WrongInputError):
                self.h.run(reflection_log=[ref_log])

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


class HProfTest(unittest.TestCase):
    def test_wrong_outputs(self):
        with self.assertRaises(ValueError):
            HProf(outputs=Types(('a', list, int), ('b', list, int)),
                  start_marker='', end_marker='',
                  skip=1, data_re=None, start_re=None)


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

    def test_no_arguments(self):
        with self.assertRaises(ValueError):
            Aggregate()

    def test_malformed_argument(self):
        with self.assertRaises(ValueError):
            Aggregate('a', (1, 'a', 'b'))


class CondenseTest(unittest.TestCase):
    def setUp(self):
        self.results = {1: {'a': 42,
                            'b': 32},
                        2: {'b': 0,
                            'c': 21}}

    def test_implicit(self):
        f = Condense(('col1', 'col2'), [('a', Value('id1')), ('b', Value('id2'))])
        f._run(results=self.results)
        self.assertEqual(f.out, {'col1': [42, 32], 'col2': ['id1', 'id2']})

    def test_explicit(self):
        f = Condense(('col1', 'col2'), [(1, 'a', Value('id1')), (2, 'b', Value('id2'))])
        f._run(results=self.results)
        self.assertEqual(f.out, {'col1': [42, 0], 'col2': ['id1', 'id2']})

    def test_implicit_fail(self):
        f = Condense(('col1', 'col2'), [('a', Value('id1')), ('d', Value('id2'))])
        with self.assertRaises(WrongInputError):
            f._run(results=self.results)

    def test_explicit_fail_column(self):
        f = Condense(('col1', 'col2'), [(1, 'a', Value('id1')), (2, 'd', Value('id2'))])
        with self.assertRaises(WrongInputError):
            f._run(results=self.results)

    def test_explicit_fail_composition(self):
        f = Condense(('col1', 'col2'), [(1, 'a', Value('id1')), (3, 'c', Value('id2'))])
        with self.assertRaises(WrongInputError):
            f._run(results=self.results)

    def test_malformed_arguments(self):
        f = Condense(('col1', 'col2'), [(1, 42, Value('id1')), (2, 'c', Value('id2'))])
        with self.assertRaises(ValueError):
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
        f = CondensingReceive(('col1', 'col2'), [('a', Value('id1')), ('b', Value('id2'))])
        f._run(**self.kwargs)
        self.assertEqual(f.out, {'col1': [42, 32], 'col2': ['id1', 'id2']})

    def test_explicit(self):
        f = CondensingReceive(('col1', 'col2'), [(1, 'a', Value('id1')), (2, 'b', Value('id2'))])
        f._run(**self.kwargs)
        self.assertEqual(f.out, {'col1': [42, 0], 'col2': ['id1', 'id2']})

    def test_implicit_fail(self):
        f = CondensingReceive(('col1', 'col2'), [('a', Value('id1')), ('d', Value('id2'))])
        with self.assertRaises(WrongInputError):
            f._run(**self.kwargs)

    def test_explicit_fail_column(self):
        f = CondensingReceive(('col1', 'col2'), [(1, 'a', Value('id1')), (2, 'd', Value('id2'))])
        with self.assertRaises(WrongInputError):
            f._run(**self.kwargs)

    def test_explicit_fail_composition(self):
        f = CondensingReceive(('col1', 'col2'), [(1, 'a', Value('id1')), (3, 'c', Value('id2'))])
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


class MeanTest(unittest.TestCase):
    def test_against_numpy_integers(self):
        rnd = random_integers(-20, 20, 50)
        f = Mean()
        f._run(values=rnd)
        self.assertAlmostEqual(f.out['mean'], average(rnd))

    def test_against_numpy_floats(self):
        rnd = random_sample(20)
        f = Mean()
        f._run(values=rnd)
        self.assertAlmostEqual(f.out['mean'], average(rnd))


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


class SumTest(unittest.TestCase):
    def test_integers(self):
        rnd = random_integers(-20, 20, 50)
        f = Sum()
        f._run(values=rnd)
        self.assertEqual(f.out['sum'], sum(rnd))

    def test_against_numpy_floats(self):
        rnd = random_sample(20)
        f = Sum()
        f._run(values=rnd)
        self.assertAlmostEqual(f.out['sum'], sum(rnd))


class EnumerateTest(unittest.TestCase):
    def test_preserves_input(self):
        f = Enumerate()
        f._run(values=[1, 2, 3])
        self.assertEqual(f.out['values'], [1, 2, 3])

    def test_enumerate(self):
        f = Enumerate(start=3, step=2)
        f._run(values=['a', 'b', 'c'])
        self.assertEqual(f.out['numbers'], [3, 5, 7])


class UnpackTest(unittest.TestCase):
    def test_valid(self):
        f = Unpack()
        f._run(singleton=[1])
        self.assertEqual(f.out['result'], 1)

    def test_list_too_long(self):
        f = Unpack()
        with self.assertRaises(WrongInputError):
            f._run(singleton=[1, 2, 3])

    def test_list_too_short(self):
        f = Unpack()
        with self.assertRaises(WrongInputError):
            f._run(singleton=[])


class MapTest(unittest.TestCase):
    def test_idenity(self):
        identity = Evaluation(lambda x: {'x': x}, Types(('x', object)), Types(('x', object)))
        f = Map(identity)
        f._run(values=[1, 2, 3])
        self.assertEqual(f.out['result'], [1, 2, 3])

    def test_multidimensional(self):
        multi = Evaluation(lambda x: {'x': [x]}, Types(('x', object)), Types(('x', object)))
        f = Map(multi)
        f._run(values=[1, 2, 3])
        self.assertEqual(f.out['result'], [[1], [2], [3]])

    def test_wrong_inputs(self):
        wrong = Evaluation(lambda x, y: {'x': x}, Types(('x', object), ('y', object)), Types(('x', object)))
        with self.assertRaises(TypeCheckError):
            Map(wrong)

    def test_wrong_outputs(self):
        wrong = Evaluation(lambda x: {'x': x, 'y': x}, Types(('x', object)), Types(('x', object), ('y', object)))
        with self.assertRaises(TypeCheckError):
            Map(wrong)

    def test_with_all_arguments(self):
        identity = Evaluation(lambda c: {'d': c}, Types(('c', object)), Types(('d', object)))
        f = Map(identity, 'a', 'b', 'c', 'd')
        f._run(a=[1, 2, 3])
        self.assertEqual(f.out['b'], [1, 2, 3])


class DecorateTest(unittest.TestCase):
    def test_valid(self):
        f = Decorate("{0}")
        f._run(values=[1, 2, 3])
        self.assertEqual(f.out['values'], ["1", "2", "3"])

    def test_nothing_to_interplolate(self):
        f = Decorate("")
        f._run(values=[1, 2, 3])
        self.assertEqual(f.out['values'], ["", "", ""])


class DropFirstTest(unittest.TestCase):
    def test_valid(self):
        f = DropFirst()
        f._run(xs=[1, 2, 3])
        self.assertEqual(f.out['xs'], [2, 3])


class SteadyStateTest(unittest.TestCase):
    def test_one_invocation(self):
        f = SteadyState(k=5, threshold=0.3)
        f._run(xs=[[30, 33, 4, 16, 29, 34, 10, 44, 12, 25, 22, 25, 36, 49, 32, 24, 39, 36, 34, 38]])
        self.assertEqual(f.out['xs'], [[36, 49, 32, 24, 39]])

    def test_two_invocations(self):
        f = SteadyState(k=5, threshold=0.3)
        f._run(xs=[[30, 33, 4, 16, 29, 34, 10, 44, 12, 25, 22, 25, 36, 49, 32, 24, 39, 36, 34, 38],
                   [15, 36, 21, 1, 2, 15, 47, 7, 19, 28, 39, 29, 32, 17, 15, 18, 14, 8, 39, 0]])
        self.assertEqual(f.out['xs'], [[36, 49, 32, 24, 39], [19, 28, 39, 29, 32] ])


class ConfidenceIntervalMeanTest(unittest.TestCase):
    def test_small_sample_set(self):
        f = ConfidenceIntervalMean(significance_level=0.9)
        f._run(values=[1, 2, 3])
        for actual, expected in zip(f.out['interval'], (1.9179390061550845, 2.0820609938449155)):
            self.assertAlmostEqual(actual, expected)

    def test_large_sample_set(self):
        f = ConfidenceIntervalMean(significance_level=0.9)
        f._run(values=range(31))
        for actual, expected in zip(f.out['interval'], (14.794795879876117, 15.205204120123883)):
            self.assertAlmostEqual(actual, expected)


class CI2AlternativesTest(unittest.TestCase):
    def test_small_sample_set(self):
        f = CI2Alternatives(significance_level=0.9)
        f._run(xs=[1, 2, 3], ys=range(31))
        for actual, expected in zip(f.out['interval'], (-13.219442204882425, -12.780557795117575)):
            self.assertAlmostEqual(actual, expected)

    def test_large_sample_set(self):
        f = CI2Alternatives(significance_level=0.9)
        f._run(xs=range(31), ys=range(31))
        for actual, expected in zip(f.out['interval'], (-0.29020244973403198, 0.29020244973403198)):
            self.assertAlmostEqual(actual, expected)
