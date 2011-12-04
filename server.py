#!/usr/bin/env python

"""
Initiates multiple JVM Benchmarks and accumulates the results.
"""

import os
import sys
import paramiko
import logging
import argparse
import rpyc

from rpyc.utils.server import ThreadedServer

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("server")


class Node(object):
    """
    This class represents a node (=a machine on which the benchmark
    will be run on).
    """
    def __init__(self, node, id_rsa):
        """
        Initialize the node.

        :param node: tuple of (hostname, port, username, remote path)
        :type node: tuple
        :param id_rsa: path of the private ssh key
        :type id_rsa: str
        :param ssh_port: port of the remote ssh daemon
        :type ssh_port: int
        """

        self.host, self.port, self.username, self.path = node
        self.id_rsa = id_rsa
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.load_system_host_keys()
        self.sftp = None

    def connect(self):
        """
        Connect to the node.
        """

        log.info("Connecting to node %s" % self.host)
        self.ssh.connect(self.host, username=self.username,
                key_filename=self.id_rsa, port=self.port)

        self.sftp = self.ssh.open_sftp()

        # Create the directory we will be uploading to (if it doesn't exist)
        try:
            self.sftp.mkdir(self.path)
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
            self.sftp.mkdir(self.path + os.sep + os.path.dirname(filename))
        except IOError:
            pass

        location = self.path + os.path.sep + filename
        log.info("Copying file %s to %s" % (filename, location))
        self.sftp.put(sys.path[0] + os.path.sep + filename, location)

    def execute(self, cmd):
        """
        Executes command on the node

        :param cmd: command to execute
        :type cmd: string
        """

        return self.ssh.exec_command(cmd)

class Service(rpyc.Service):
    def exposed_rcv_data(self, output):
        """
        Receive client data.
     
        :param output: benchmark output that has been filtered by the client.
        """
        # XXX: testing stub
        log.info("Received: " + str(output))

def main(config, job=None):
    """
    Runs the server component.

    :param config: the config module to use
    :type config: config
    """

    nodes = []
    for node in config.NODES:
        nodes.append(Node(node, config.ID_RSA))

    for node in nodes:
        node.connect()
        for f in config.FILES:
            node.put(f)

        # Execute the client and disconnect immediately
        node.execute('cd %s && python client.py' % node.path)
        node.disconnect()

    t = ThreadedServer(Service, hostname="192.168.56.1", port=config.LISTEN_PORT)
    t.start()
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    log_group = parser.add_mutually_exclusive_group()
    log_group.add_argument("-d", "--debug",
            action="store_const", const=logging.DEBUG,
            dest="loglevel", default=logging.INFO,
            help="print debugging messages")
    log_group.add_argument("-q", "--quiet",
            action="store_const", const=logging.WARNING,
            dest="loglevel", help="suppress most messages")
    parser.add_argument("-c", "--config",
            action="store", dest="config", default="config",
            help="config module to use")
    parser.add_argument("job", help="job to execute",
            metavar="job")
    args = parser.parse_args()
    logging.root.setLevel(args.loglevel)
    log.info('Using the "%s" config module' % args.config)
    config = __import__(args.config)
    job = __import__(args.job[:-3] if args.job.endswith('py') else args.job)
    main(config, job)
