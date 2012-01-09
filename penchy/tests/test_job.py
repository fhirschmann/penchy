import unittest2

from penchy.jobs import job
from penchy.jobs.dependency import Edge
from penchy.jobs.jvms import JVM

class JobClientElementsTest(unittest2.TestCase):

    def setUp(self):
        super(JobClientElementsTest, self).setUp()
        self.config = job.makeJVMNodeConfiguration(JVM('foo'), 'pseudo_node')
        self.job = job.Job([self.config], [Edge(1, 2), Edge(3, 4)], [])

    def test_empty_elements(self):
        self.job.client_flow = []
        self.assertSetEqual(self.job.get_client_elements(self.config),
                            set())

    def test_full_client_elements(self):
        self.config.jvm.workload = 42
        self.config.jvm.tool = 23
        self.assertSetEqual(self.job.get_client_elements(self.config),
                            set([42, 23, 2, 4]))

    def test_empty_configuration(self):
        self.assertSetEqual(self.job.get_client_elements(self.config),
                            set([2, 4]))

    def test_empty_tool(self):
        self.config.jvm.workload = 42
        self.assertSetEqual(self.job.get_client_elements(self.config),
                            set([42, 2, 4]))

    def test_empty_workload(self):
        self.config.jvm.tool = 23
        self.assertSetEqual(self.job.get_client_elements(self.config),
                            set([23, 2, 4]))
