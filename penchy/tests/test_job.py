import unittest2
from itertools import chain

from penchy.jobs import job
from penchy.jobs.dependency import Edge
from penchy.jobs.elements import _check_kwargs
from penchy.jobs.jvms import JVM
from penchy.jobs.workloads import ScalaBench
from penchy.jobs.tools import HProf
from penchy.jobs.filters import Print
from penchy.tests.util import MockPipelineElement


class JobClientElementsTest(unittest2.TestCase):

    def setUp(self):
        super(JobClientElementsTest, self).setUp()
        self.jvm = JVM('foo')
        w = ScalaBench('scalac')
        self.jvm.workload = w
        t = HProf('')
        self.jvm.tool = t
        f = Print()
        self.config = job.makeJVMNodeConfiguration(self.jvm, 'pseudo_node')
        self.job = job.Job(self.config, [Edge(w, f)], [])

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
        self.config.jvm.workload = None
        self.assertSetEqual(self.job._get_client_dependencies(self.config),
                            HProf.DEPENDENCIES)


class JobServerElementsTest(unittest2.TestCase):
    def setUp(self):
        super(JobServerElementsTest, self).setUp()
        self.config = job.makeJVMNodeConfiguration(JVM('foo'), 'pseudo_node')
        self.job = job.Job([self.config], [], [])

    def test_empty_elements(self):
        self.assertSetEqual(self.job.get_server_elements(), set())

    def test_nonempty_elements(self):
        self.job.server_flow = [Edge(1, 2), Edge(3, 4)]
        self.assertSetEqual(self.job.get_server_elements(), set([2, 4]))


class CheckArgsTest(unittest2.TestCase):
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
