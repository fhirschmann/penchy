from penchy.compat import unittest
from penchy.jobs import *


class JobClientElementsTest(unittest.TestCase):
    def test_timeout_factor_int(self):
        ns = NodeSetting('localhost', 22, 'dummy', '/', '/', timeout_factor=5)
        self.assertEquals(ns.timeout_factor, 5)

    def test_timeout_factor_func(self):
        ns = NodeSetting('localhost', 22, 'dummy', '/', '/',
                timeout_factor=lambda: 6)
        self.assertEquals(ns.timeout_factor, 6)

    def test_jvm_no_timeout(self):
        j = jvms.JVM('java')
        w = workloads.ScalaBench('dummy')
        self.assertEquals(j.timeout, 0)
        j.workload = w
        self.assertEquals(j.timeout, 0)

    def test_jvm_timeout(self):
        j = jvms.JVM('java', timeout_factor=2)
        j.workload = workloads.ScalaBench('dummy', timeout=10)
        self.assertEquals(j.timeout, 20)

    def test_comp_timeout(self):
        n = NodeSetting('localhost', 22, 'dummy', '/', '/', timeout_factor=2)
        j = jvms.JVM('java', timeout_factor=2)
        j.workload = workloads.ScalaBench('dummy', timeout=10)
        c = SystemComposition(j, n)
        self.assertEquals(c.timeout, 40)

    def test_hooks(self):
        n = NodeSetting('localhost', 22, 'dummy', '/', '/', timeout_factor=2)
        j = jvms.JVM('java', timeout_factor=2)
        j.workload = workloads.ScalaBench('dummy', timeout=10)
        c = SystemComposition(j, n)
        c.set_timeout_function(lambda x, y: 42)
        self.assertEquals(j.prehooks[0](), 42)
        self.assertEquals(j.posthooks[0](), 42)
