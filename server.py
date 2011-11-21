#!/usr/bin/env python

import os
import sys
import paramiko
import logging

from config import *

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("server")

class Node(object):
    """
    This class represents a node (=a machine on which the benchmark
    will be run on).
    """
    def __init__(self, node, pkey):
        """Initialize the node

        :param node: tuple of (hostname, port, username, remote path)
        :type pkey: paramiko.RSAKey
        """

        self.host, self.port, self.username, self.path = node
        self.pkey = pkey
        self.transport = paramiko.Transport((self.host, self.port))
        self.sftp = None
        self.ssh = None

    def connect(self):
        """Connect to the node"""

        log.info("Connecting to node %s" % self.host)
        self.transport.connect(username = self.username, pkey = self.pkey)
        self.sftp = paramiko.SFTPClient.from_transport(self.transport)
        self.ssh = self.transport.open_session()

        # Create the directory we will be uploading to
        try:
            self.sftp.mkdir(self.path)
        except IOError:
            pass

    def put(self, filename):
        """Upload a file to the node

        :param filename: string
        """

        location = self.path + os.path.sep + os.path.basename(filename)
        log.info("Copying file %s to %s" % (filename, location))
        self.sftp.put(sys.path[0] + os.path.sep + filename, location)


if __name__ == "__main__":
    pkey = paramiko.RSAKey.from_private_key_file(ID_RSA)

    nodes = []
    for node in NODES:
        nodes.append(Node(node, pkey))

    for node in nodes:
        node.connect()
        for f in FILES:
            node.put(f)
