"""
Initiates multiple JVM Benchmarks and accumulates the results.
"""

import os
import imp
import logging

import argparse
import rpyc
from rpyc.utils.server import ThreadedServer

from penchy.node import Node

log = logging.getLogger("server")


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
        :type job: :class:`penchy.jobs.job`
        """
        self.config = config
        self.job = job
        self.nodes = [Node(n) for n in config.NODES]

    def run(self):
        """
        Runs the server component.

        :param config: the config module to use
        :type config: config
        :param job: filename of the job to execute
        :type job: string
        """
        for node in self.nodes:
            node.connect()
            node.put(job)

            # TODO: Upload the bootstrap client and execute it.
            #node.execute('cd %s && python client.py' % node.path)
            node.disconnect()

        self.start_listening()

    def start_listening(self):
        t = ThreadedServer(Service, hostname="192.168.56.1",
                port=config.LISTEN_PORT)
        t.start()


def main(config, job):
    server = Server(config, args.job)
    server.run()

if __name__ == "__main__":
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
            action="store", dest="config",
            default=os.path.expanduser("~/.penchyrc"),
            help="config module to use")
    parser.add_argument("job", help="job to execute",
            metavar="job")
    args = parser.parse_args()
    logging.root.setLevel(args.loglevel)
    log.info('Using the "%s" config module' % args.config)

    try:
        config = imp.load_source('Config', args.config)
    except IOError:
        raise IOError("Config file could not be found: %s" % args.config)

    main(config, args.job)
