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
    def __init__(self, args):
        """
        :param args: arguments; this would normally be sys.argv
        :type args: list
        """
        args = self.parse_args(args)
        self.config, config_filename = self._load_config(args.config)
        self.job = self._load_job(args.job)

        self.nodes = [Node(n, self.job) for n in self.config.NODES]
        self.uploads = set((args.job, config_filename, find_bootstrap_client()))
        self.listener = ThreadedServer(Service, hostname="192.168.56.1",
                port=self.config.LISTEN_PORT)
        self.client_thread = self._setup_client_thread([args.job])
        self.bootstrap_args = []

    def _load_config(self, filename):
        """
        Loads the config module from filename. Looks
        in the current working directory as well.

        :param filename: filename of the config file
        :type filename: string
        :returns: tuple of (config object, config filename)
        :rtype: tuple
        """
        try:
            config = imp.load_source('config', filename)
            actual_filename = filename
        except IOError:
            try:
                config = imp.load_source('config', 'penchyrc')
                actual_filename = 'penchyrc'
            except IOError:
                raise IOError("Config file could not be loaded from: %s or ./penchyrc" % filename)

        sys.modules['config'] = config

        log.info('Using %s config module' % config.__file__)
        return (config, actual_filename)

    def _load_job(self, filename):
        """
        Loads a job.

        :param filename: filename of the job
        :type filename: string
        """
        job = imp.load_source('job', filename)
        return job

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

    def parse_args(self, args):
        """
        Parses the arguments.

        :param args: arguments; this would normally be sys.argv
        :type args: list
        """
        parser = argparse.ArgumentParser()
        log_group = parser.add_mutually_exclusive_group()
        log_group.add_argument("-d", "--debug",
                action="store_const", const=logging.DEBUG,
                dest="loglevel", default=logging.INFO,
                help="print debugging messages")
        log_group.add_argument("-q", "--quiet",
                action="store_const", const=logging.WARNING,
                dest="loglevel", help="suppress most messages")
        parser.add_argument("-c", "--config",
                action="store", dest="config",
                default=os.path.expanduser("~/.penchyrc"),
                help="config module to use")
        parser.add_argument("-f", "--load-from",
                action="store", dest="load_from",
                help="load penchy from this path on the node")
        parser.add_argument("job", help="job to execute",
                metavar="job")
        args = parser.parse_args(args)
        logging.root.setLevel(args.loglevel)
        if args.load_from:
            self.bootstrap_args.extend(['--load-from', args.load_from])
        return args

    def run_clients(self, jobfile):
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
                    self.bootstrap_args + \
                    [jobfile, "192.168.56.1", "4343", node.identifier]))
                node.disconnect()

    def run(self):
        """
        Runs the server component.
        """
        self.client_thread.start()
        self.listener.start()
