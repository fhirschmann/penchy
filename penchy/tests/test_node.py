from penchy.compat import unittest
from penchy.config import *
from penchy.node import *


class NodeConfigurationTest(unittest.TestCase):
    def setUp(self):
        self.nc1 = NodeConfiguration('localhost', 22, 'foo', '/tmp', '/usr/bin')
        self.nc2 = NodeConfiguration('localhost', 22, 'foo', '/tmp', '/usr/bin')
        self.n1 = Node(self.nc1, None)
        self.n2 = Node(self.nc2, None)

    def test_nodeconfiguration_identity(self):
        self.assertEquals(set((self.nc1, self.nc2)), set((self.nc1,)))
        self.assertEquals(set((self.n1, self.n2)), set((self.n1,)))
