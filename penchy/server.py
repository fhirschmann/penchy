"""
Initiates multiple JVM Benchmarks and accumulates the results.
"""

import os
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
from penchy.util import find_bootstrap_client
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


class Server:
    """
    This class represents the server.
    """
    def __init__(self, config, job):
        """
        :param config: A config module
        :param job: The job to execute:
        :type job: :class:`penchy.jobs.Job`
        """
        self.config = config
        self.job = job
        self.nodes = [Node(n, job) for n in config.NODES]
        self.uploads = set((self.job, find_bootstrap_client()))
        self.listener = ThreadedServer(Service, hostname="192.168.56.1",
                port=self.config.LISTEN_PORT)
        self.client_thread = threading.Thread(target=self.run_clients)
        self.client_thread.daemon = True
        self.bootstrap_args = []

    def run_clients(self):
        """
        This method will run the clients on all nodes.
        """
        with makeBootstrapPOM() as pom:
            for node in self.nodes:
                node.connect()
                for upload in self.uploads:
                    node.put(upload)
                node.put(pom.name, 'bootstrap.pom')

                node.execute_penchy(" ".join(
                    self.bootstrap_args + [self.job, "192.168.56.1", "4343"]))
                node.disconnect()

    def run(self):
        """
        Runs the server component.
        """
        self.client_thread.start()
        self.listener.start()
