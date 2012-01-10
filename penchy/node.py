#!/usr/bin/env python

from penchy.util import dict2string


class NodeConfig(object):
    """
    This class represents a configuration of a node.
    """

    def __init__(self, host, ssh_port, username, path):
        self.host = host
        self.ssh_port = ssh_port
        self.username = username
        self.path = path

    def __str__(self):
        return "<%s: %s>" % (self.__class__.__name__,
                dict2string(self.__dict__))
