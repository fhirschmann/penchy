from hashlib import sha1

from penchy.compat import unittest, update_hasher
from penchy.jobs.jvms import JVM, JVMNotConfiguredError
from penchy.jobs.tools import HProf
from penchy.jobs.workloads import ScalaBench
from penchy.tests.util import MockPipelineElement


def setup_jvm(self):
    self.jvm = JVM('java')
    self.w = ScalaBench('batik')
    self.jvm.workload = self.w
    self.t = HProf('')
    self.jvm.tool = self.t
    self.jvm.add_to_cp('foo')


class JVMClasspathTest(unittest.TestCase):
    setUp = setup_jvm

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

    def test_raise_nonconfigured_workload(self):
        self.jvm.workload = None
        with self.assertRaises(JVMNotConfiguredError):
            self.jvm.run()

    def test_raise_nonconfigured_classpath(self):
        self.jvm._classpath = None
        with self.assertRaises(JVMNotConfiguredError):
            self.jvm.run()


class JVMCmdlineTest(unittest.TestCase):
    setUp = setup_jvm

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


class JVMHooksTest(unittest.TestCase):
    setUp = setup_jvm

    def test_get_hooks_empty(self):
        jvm = JVM('foo')
        self.assertListEqual(list(map(list, jvm._get_hooks())), [[], []])

    def test_get_hooks_tool(self):
        a = [0]
        b = [0]
        jvm = JVM('foo')
        w = MockPipelineElement()
        w.prehooks = [lambda: a.__setitem__(0, 23)]
        w.posthooks = [lambda: a.__setitem__(0, 42)]
        jvm.workload = w
        self.assertListEqual(list(map(list, jvm._get_hooks())), [w.prehooks,
                                                                 w.posthooks])

    def test_get_hooks_workload(self):
        a = [0]
        b = [0]
        jvm = JVM('foo')
        t = MockPipelineElement()
        t.prehooks = [lambda: a.__setitem__(0, 23)]
        t.posthooks = [lambda: a.__setitem__(0, 42)]
        jvm.tool = t
        self.assertListEqual(list(map(list, jvm._get_hooks())), [t.prehooks,
                                                                 t.posthooks])


class JVMTest(unittest.TestCase):
    def test_eq(self):
        i = JVM('foo')
        j = JVM('foo')
        self.assertEqual(i, j)
        i.workload = ScalaBench('dummy')
        j.workload = ScalaBench('dummy')
        self.assertEqual(i, j)
        i.workload = None
        j.workload = None
        self.assertEqual(i, j)
        i._user_options = '-server'
        self.assertNotEqual(i, j)
        j._user_options = '-server'
        self.assertEqual(i, j)

    def test_ne(self):
        i = JVM('foo')
        j = JVM('bar')
        self.assertNotEqual(i, j)

    def test_hash(self):
        i = JVM('foo')
        s = set((i,))
        self.assertIn(i, s)

    def test_sha1hash(self):
        path = 'foo'
        options = 'option'
        i = JVM(path, options)
        h = sha1()
        update_hasher(h, path)
        update_hasher(h, options)
        self.assertEqual(i.hash(), h.hexdigest())

    def test_wrong_comparison(self):
        i = JVM('foo')
        self.assertNotEqual(i, 2)
