""" Executes benchmarks and filters generated data. """

import time
import sys
import logging
import imp
import xmlrpclib

import argparse

from penchy.util import load_config, load_job


log = logging.getLogger(__name__)


class Client(object):
    """
    This class represents a client which executes a job
    and sends the results to the server.
    """
    def __init__(self, args):
        """
        :param args: arguments; this would normally be sys.argv
        :type args: list
        """
        self.args = self.parse_args(args)
        self.config = load_config(self.args.config)
        self.job = load_job(self.args.job)
        self.identifier = self.args.identifier
        self.proxy = xmlrpclib.ServerProxy("http://%s:%s/" % (self.config.SERVER_HOST,
            self.config.SERVER_PORT))

        try:
            logging.root.setLevel(getattr(logging, self.args.loglevel))
        except AttributeError:
            pass

    def run(self):
        """
        Runs the client.
        """
        self.job.job.send = self.proxy.rcv_data

        for configuration in self.job.job.configurations_for_node(self.identifier):
            self.job.job.run(configuration)
            #self.proxy.rcv_data(str(configuration.hash()), 'results!')

    def parse_args(self, args):
        """
        Parses the arguments.

        :param args: arguments; this would normally be sys.argv
        :type args: list
        """
        parser = argparse.ArgumentParser(description=__doc__, prog=args)
        parser.add_argument("job", help="job to execute", metavar="job")
        parser.add_argument("config", help="config file to use", metavar="config")
        parser.add_argument("identifier", help="my identifier", metavar="identifier")
        parser.add_argument("-l", "--loglevel", dest="loglevel", default='INFO')
        args = parser.parse_args(args=args)
        return args
