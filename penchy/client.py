""" Executes benchmarks and filters generated data. """

import time
import sys

import rpyc


class Client(object):
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

    def main(argv):
        pass
