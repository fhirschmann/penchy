from penchy.config import *
from penchy.node import *
from penchy.tests.unit import *


class NodeConfigurationTest(unittest.TestCase):
    def setUp(self):
        self.nc1 = NodeConfiguration('localhost', 22, 'foo', '/tmp', '/usr/bin')
        self.nc2 = NodeConfiguration('localhost', 22, 'foo', '/tmp', '/usr/bin')

    def test_nodeconfiguration_identity(self):
        self.assertEquals(set((self.nc1, self.nc2)), set((self.nc1,)))
