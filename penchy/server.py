"""
Initiates multiple JVM Benchmarks and accumulates the results.
"""

import os
import logging

import argparse
import rpyc
from rpyc.utils.server import ThreadedServer

from penchy.node import Node

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("server")


class Service(rpyc.Service):

    def exposed_rcv_data(self, output):
        """
        Receive client data.

        :param output: benchmark output that has been filtered by the client.
        """
        # XXX: testing stub
        log.info("Received: " + str(output))


def run(config, job):
    """
    Runs the server component.

    :param config: the config module to use
    :type config: config
    :param job: filename of the job to execute
    :type job: string
    """

    nodes = [Node(n) for n in config.NODES]

    for node in nodes:
        node.connect()
        node.put(job)

        # TODO: Execute the client and disconnect immediately
        #node.execute('cd %s && python client.py' % node.path)
        node.disconnect()

    t = ThreadedServer(Service, hostname="192.168.56.1",
            port=config.LISTEN_PORT)
    t.start()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    log_group = parser.add_mutually_exclusive_group()
    log_group.add_argument("-d", "--debug",
            action="store_const", const=logging.DEBUG,
            dest="loglevel", default=logging.INFO,
            help="print debugging messages")
    log_group.add_argument("-q", "--quiet",
            action="store_const", const=logging.WARNING,
            dest="loglevel", help="suppress most messages")
    parser.add_argument("-c", "--config",
            action="store", dest="config", default=None,
            help="config module to use")
    parser.add_argument("job", help="job to execute",
            metavar="job")
    args = parser.parse_args()
    logging.root.setLevel(args.loglevel)
    log.info('Using the "%s" config module' % args.config)

    if args.config:
        config = __import__(args.config)
    else:
        from penchy import config

    run(config, args.job)
