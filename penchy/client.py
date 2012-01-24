""" Executes benchmarks and filters generated data. """

import logging
import xmlrpclib

import argparse

from penchy.util import load_config, load_job
from penchy.log import configure_logging


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
        self.job = load_job(self.args.job).job
        self.identifier = self.args.identifier
        self.proxy = xmlrpclib.ServerProxy("http://%s:%s/" % \
                (self.config.SERVER_HOST, self.config.SERVER_PORT))

        configure_logging(int(self.args.loglevel))

    def run(self):
        """
        Runs the client.
        """
        self.job.send = self.proxy.rcv_data

        for composition in self.job.compositions_for_node(self.identifier):
            self.job.run(composition)

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
        parser.add_argument("--loglevel", dest="loglevel", default='20')
        args = parser.parse_args(args=args)
        return args
