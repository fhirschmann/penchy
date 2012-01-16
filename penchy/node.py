#!/usr/bin/env python

import os
import logging

import paramiko

from penchy.util import dict2string


log = logging.getLogger(__name__)


class NodeConfiguration(object):
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

    def __init__(self, configuration):
        """
        Initialize the node.

        :param node: the node configuration
        :type node: :class:`NodeConfiguration`
        """

        # TODO: SSH Keyfile and Passphrase may need to be specified

        self.config = node
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.load_system_host_keys()
        self.sftp = None

    def connect(self):
        """
        Connect to the node.
        """
        log.info("Connecting to node %s" % self.config.host)
        self.ssh.connect(self.config.host, username=self.config.username,
                port=self.config.ssh_port)

        self.sftp = self.ssh.open_sftp()

    def disconnect(self):
        """
        Disconnect from the node.
        """
        self.sftp.close()
        self.ssh.close()

    def put(self, local, remote=None):
        """
        Upload a file to the node

        :param local: path to the local file
        :type local: string
        :param remote: path to the remote file
        :type remote: string
        """

        local = os.path.abspath(local)

        if not remote:
            remote = os.path.basename(local)

        if not os.path.isabs(remote):
            remote = os.path.join(self.config.path, remote)

        try:
            self.sftp.mkdir(os.path.dirname(remote))
        except IOError:
            pass

        log.info("Copying file %s to %s" % (local, remote))
        self.sftp.put(local, remote)

    def execute(self, cmd):
        """
        Executes command on the node

        :param cmd: command to execute
        :type cmd: string
        """
        return self.ssh.exec_command(cmd)
