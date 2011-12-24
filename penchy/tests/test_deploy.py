#!/usr/bin/env python

import os
import sys
import random
import unittest2
import tempfile
import logging

from penchy.server import Node
from penchy.util import NodeConfig
from penchy.server import run as start_server

logging.root.setLevel(logging.DEBUG)


class SFTPTest(unittest2.TestCase):

    def setUp(self):
        self.f = tempfile.NamedTemporaryFile(dir=tempfile.gettempdir())
        self.fname = os.path.basename(self.f.name)
        self.randint = str(random.randint(0, 100))
        self.f.write(self.randint)
        self.f.flush()

    def test_scp(self):
        nodeconfig = NodeConfig('127.0.0.1', 22, os.environ["USER"],
                tempfile.gettempdir() + os.sep + 'penchytest')
        node = Node(nodeconfig)

        node.connect()
        node.put(self.f.name)

        filename = tempfile.gettempdir() + os.sep + self.fname
        self.assertTrue(file(filename, 'r').read() == self.randint)
