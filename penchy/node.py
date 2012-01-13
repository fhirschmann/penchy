#!/usr/bin/env python

import os
import logging

import paramiko

from penchy.util import dict2string


log = logging.getLogger(__name__)


class NodeConfig(object):
    """
    This class represents a configuration of a node.
    """

    def __init__(self, host, ssh_port, username, path,
                 basepath, description=""):
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
        """
        self.host = host
        self.ssh_port = ssh_port
        self.username = username
        self.path = path
        self.basepath = basepath
        self.description = description

    def __str__(self):
        return "<%s: %s>" % (self.__class__.__name__,
                dict2string(self.__dict__))


class Node(object):
    """
    This class represents a node (=a machine on which the benchmark
    will be run on).
    """

    def __init__(self, node):
        """
        Initialize the node.

        :param node: tuple of (hostname, port, username, remote path)
        :type node: :class:`NodeConfig`
        """

        # TODO: SSH Keyfile and Passphrase may need to be specified

        self.node = node
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.load_system_host_keys()
        self.sftp = None

    def connect(self):
        """
        Connect to the node.
        """
        log.info("Connecting to node %s" % self.node.host)
        self.ssh.connect(self.node.host, username=self.node.username,
                port=self.node.ssh_port)

        self.sftp = self.ssh.open_sftp()

        # Create the directory we will be uploading to (if it doesn't exist)
        try:
            self.sftp.mkdir(self.node.path)
        except IOError:
            pass

    def disconnect(self):
        """
        Disconnect from the node.
        """
        self.sftp.close()
        self.ssh.close()

    def put(self, filename):
        """
        Upload a file to the node

        :param filename: the file to upload
        :type name: str
        """
        try:
            self.sftp.mkdir(self.node.path + os.sep + \
                    os.path.dirname(filename))
        except IOError:
            pass

        location = self.node.path + os.path.sep + os.path.basename(filename)
        log.info("Copying file %s to %s" % (filename, location))
        self.sftp.put(filename, location)

    def execute(self, cmd):
        """
        Executes command on the node

        :param cmd: command to execute
        :type cmd: str
        """
        return self.ssh.exec_command(cmd)
