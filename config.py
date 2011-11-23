#!/usr/bin/env python

import os

# The location of your private ssh key
ID_RSA = os.path.expanduser('~/.ssh/id_rsa')

# The default username on the nodes
USERNAME = 'bench'

# A list of files to copy to the node
FILES = ['client.py', 'dacapo_analyzer.py']

SSH_PORT = 22

# The port the server listens on
LISTEN_PORT = 4343

# List of nodes; tuple of (host, username, port, path)
NODES = [
        ('192.168.56.11', SSH_PORT, USERNAME, '/tmp/bench'),
        ('192.168.56.10', SSH_PORT, USERNAME, '/tmp/bench'),
        ]
