"""
Initiates multiple JVM Benchmarks and accumulates the results.
"""
import logging
import os
import signal
import threading
from SimpleXMLRPCServer import SimpleXMLRPCServer

from penchy.maven import make_bootstrap_pom
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
        self.server.register_function(self.node_error, "node_error")
        # XXX: I don't yet know if this will work. With no timeout set,
        # handle_request will wait forever and timeouts caused by Timer()
        # will not cause the server to stop waiting. I think this should work!
        self.server.timeout = 2

        # Set up the thread which is deploying the job
        self.client_thread = self._setup_client_thread()

        # Signal handler
        signal.signal(signal.SIGTERM, self._signal_handler)

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

    def _signal_handler(self, signum, frame):
        """
        This handles signals sent to this process.
        """
        log.info("Received signal %s " % signum)
        if signum == signal.SIGTERM:
            for node in self.nodes.values():
                node.close()
            self.server.server_close()

    def node_for(self, setting):
        """
        Find the Node for a given :class:`NodeSetting`
        or hashcode.

        :param setting: setting or hashcode to receive Node for
        :type setting: :class:`NodeSetting` or string
        :returns: the Node
        :rtype: :class:`Node`
        """
        return self.nodes[setting.identifier]

    def composition_for(self, hashcode):
        """
        Find the :class:`SystemComposition` for a given
        hashcode.

        :param hashcode: hashcode of the wanted composition
        :type hashcode: string
        :returns: the system composition
        :rtype: :class:`SystemComposition`
        """
        for composition in self.job.compositions:
            if hashcode == composition.hash():
                return composition

        raise ValueError('Composition not found')

    def rcv_data(self, hashcode, result):
        """
        This is a method exposed to the nodes.

        :param hashcode: the hashcode to identify the
                         :class:`SystemComposition` by
        :type hashcode: string
        :param result: the result of the job
        """
        composition = self.composition_for(hashcode)

        with Server._rcv_lock:
            self.node_for(composition.node_setting).expected.remove(composition)
            Server.results[composition] = result

    def node_error(self, hashcode, reason=None):
        """
        This is a method exposed to the nodes.

        It should be called by a node in case of errors.
        """
        composition = self.composition_for(hashcode)

        with Server._rcv_lock:
            self.node_for(composition.node_setting).expected.remove(composition)

    @property
    def received_all_results(self):
        """
        This indicates wheter we have received results for *all*
        :class:`SystemComposition`.
        """
        return all([n.received_all_results for n in self.nodes.values()])

    @property
    def nodes_timed_out(self):
        """
        This indicates wheter *all* nodes have timed out.
        """
        return all([n.timed_out for n in self.nodes.values()])

    def run_clients(self):
        """
        This method will run the clients on all nodes.
        """
        with make_bootstrap_pom() as pom:
            for node in self.nodes.values():
                node.connect()
                for upload in self.uploads:
                    node.put(*upload)
                node.put(pom.name, 'bootstrap.pom')

                node.execute_penchy(" ".join(
                    self.bootstrap_args + [os.path.basename(self.job_file),
                        'config.py', node.setting.identifier]))
                node.disconnect()

    def run(self):
        """
        Runs the server component.
        """
        self.client_thread.start()
        while not self.received_all_results and not self.nodes_timed_out:
            self.server.handle_request()

        for node in self.nodes.values():
            node.close()

        if self.received_all_results:
            log.info("Received results from all nodes. Excellent.")
        if self.nodes_timed_out:
            log.error("All nodes have timed out. That's not good!")

        self.run_pipeline()

    def run_pipeline(self):
        """
        This method is called when we have received results from all nodes and
        starts the serverside pipeline.
        """
        log.info(Server.results)
        self.job.receive = lambda: Server.results
        self.job.run_server_pipeline()
