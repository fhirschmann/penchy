#!/usr/bin/env python

import os

from penchy.node import NodeConfig

# The location of your private ssh key
ID_RSA = os.path.expanduser('~/.ssh/id_rsa')

# The default username on the nodes
USERNAME = 'bench'

# A list of files to copy to the node
FILES = []

SSH_PORT = 22

# The port the server listens on
LISTEN_PORT = 4343

# List of nodes
NODES = [
          NodeConfig('192.168.56.11', SSH_PORT, USERNAME, '/home/bench')
        , NodeConfig('192.168.56.10', SSH_PORT, USERNAME, '/home/bench')
        ]

LOCALNODE = NodeConfig('localhost', 22, os.eviron['USER'], '/tmp')
