#!/usr/bin/env python

import os
import sys
import random
import unittest
import tempfile
import logging

from server import main as start_server

TEST_NODES = [('127.0.0.1', 22, os.environ["USER"], '/tmp/jvmbenchtests')]


logging.root.setLevel(logging.DEBUG)

class SFTPTest(unittest.TestCase):
    def setUp(self):
        self.f = tempfile.NamedTemporaryFile(dir=sys.path[0])
        self.fname = os.path.basename(self.f.name)
        self.randint = str(random.randint(0,100))
        self.f.write(self.randint)
        self.f.flush()

        class Config:
            ID_RSA = os.path.expanduser('~/.ssh/id_rsa')
            FILES = [self.fname]
            NODES = TEST_NODES
        self.config = Config()

    def test_scp(self):
        start_server(self.config)
        f = file(self.config.NODES[0][3] + os.sep + self.fname, 'r')
        self.assertTrue(f.read() == self.randint)
        

if __name__ == '__main__':
    unittest.main()
