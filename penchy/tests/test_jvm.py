from itertools import chain

from penchy.jobs.jvms import JVM
from penchy.jobs.workloads import ScalaBench
from penchy.jobs.tools import HProf
from penchy.tests.unit import unittest
from penchy.tests.util import MockPipelineElement


class JVMTest(unittest.TestCase):

    def setUp(self):
        self.jvm = JVM('java')
        self.w = ScalaBench('batik')
        self.jvm.workload = self.w
        self.t = HProf('')
        self.jvm.tool = self.t
        self.jvm.add_to_cp('foo')

    def test_add_to_existing_classpath(self):
        self.jvm._classpath = 'bar'
        self.assertEqual(self.jvm._classpath, 'bar')
        self.jvm.add_to_cp('foo')
        self.assertEqual(self.jvm._classpath, 'bar:foo')
        self.jvm.add_to_cp('baz')
        self.assertEqual(self.jvm._classpath, 'bar:foo:baz')

    def test_add_to_empty_classpath(self):
        self.jvm._classpath = None

        self.jvm.add_to_cp('foo')
        self.assertEqual(self.jvm._classpath, 'foo')
        self.jvm.add_to_cp('baz')
        self.assertEqual(self.jvm._classpath, 'foo:baz')

    def test_cmdline_no_classpath(self):
        self.jvm._classpath = ''

        self.assertListEqual(self.jvm.cmdline,
                             ['/java'] + self.t.arguments + self.w.arguments)

    def test_cmdline_no_tool(self):
        self.jvm.tool = None
        self.assertListEqual(self.jvm.cmdline,
                             ['/java'] + ['-classpath', 'foo'] +
                             self.w.arguments)

    def test_cmdline_no_workload(self):
        self.jvm.workload = None
        self.assertListEqual(self.jvm.cmdline,
                             ['/java'] + self.t.arguments +
                             ['-classpath', 'foo'])

    def test_cmdline_full(self):
        self.assertListEqual(self.jvm.cmdline,
                             ['/java'] + self.t.arguments +
                             ['-classpath', 'foo'] + self.w.arguments)

    def test_get_hooks_empty(self):
        jvm = JVM('foo')
        self.assertListEqual(map(list, jvm._get_hooks()), [[], []])

    def test_get_hooks_tool(self):
        a = [0]
        b = [0]
        jvm = JVM('foo')
        w = MockPipelineElement()
        w.prehooks = [lambda: a.__setitem__(0, 23)]
        w.posthooks = [lambda: a.__setitem__(0, 42)]
        jvm.workload = w
        self.assertListEqual(map(list, jvm._get_hooks()), [w.prehooks,
                                                           w.posthooks])

    def test_get_hooks_workload(self):
        a = [0]
        b = [0]
        jvm = JVM('foo')
        t = MockPipelineElement()
        t.prehooks = [lambda: a.__setitem__(0, 23)]
        t.posthooks = [lambda: a.__setitem__(0, 42)]
        jvm.tool = t
        self.assertListEqual(map(list, jvm._get_hooks()), [t.prehooks,
                                                           t.posthooks])
