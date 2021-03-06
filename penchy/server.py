"""
Initiates multiple JVM Benchmarks and accumulates the results.

 .. moduleauthor:: Fabian Hirschmann <fabian@hirschmann.email>

 :copyright: PenchY Developers 2011-2012, see AUTHORS
 :license: MIT License, see LICENSE
"""
import logging
import os
import signal
import threading
from penchy.compat import SimpleXMLRPCServer, nested

from penchy.maven import make_bootstrap_pom
from penchy.util import make_bootstrap_client
from penchy.node import Node


log = logging.getLogger(__name__)


class Server(object):
    """
    This class represents the server.
    """
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

        # The dict of results we will receive (SystemComposition : result)
        self.results = {}

        # The dict of Timers which implement timeouts
        self.timers = {}

        # additional arguments to pass to the bootstrap client
        self.bootstrap_args = []

        # List of nodes to upload to
        self.nodes = dict((n.node_setting.identifier,
            Node(n.node_setting, job)) for n in self.job.compositions)

        # Files to upload
        self.uploads = (
                (job.__file__,),
                (self.config.__file__, 'config.py'))

        # Set up the listener
        self.server = SimpleXMLRPCServer(
                (config.SERVER_HOST, config.SERVER_PORT),
                allow_none=True)
        self.server.register_function(self.exp_rcv_data, 'rcv_data')
        self.server.register_function(self.exp_report_error, 'report_error')
        self.server.register_function(self.exp_set_timeout, 'set_timeout')

        # This sets the timeout after which self.server.handle_request() should
        # return. This should be a nonzero value, because we are running it
        # in a loop until we have received all results. However, timeouts
        # can occur while running handle_request() in which case handle_request()
        # would run forever without actually expecting anymore results.
        self.server.timeout = 2

        # Set up the thread which is deploying the job
        self.client_thread = self._setup_client_thread()

        # Signal handler
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _setup_client_thread(self):
        """
        Sets up the client threads.

        :returns: the thread object
        :rtype: :class:`threading.Thread`
        """
        thread = threading.Thread(target=self.run_clients)
        thread.daemon = True
        return thread

    def _signal_handler(self, signum, frame):
        """
        Handles signals sent to this process.

        :param signum: signal number as defined in the ``signal`` module
        :type signum: int
        :param frame: execution frame
        :type frame: frame object
        """
        log.info('Received signal %s ' % signum)
        if signum == signal.SIGTERM:
            for node in self.nodes.values():
                node.close()
            self.server.server_close()

    def node_for(self, setting):
        """
        Find the Node for a given :class:`~penchy.jobs.job.NodeSetting`.

        :param setting: setting identifier to receive Node for
        :type setting: string
        :returns: the Node
        :rtype: :class:`~penchy.node.Node`
        """
        return self.nodes[setting.identifier]

    def composition_for(self, hashcode):
        """
        Find the :class:`~penchy.jobs.job.SystemComposition` for a given
        hashcode.

        :param hashcode: hashcode of the wanted composition
        :type hashcode: string
        :returns: the system composition
        :rtype: :class:`~penchy.jobs.job.SystemComposition`
        """
        for composition in self.job.compositions:
            if hashcode == composition.hash():
                return composition

        raise ValueError('Composition not found')

    def exp_rcv_data(self, hashcode, result):
        """
        Receive data from nodes.

        :param hashcode: the hashcode to identify the
                         :class:`~penchy.jobs.job.SystemComposition` by
        :type hashcode: string
        :param result: the result of the job
        :type result: dict
        """
        composition = self.composition_for(hashcode)

        with Server._rcv_lock:
            node = self.node_for(composition.node_setting)
            node.received(composition)
            self.results[composition] = result
            log.info('Received result. Waiting for %s more.' %
                    self.remaining_compositions)

    def exp_report_error(self, hashcode, reason=None):
        """
        Deal with client-side errors. Call this for each
        composition for which a job failed.

        :param hashcode: the hashcode to identify the
                         :class:`~penchy.jobs.job.SystemComposition`
        :type hashcode: string
        :type reason: reason for the error; please note that this is
                      used when you'd like to display an error right
                      away without waiting for the server to fetch
                      the logs from the node.
        """
        composition = self.composition_for(hashcode)

        with Server._rcv_lock:
            node = self.node_for(composition.node_setting)
            node.received(composition)

        if reason:
            node.log.error(reason)

    def exp_set_timeout(self, hashcode, timeout):
        """
        Sets the timeout for the node identified by
        ``hashcode`` to ``timeout``

        :param hashcode: hashcode for composition
        :type hashcode: string
        :param timeout: timeout in seconds
        :type timeout: int
        """
        composition = self.composition_for(hashcode)
        with Server._rcv_lock:
            if hashcode in self.timers:
                self.timers[hashcode].cancel()
            if timeout > 0:
                self.timers[hashcode] = threading.Timer(timeout,
                        lambda: self._on_timeout(hashcode))
                self.timers[hashcode].start()
        log.debug('Timeout set to %s for %s' % (timeout, composition))

    def _on_timeout(self, hashcode):
        """
        Called when a timeout occurs for the node identified
        by ``hashcode``.

        :param hashcode: hashcode of the node
        :type hashcode: string
        """
        composition = self.composition_for(hashcode)
        node = self.node_for(composition.node_setting)
        with node.connection_required():
            node.kill_composition()
        log.error('%s timed out.' % self.composition_for(hashcode))

    @property
    def received_all_results(self):
        """
        Indicates wheter we have received results for *all*
        :class:`~penchy.jobs.job.SystemComposition`.
        """
        return all([n.received_all_results for n in self.nodes.values()])

    @property
    def remaining_compositions(self):
        """
        Number of composition we are still waiting for.
        """
        return sum([len(n.expected) for n in self.nodes.values()])

    def run_clients(self):
        """
        Run the client on all nodes.
        """
        with nested(make_bootstrap_pom(), make_bootstrap_client()) \
                as (pom, bclient):
            for node in self.nodes.values():
                with node.connection_required():
                    for upload in self.uploads:
                        node.put(*upload)
                    node.put(pom.name, 'bootstrap.pom')
                    node.put(bclient.name, 'penchy_bootstrap')

                    node.execute_penchy(' '.join(
                        self.bootstrap_args + [os.path.basename(self.job_file),
                            'config.py', node.setting.identifier]))

    def run(self):
        """
        Run the server component.
        """
        self.client_thread.start()
        try:
            while not self.received_all_results:
                self.server.handle_request()
            if self.results:
                self.run_pipeline()
            else:
                log.error('Received no results. Server-pipline was not executed.')
        except KeyboardInterrupt:
            log.warning('Keyboard Interrupt - Shutting down, please wait')
        finally:
            for node in self.nodes.values():
                node.close()

    def run_pipeline(self):
        """
        Called when we have received results for *all* compositions; starts
        the server-side pipeline.
        """
        log.info('Run server-side pipeline.')
        self.job.filename = self.job_file
        self.job.receive = lambda: self.results
        self.job.run_server_pipeline()
