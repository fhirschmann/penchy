#!/usr/bin/env python

import os

from penchy.util import dict2string


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

    @property
    def identifier(self):
        """
        A unique identifier for this node.
        """
        return self.host

    def __str__(self):
        return "<%s: %s>" % (self.__class__.__name__,
                dict2string(self.__dict__, ['host', 'ssh_port']))
