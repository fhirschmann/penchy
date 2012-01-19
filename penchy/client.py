""" Executes benchmarks and filters generated data. """

import time
import sys
import logging
import imp

import argparse
import rpyc

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
        self.job = load_job(self.args.job, self.config)

        try:
            logging.root.setLevel(getattr(logging, self.args.loglevel))
        except AttributeError:
            pass

    def run(self):
        """
        Runs the client.
        """
        # TODO: Check MavenDependency checksums

        self.job.job.run(self.job.jconfig)
        self.send_data("Job finished!", (self.config.SERVER_HOST,
            self.config.SERVER_PORT))

    def parse_args(self, args):
        """
        Parses the arguments.

        :param args: arguments; this would normally be sys.argv
        :type args: list
        """
        # TODO: This could be imported from the config file
        parser = argparse.ArgumentParser(description=__doc__, prog=args)
        parser.add_argument("job", help="job to execute", metavar="job")
        parser.add_argument("config", help="config file to use", metavar="config")
        parser.add_argument("myname", help="my hostname", metavar="myname")
        parser.add_argument("-l", "--loglevel", dest="loglevel", default='INFO')
        args = parser.parse_args(args=args)
        return args

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
