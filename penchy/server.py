"""
Initiates multiple JVM Benchmarks and accumulates the results.
"""

import os
import sys
import imp
import atexit
import logging
import threading
from SimpleXMLRPCServer import SimpleXMLRPCServer
from tempfile import NamedTemporaryFile
from time import sleep

import argparse

from penchy.node import Node
from penchy.util import find_bootstrap_client, load_job, load_config
from penchy.maven import makeBootstrapPOM

log = logging.getLogger(__name__)


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
        self.nodes = dict((n.node.identifier, Node(n.node, job)) for \
                n in job.job.configurations)

        # Files to upload
        self.uploads = (
                (jobfile,),
                (find_bootstrap_client(),),
                (configfile, 'config.py'))

        # Set up the listener
        self.server = SimpleXMLRPCServer(
                (config.SERVER_HOST, config.SERVER_PORT),
                allow_none=True)
        self.server.register_function(self.rcv_data, "rcv_data")

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

    def rcv_data(self, result):
        print result

    def run_clients(self, jobfile, configfile):
        """
        This method will run the clients on all nodes.
        """
        with makeBootstrapPOM() as pom:
            for node in self.nodes.values():
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
        #self.listener.start()
        self.server.serve_forever()
