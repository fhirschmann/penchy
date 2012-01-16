#!/usr/bin/env python

import os


class NodeConfiguration(object):
    """
    This class represents a configuration of a node.
    """

    def __init__(self, host, ssh_port, username, path,
                 basepath, description="", password=None,
                 keyfile=None):
        """
        :param host: hostname (or IP) of node
        :type host: string
        :param ssh_port: port number of ssh server on node
        :type ssh_port: int
        :param username: login name for penchy on node
        :type username: string
        :param path: working directory on the node (this is where
                     the job will be uploaded to and where the
                     temporary files and directories will be created)
        :type path: string
        :param basepath: basepath for JVMs on this node
        :type basepath: string
        :param description: Textual description of node
        :type description: string
        :param password: this is either the password for a given username
                         or the passphrase to unlock the keyfile
        :type password: string
        :param keyfile: path to the ssh keyfile to use
        :type keyfile: string
        """
        self.host = host
        self.ssh_port = ssh_port
        self.username = username
        self.path = path
        self.basepath = basepath
        self.description = description
        self.password = password
        self.keyfile = keyfile

    def __str__(self):
        return "<%s: %s>" % (self.__class__.__name__,
                dict2string(self.__dict__, ['host', 'ssh_port']))


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
    NodeConfiguration('192.168.56.11', SSH_PORT, USERNAME, '/home/bench', '/usr/bin'),
    NodeConfiguration('192.168.56.10', SSH_PORT, USERNAME, '/home/bench', '/usr/bin')
]

LOCALNODE = NodeConfiguration('localhost', 22, os.environ['USER'], '/tmp', '/usr/bin')
