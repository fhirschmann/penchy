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


class NodeSet(set):
    """
    This represents a set of nodes.
    """
    def get_node(self, identifier):
        for node in self:
            if node.config.identifier == identifier:
                return node


class Service(rpyc.Service):
    config = None
    job = None
    waiting_for = set()
    results = set()

    def exposed_rcv_data(self, identifier, output):
        """
        Receive client data.

        :param output: benchmark output that has been filtered by the client.
        """
        log.info("Received: " + str(output))
        node = Service.waiting_for.get_node(identifier)
        Service.waiting_for.remove(node)
        if len(Service.waiting_for) == 0:
            self.finish()

    def finish(self):
        """
        Called when we have received data from all nodes.
        """
        # TODO: Implement me
        log.info("Ready to do real work!")


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

        config = load_config(configfile)
        job = load_job(jobfile)

        # List of nodes to upload to
        self.nodes = NodeSet((Node(nc.node, job) for nc in
                job.job.configurations))

        # Files to upload
        self.uploads = (
                (jobfile,),
                (find_bootstrap_client(),),
                (configfile, 'config.py'))

        # Set up the listener
        self.listener = self._setup_service(config, job)

        # Set up the thread which is deploying the job
        self.client_thread = self._setup_client_thread([
            os.path.basename(jobfile), 'config.py'])

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

    def _setup_service(self, config, job):
        """
        Sets up the Service which answers to nodes.
        """
        listener = ThreadedServer(Service,
                hostname=config.SERVER_HOST,
                port=config.SERVER_PORT)
        listener.service.config = config
        listener.service.job = job
        listener.service.waiting_for = self.nodes.copy()
        return listener

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
                    [jobfile, configfile, node.config.identifier]))
                node.disconnect()

    def run(self):
        """
        Runs the server component.
        """
        self.client_thread.start()
        self.listener.start()
