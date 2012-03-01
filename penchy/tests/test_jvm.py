from hashlib import sha1
import os

from penchy.compat import unittest, update_hasher
from penchy.jobs.jvms import JVM, JVMNotConfiguredError, JVMExecutionError, _extract_classpath
from penchy.jobs.hooks import Hook
from penchy.jobs.tools import HProf
from penchy.jobs.workloads import ScalaBench
from penchy.util import tempdir
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
        self.jvm._classpath = ['bar']
        self.assertListEqual(self.jvm._classpath, ['bar'])
        self.jvm.add_to_cp('foo')
        self.assertListEqual(self.jvm._classpath, ['bar', 'foo'])
        self.jvm.add_to_cp('baz')
        self.assertListEqual(self.jvm._classpath, ['bar', 'foo', 'baz'])

    def test_add_to_empty_classpath(self):
        self.jvm._classpath = []

        self.jvm.add_to_cp('foo')
        self.assertListEqual(self.jvm._classpath, ['foo'])
        self.jvm.add_to_cp('baz')
        self.assertListEqual(self.jvm._classpath, ['foo', 'baz'])

    def test_raise_nonconfigured_workload(self):
        self.jvm.workload = None
        with self.assertRaises(JVMNotConfiguredError):
            self.jvm.run()

    def test_raise_nonconfigured_classpath(self):
        self.jvm._classpath = []
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
        self.assertSequenceEqual(list(jvm._get_hooks()), [])

    def test_get_hooks_tool(self):
        a = [0]
        jvm = JVM('foo')
        w = MockPipelineElement()
        w.hooks = [Hook(lambda: a.__setitem__(0, 23),
                        lambda: a.__setitem__(0, 42))]
        jvm.workload = w
        self.assertSequenceEqual(list(jvm._get_hooks()), w.hooks)

    def test_get_hooks_workload(self):
        a = [0]
        jvm = JVM('foo')
        t = MockPipelineElement()
        t.hooks = [Hook(lambda: a.__setitem__(0, 23),
                        lambda: a.__setitem__(0, 42))]
        jvm.tool = t
        self.assertSequenceEqual(list(jvm._get_hooks()), t.hooks)


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

    def test_execution_error(self):
        j = JVM('/bin/false')
        j.add_to_cp('foo')
        j.workload = ScalaBench('dummy')
        with tempdir(delete=True):
            with self.assertRaises(JVMExecutionError):
                j.run()


class ExtractClasspathTest(unittest.TestCase):

    def test_valid_options(self):
        expected = ['foo', 'bar', 'baz']
        options = ['-cp', os.pathsep.join(expected)]
        self.assertListEqual(_extract_classpath(options), expected)
        options = ['-classpath', os.pathsep.join(expected)]
        self.assertListEqual(_extract_classpath(options), expected)

    def test_multiple_classpaths(self):
        expected = ['foo', 'bar', 'baz']
        options = ['-cp', 'com:org:de', '-cp', os.pathsep.join(expected)]
        self.assertListEqual(_extract_classpath(options), expected)

    def test_only_option(self):
        options = ['-cp']
        self.assertListEqual(_extract_classpath(options), [])
