from hashlib import sha1

from penchy.compat import unittest, update_hasher
from penchy.jobs.dependency import Edge
from penchy.jobs.filters import Print, DacapoHarness, Receive, Send
from penchy.jobs.job import Job, SystemComposition, NodeSetting
from penchy.jobs.jvms import JVM
from penchy.jobs.tools import HProf
from penchy.jobs.typecheck import Types
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


class JobCheckTest(unittest.TestCase):
    def test_valid_job(self):
        c = make_system_composition()
        w = ScalaBench('jython')
        f = DacapoHarness()
        s = Send()
        r = Receive()
        p = Print()
        c.jvm.workload = w
        j = Job(c,
                [w >> f >> ('times', 'payload') >> s],
                [r >> p])

        self.assertTrue(j.check())

    def test_client_cycle(self):
        c = make_system_composition()
        w = ScalaBench('jython')
        f = DacapoHarness()
        s = Send()
        r = Receive()
        p = Print()
        c.jvm.workload = w
        j = Job(c, [f >> f >> s], [r >> p])
        self.assertFalse(j.check())

    def test_server_cycle(self):
        c = make_system_composition()
        w = ScalaBench('jython')
        f = DacapoHarness()
        s = Send()
        r = Receive()
        p = Print()
        m = MockPipelineElement()
        m.inputs = Types(('a', int))
        m.outputs = Types(('a', int))
        c.jvm.workload = w
        j = Job(c, [w >> f >> s], [r >> m >> m >> p])
        self.assertFalse(j.check())

    def test_no_workload(self):
        c = make_system_composition()
        j = Job(c, [], [])
        self.assertFalse(j.check())

    def test_wrong_output(self):
        c = make_system_composition()
        w = ScalaBench('jython')
        f = DacapoHarness()
        s = Send()
        r = Receive()
        p = Print()
        c.jvm.workload = w
        j = Job(c,
                [w >> [('a', 'stderr'), 'exit_code'] >> f >> s],
                [r >> p])
        self.assertFalse(j.check())

    def test_missing_input(self):
        c = make_system_composition()
        w = ScalaBench('jython')
        f = DacapoHarness()
        s = Send()
        r = Receive()
        p = Print()
        c.jvm.workload = w
        j = Job(c,
                [w >> 'exit_code' >> f >> s],
                [r >> p])
        self.assertFalse(j.check())
