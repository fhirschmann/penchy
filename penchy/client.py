""" Executes benchmarks and filters generated data. """

import time
import sys
import logging
import imp

import argparse
import rpyc


log = logging.getLogger(__name__)


class Client(object):
    """
    This class represents a client which executes a job
    and sends the results to the server.
    """
    def __init__(self):
        self.args = None
        self.job = None

    def run(self):
        """
        Runs the client.
        """
        self.job.job.run(self.job.jconfig)

    def parse_args(self, args):
        """
        Parses the arguments.

        :param argv: arguments; this would normally be sys.argv
        :type args: list
        """
        parser = argparse.ArgumentParser(description=__doc__, prog=args[0])
        parser.add_argument("job", help="job to execute", metavar="job")
        parser.add_argument("-l", "--loglevel", dest="loglevel",
                default='INFO')
        self.args = parser.parse_args(args=args[1:])

        try:
            logging.root.setLevel(getattr(logging, self.args.loglevel))
        except AttributeError:
            pass

        log.info('Loading job from %s' % self.args.job)
        self.job = imp.load_source('job', self.args.job)

    # XXX: Old method; only here for reference
    def send_data(self, filtered_output, server):
        """
        Send filtered benchmark output to server.

        :param filtered_output: relevant benchmark output
        :param server: server identifier, tuple of (Host, Port), if Port is None
                       default will be used
        """
        host, port = server
        conn = rpyc.connect(host, port)
        conn.root.rcv_data(filtered_output)
