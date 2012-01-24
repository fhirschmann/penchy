"""
Initiates multiple JVM Benchmarks and accumulates the results.
"""
import logging
import os
import signal
import threading
from SimpleXMLRPCServer import SimpleXMLRPCServer

from penchy.maven import makeBootstrapPOM
from penchy.node import Node
from penchy.util import find_bootstrap_client


log = logging.getLogger(__name__)


class Server(object):
    """
    This class represents the server.
    """
    # The dict of results we will receive (SystemComposition : result)
    results = {}

    _rcv_lock = threading.Lock()

    def __init__(self, config, job):
        """
        :param config: config module to use
        :type config: module
        :param job: module of job to execute
        :type job: module
        """
        self.config = config
        self.job = job.job
        self.job_file = job.__file__
        # XXX: DEBUG
        print config.__file__
        # additional arguments to pass to the bootstrap client
        self.bootstrap_args = []

        # List of nodes to upload to
        self.nodes = dict((n.node_setting.identifier,
            Node(n.node_setting, job)) for n in self.job.compositions)

        # Files to upload
        self.uploads = (
                (job.__file__,),
                (find_bootstrap_client(),),
                (self.config.__file__, 'config.py'))

        # Set up the listener
        self.server = SimpleXMLRPCServer(
                (config.SERVER_HOST, config.SERVER_PORT),
                allow_none=True)
        self.server.register_function(self.rcv_data, "rcv_data")

        # Set up the thread which is deploying the job
        self.client_thread = self._setup_client_thread()

        # Signal handler
        signal.signal(signal.SIGTERM, self.signal_handler_shutdown)

    def _setup_client_thread(self):
        """
        Sets up the client threads.

        :param args: arguments to pass to run_clients()
        :type args: list
        :returns: the thread object
        :rtype: :class:`threading.Thread`
        """
        thread = threading.Thread(target=self.run_clients)
        thread.daemon = True
        return thread

    def node_for(self, setting):
        """
        Find the Node for a given :class:`NodeSetting`.

        :param setting: setting to receive Node for
        :type setting: :class:`NodeSetting`
        :returns: the Node
        :rtype: :class:`Node`
        """
        return self.nodes[setting.identifier]

    def rcv_data(self, hashcode, result):
        """
        This is the method exposed to the nodes.

        :param hashcode: the hashcode to identify the
                         :class:`SystemComposition` by
        :type hashcode: string
        :param result: the result of the job
        """
        for composition in self.job.compositions:
            if hashcode == composition.hash():
                break
        else:
            raise ValueError('Composition not expected')

        with Server._rcv_lock:
            self.node_for(composition.node_setting).expected.remove(composition)
            Server.results[composition] = result

    @property
    def received_all_results(self):
        return all([n.received_all_results for n in self.nodes.values()])

    @property
    def nodes_timed_out(self):
        return all([n.timed_out for n in self.nodes.values()])

    def run_clients(self):
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
                    self.bootstrap_args + [os.path.basename(self.job_file),
                        'config.py', node.setting.identifier]))
                node.disconnect()

    def signal_handler_shutdown(self, num, frame):
        for node in self.nodes.values():
            node.close()
        self.server.server_close()

    def run(self):
        """
        Runs the server component.
        """
        print dir(self.server)
        self.client_thread.start()
        while not self.received_all_results:
            self.server.handle_request()

        log.info("Received results from all nodes. Excellent.")
        self.run_pipeline()

    def run_pipeline(self):
        """
        This method is called when we have received results from all nodes and
        starts the serverside pipeline.
        """
        log.info(Server.results)
        self.job.receive = lambda: Server.results
        self.job.run_server_pipeline()
