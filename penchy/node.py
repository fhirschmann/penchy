#!/usr/bin/env python

import os
import logging
import atexit
from threading import Timer

import paramiko


log = logging.getLogger(__name__)


class NodeError(Exception):
    """
    Raised when errors occur while dealing
    with :class:`Node`.
    """


class Node(object):  # pragma: no cover
    """
    This class represents a node (=a machine on which the benchmark
    will be run on) and provides basic ssh/sftp functionality.
    """

    _LOGFILES = set(('penchy_bootstrap.log', 'penchy.log'))

    def __init__(self, configuration, job):
        """
        Initialize the node.

        :param node: the node configuration
        :type node: :class:`NodeConfiguration`
        :param job: the job to execute
        """
        self.config = configuration

        self.job = job
        self.timer = self._setup_timer()

        self.client_is_running = False
        self.client_has_finished = False
        self.client_timed_out = False

        self._setup_ssh()

    def __str__(self):
        return "<Node %s>" % self.config.host

    def __eq__(self, other):
        return isinstance(other, Node) and \
                self.config.identifier == other.config.identifier

    def __hash__(self):
        return hash(self.config.identifier)

    def _setup_timer(self):
        """
        Sets up the Timer from the current job.
        """
        if hasattr(self.job, 'timeout'):
            timeout_after = getattr(self.job, 'timeout')
            if timeout_after:
                return Timer(timeout_after, self.timeout)

    def _setup_ssh(self):
        """
        Sets up the SSH objects.
        """
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if not self.config.keyfile:
            self.ssh.load_system_host_keys()
        self.sftp = None

    def logformat(self, msg):
        """
        Prepends the name of this node to a (log)message.
        """
        return " ".join([str(self.config.identifier), msg])

    def connect(self):
        """
        Connect to the node.
        """
        log.debug(self.logformat("Connecting"))
        self.ssh.connect(self.config.host, username=self.config.username,
                port=self.config.ssh_port, password=self.config.password,
                key_filename=self.config.keyfile)

        self.sftp = self.ssh.open_sftp()

    def disconnect(self):
        """
        Disconnect from the node.
        """
        log.debug(self.logformat("Disconnecting"))
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

        log.debug(self.logformat("Copying file %s to %s" % (local, remote)))
        self.sftp.put(local, remote)

    def get_logs(self):
        """
        This method will read the client's log file
        and log it using the server's logging facilities.
        """
        client_log = []

        for filename in self.__class__._LOGFILES:
            try:
                filename = os.path.join(self.config.path, filename)
                logfile = self.sftp.open(filename)
                client_log.append(logfile.read())
                logfile.close()
            except IOError:
                log.error("Logfile %s could not be received from %s" % \
                        (filename, self))

        log.info("".join(["Replaying logfile for ",
            self.config.identifier, os.linesep, "".join(client_log)]))
        log.info("End log for " + self.config.identifier)

    def execute(self, cmd):
        """
        Executes command on the node

        :param cmd: command to execute
        :type cmd: string
        """
        log.info(self.logformat("Executing %s" % cmd))
        return self.ssh.exec_command(cmd)

    def execute_penchy(self, args):
        """
        Executes penchy on this node.

        :param args: arguments to pass to penchy
        :type args: string
        """
        if self.client_is_running:
            raise NodeError("You may not start penchy twice!")

        self.execute('cd %s && python penchy_bootstrap %s' % (
            self.config.path, args))
        self.client_is_running = True

        if self.timer:
            self.timer.start()

        @atexit.register
        def kill():
            self.connect()
            self.get_logs()
            self.kill()
            self.disconnect()

    def timeout(self):
        """
        Executed when this node times out.
        """
        log.error(self.logformat("Timed out"))

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
        log.warn(self.logformat("Client was terminated"))
