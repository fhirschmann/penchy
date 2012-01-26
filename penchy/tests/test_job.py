from hashlib import sha1

from penchy.compat import unittest, update_hasher
from penchy.jobs.dependency import Edge
from penchy.jobs.elements import _check_kwargs
from penchy.jobs.filters import Print, DacapoHarness, Receive
from penchy.jobs.job import Job, SystemComposition, NodeSetting
from penchy.jobs.jvms import JVM
from penchy.jobs.tools import HProf
from penchy.jobs.workloads import ScalaBench
from penchy.tests.util import MockPipelineElement, make_system_composition


class JobClientElementsTest(unittest.TestCase):

    def setUp(self):
        super(JobClientElementsTest, self).setUp()
        self.jvm = JVM('foo')
        w = ScalaBench('scalac')
        self.jvm.workload = w
        t = HProf('')
        self.jvm.tool = t
        f = Print()
        self.config = SystemComposition(self.jvm, 'pseudo_node')
        self.job = Job(self.config, [Edge(w, f)], [])

    def test_empty_elements(self):
        self.job.client_flow = []
        self.assertSetEqual(self.job._get_client_dependencies(self.config),
                            ScalaBench.DEPENDENCIES.union(HProf.DEPENDENCIES))

    def test_full_client_elements(self):
        self.assertSetEqual(self.job._get_client_dependencies(self.config),
                            ScalaBench.DEPENDENCIES.union(HProf.DEPENDENCIES))

    def test_empty_tool(self):
        self.config.jvm.tool = None
        self.assertSetEqual(self.job._get_client_dependencies(self.config),
                            ScalaBench.DEPENDENCIES)

    def test_empty_workload(self):
        config = make_system_composition()
        config.jvm.tool = HProf('')
        self.assertSetEqual(Job(config, [], [])._get_client_dependencies(config),
                            HProf.DEPENDENCIES)

    def test_wrong_config(self):
        with self.assertRaises(ValueError):
            self.job._get_client_dependencies(SystemComposition(JVM('java'),
                                                                           'pseudo'))


class JobServerElementsTest(unittest.TestCase):
    def setUp(self):
        super(JobServerElementsTest, self).setUp()
        self.config = SystemComposition(JVM('foo'), 'pseudo_node')
        self.job = Job([self.config], [], [])

    def test_empty_elements(self):
        self.assertSetEqual(self.job._get_server_dependencies(), set())


class CheckArgsTest(unittest.TestCase):
    def setUp(self):
        super(CheckArgsTest, self).setUp()

        self.p = MockPipelineElement()
        self.p.inputs = (('foo', str), ('bar', list, int))
        self.d = {'foo' : '23', 'bar' : range(5)}

    def test_malformed_types(self):
        for t in ((1, str),
                 (1, list, str),
                 ('bar', str, 2),
                 ('baz', 2, list),
                 ()):
            with self.assertRaises(AssertionError):
                self.p.inputs = (t,)
                _check_kwargs(self.p, {})

    def test_wrong_type(self):
        self._raising_error_on_replacement(ValueError,
                                           (('foo', 23),
                                            ('foo', ['23']),
                                            ('bar', 42)))

    def test_wrong_subtype(self):
        self._raising_error_on_replacement(ValueError,
                                           (('bar', ['23']),
                                            ('bar', [(), ()])))

    def test_missing_arg(self):
        self._raising_error_on_deletion(ValueError,
                                           (('foo'),
                                            ('bar'),
                                            (['foo', 'bar']),
                                            (['foo', 'bar'])))

    def test_unused_input_count(self):
        self.d['baz'] = 42
        self.d['bad'] = 23
        self.assertEqual(_check_kwargs(self.p, self.d), 2)

    def test_fully_used_input_count(self):
        self.assertEqual(_check_kwargs(self.p, self.d), 0)

    def test_disabled_checking(self):
        self.p.inputs = None
        # d contains 2 unused inputs
        self.assertEqual(_check_kwargs(self.p, self.d), 0)

    def test_subtype_of_dict(self):
        self.p.inputs = [('foo', dict, int),
                         ('bar', dict, list, int)]
        self.assertEqual(_check_kwargs(self.p, {'foo' : dict(a=1, b=2),
                                                'bar' : dict(a=[1], b=[2])})
                         , 0)
        with self.assertRaises(ValueError):
            _check_kwargs(self.p, {'foo' : dict(a=1, b=2),
                                   'bar' : dict(a=1, b=2)})

    def _raising_error_on_deletion(self, error, deletions):
        for del_ in deletions:
            with self.assertRaises(error):
                d = self.d.copy()
                if not isinstance(del_, (list, tuple)):
                    del_ = [del_]
                for del__ in del_:
                    d.pop(del__, None)
                _check_kwargs(self.p, d)

    def _raising_error_on_replacement(self, error, replacements):
        for k, v in replacements:
            with self.assertRaises(error):
                d = self.d.copy()
                d[k] = v
                _check_kwargs(self.p, d)


class SystemCompositionsTest(unittest.TestCase):
    def setUp(self):
        self.single_host = [make_system_composition('192.168.1.10')]
        self.multi_host = [make_system_composition('192.168.1.11'),
                           make_system_composition('192.168.1.11')]
        self.job = Job(self.single_host + self.multi_host, [], [])

    def test_wrong_identifier(self):
        self.assertListEqual(self.job.compositions_for_node('baz'), [])

    def test_single_host_identifier(self):
        self.assertListEqual(self.job.compositions_for_node('192.168.1.10'),
                             self.single_host)

    def test_multi_host_identifier(self):
        self.assertListEqual(self.job.compositions_for_node('192.168.1.11'),
                             self.multi_host)

    def test_hash(self):
        c = make_system_composition()
        self.assertIn(c, set((c,)))

    def test_sha1hash(self):
        c = make_system_composition('localhost')
        c.jvm = JVM('path', 'options')
        h = sha1()
        update_hasher(h, c.jvm.hash())
        update_hasher(h, c.node_setting.hash())
        self.assertEqual(c.hash(), h.hexdigest())

    def test_equal(self):
        s1 = SystemComposition(JVM('java'),
                               NodeSetting('localhost', 22, 'dummy', '/', '/'))
        s2 = SystemComposition(JVM('java'),
                               NodeSetting('localhost', 22, 'dummy', '/', '/'))
        self.assertEqual(s1, s2)

    def test_not_equal(self):
        s1 = SystemComposition(JVM('java'),
                               NodeSetting('localhost', 22, 'dummy', '/', '/'))
        s2 = SystemComposition(JVM('java'),
                               NodeSetting('192.168.1.1', 22, 'dummy', '/',
        '/'))
        self.assertNotEqual(s1, s2)

        self.assertNotEqual(s1, SystemComposition(JVM('java'), 'no_setting'))


class ResetPipelineTest(unittest.TestCase):
    def setUp(self):
        self.workload = ScalaBench('dummy')
        self.workload.out['test'].append(42)
        self.tool = HProf('')
        self.tool.out['test'].append(23)
        self.filter = DacapoHarness()
        self.filter.out['test'].append(5)
        config = make_system_composition()
        config.jvm.workload = self.workload
        config.jvm.tool = self.tool
        self.job = Job(config, [Edge(self.workload, self.filter)], [])

    def test_reset_jvm_part(self):
        self.assertDictEqual(self.workload.out, {'test' : [42]})
        self.assertDictEqual(self.tool.out, {'test' : [23]})
        self.job._reset_client_pipeline()
        self.assertDictEqual(self.workload.out, {})
        self.assertDictEqual(self.tool.out, {})

    def test_reset_filter(self):
        self.assertDictEqual(self.filter.out, {'test' : [5]})
        self.job._reset_client_pipeline()
        self.assertDictEqual(self.filter.out, {})


class BuildEnvTest(unittest.TestCase):
    def setUp(self):
        self.job = Job(make_system_composition(), [], [])

    def test_empty_send_rcv(self):
        env = self.job._build_environment()
        self.assertDictEqual(env['receive'](), {})
        self.assertEqual(env['send']('data'), None)

    def test_set_send_rcv(self):
        receive = lambda: {'x' : 23}
        send = lambda data: 42
        self.job.receive = receive
        self.job.send = send
        env = self.job._build_environment()
        self.assertDictEqual(env['receive'](), {'x' : 23})
        self.assertEqual(env['send']('data'), 42)


class RunServerPipelineTest(unittest.TestCase):
    def setUp(self):
        self.receive = Receive()
        self.j = Job([], [], [Edge(self.receive, MockPipelineElement())])
        self.data = {'a': 1, 'b' : 2}
        self.j.receive = lambda: self.data

    def test_receive(self):
        self.assertDictEqual(self.receive.out, {})
        self.j.run_server_pipeline()
        self.assertDictEqual(self.receive.out, {'results' : self.data})

    def test_no_receivers(self):
        j = Job([], [], [])
        with self.assertRaises(ValueError):
            j.run_server_pipeline()
