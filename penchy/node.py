#!/usr/bin/env python

import os
import logging
import atexit

import paramiko

from penchy.util import dict2string


log = logging.getLogger(__name__)


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


class NodeError(Exception):
    """
    Raised when errors occur while dealing
    with :class:`Node`.
    """


class Node(object):
    """
    This class represents a node (=a machine on which the benchmark
    will be run on).
    """

    _LOGFILES = set(('penchy_bootstrap.log', 'penchy_client.log'))

    def __init__(self, configuration):
        """
        Initialize the node.

        :param node: the node configuration
        :type node: :class:`NodeConfiguration`
        """

        self.config = configuration
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if not self.config.keyfile:
            self.ssh.load_system_host_keys()
        self.sftp = None
        self.client_is_running = False

    def __str__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.config)

    def connect(self):
        """
        Connect to the node.
        """
        log.info("Connecting to node %s" % self.config.host)
        self.ssh.connect(self.config.host, username=self.config.username,
                port=self.config.ssh_port, password=self.config.password,
                key_filename=self.config.keyfile)

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

    def get_logs(self):
        """
        This method will read the client's log file
        and log it using the server's logging facilities.
        """
        for filename in self.__class__._LOGFILES:
            try:
                filename = os.path.join(self.config.path, filename)
                logfile = self.sftp.open(filename)
                log.info("".join(["Replaying logfile for",
                    str(self), os.linesep, logfile.read()]))
                logfile.close()
            except IOError:
                log.error("Logfile %s could not be received from %s" % \
                        (filename, self))

    def execute(self, cmd):
        """
        Executes command on the node

        :param cmd: command to execute
        :type cmd: string
        """
        log.info("Executing %s on %s" % (cmd, self))
        return self.ssh.exec_command(cmd)

    def execute_penchy(self, job):
        """
        Executes penchy on this node.

        :param job: the job to execute
        :type job: string
        """
        if self.client_is_running:
            raise NodeError("You may not start penchy twice!")

        self.execute('cd %s && python penchy_bootstrap %s' % (
            self.config.path, job))
        self.client_is_running = True

        @atexit.register
        def kill():
            self.connect()
            self.kill()

    def kill(self):
        """
        This kills the PenchY on this node.

        An existing pidfile named `penchy.pid` must exist on the node.
        """
        pidfile_name = os.path.join(self.config.path, 'penchy.pid')
        pidfile = self.sftp.open(pidfile_name)
        pid = pidfile.read()
        pidfile.close()
        self.execute('kill ' + pid)
        log.warn('Client on %s was terminated' % self)
