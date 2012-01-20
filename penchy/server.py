"""
Initiates multiple JVM Benchmarks and accumulates the results.
"""

import os
import sys
import imp
import atexit
import logging
import threading
from tempfile import NamedTemporaryFile
from time import sleep

import argparse
import rpyc
from rpyc.utils.server import ThreadedServer

from penchy.node import Node
from penchy.util import find_bootstrap_client, load_job, load_config
from penchy.maven import makeBootstrapPOM

log = logging.getLogger(__name__)


class Service(rpyc.Service):
    def exposed_rcv_data(self, output):
        """
        Receive client data.

        :param output: benchmark output that has been filtered by the client.
        """
        # XXX: testing stub
        log.info("Received: " + str(output))


class Server(object):
    """
    This class represents the server.
    """
    def __init__(self, configfile, jobfile):
        """
        :param configfile: config file to use
        :type configfile: string
        :param jobfile: job file to execute
        :type jobfile: string
        """
        # additional arguments to pass to the bootstrap client
        self.bootstrap_args = []

        # TODO: maybe use ``config`` instead of ``self.config``
        self.config = load_config(configfile)
        self.job = load_job(jobfile)

        self.nodes = set((Node(nc.node, self.job) for nc in
                self.job.job.configurations))
        self.uploads = (
                (jobfile,),
                (find_bootstrap_client(),),
                (configfile, 'config.py'))
        self.listener = ThreadedServer(Service,
                hostname=self.config.SERVER_HOST,
                port=self.config.SERVER_PORT)
        self.client_thread = self._setup_client_thread([jobfile,
            'config.py'])

    def _setup_client_thread(self, args):
        """
        Sets up the client threads.

        :param args: arguments to pass to run_clients()
        :type args: list
        :returns: the thread object
        :rtype: :class:`threading.Thread`
        """
        thread = threading.Thread(target=self.run_clients, args=args)
        thread.daemon = True
        return thread

    def run_clients(self, jobfile, configfile):
        """
        This method will run the clients on all nodes.
        """
        with makeBootstrapPOM() as pom:
            for node in self.nodes:
                node.connect()
                for upload in self.uploads:
                    node.put(*upload)
                node.put(pom.name, 'bootstrap.pom')

                node.execute_penchy(" ".join(
                    self.bootstrap_args + \
                    [jobfile, configfile, node.identifier]))
                node.disconnect()

    def run(self):
        """
        Runs the server component.
        """
        self.client_thread.start()
        self.listener.start()
