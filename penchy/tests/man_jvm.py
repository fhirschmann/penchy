from penchy.compat import unittest
from penchy.jobs.hooks import Hook
from penchy.jobs.jvms import JVM
from penchy.jobs.workloads import ScalaBench
from penchy.maven import BootstrapPOM, get_classpath
from penchy.util import tempdir


class JVMTest(unittest.TestCase):
    def test_run(self):
        a = [0, 0, 0]
        b = [0, 0, 0]
        jvm = JVM('java')
        jvm.basepath = '/usr/bin'

        w = ScalaBench('dummy')
        jvm.workload = w
        jvm.hooks = [Hook(lambda: a.__setitem__(0, 1)),
                     Hook(lambda: a.__setitem__(1, 2)),
                     Hook(lambda: a.__setitem__(2, 3)),
                     Hook(teardown=lambda: b.__setitem__(0, 1)),
                     Hook(teardown=lambda: b.__setitem__(1, 2)),
                     Hook(teardown=lambda: b.__setitem__(2, 3))]

        self.assertFalse('stdout' in w.out)
        self.assertFalse('stderr' in w.out)
        self.assertFalse('exit_code' in w.out)

        with tempdir(prefix='penchy-test', delete=True):
            p = BootstrapPOM()
            for d in ScalaBench.DEPENDENCIES:
                p.add_dependency(d)
            p.write('pom.xml')
            jvm.add_to_cp(get_classpath())
            jvm.run()

        self.assertTrue('stdout' in w.out)
        self.assertTrue('stderr' in w.out)
        self.assertTrue('exit_code' in w.out)

        self.assertListEqual(a, [1, 2, 3])
        self.assertListEqual(b, [1, 2, 3])
