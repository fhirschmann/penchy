"""
Executes benchmarks and filters generated data.

 .. moduleauthor:: Fabian Hirschmann <fabian@hirschm.net>

 :copyright: PenchY Developers 2011-2012, see AUTHORS
 :license: MIT License, see LICENSE
"""

import logging
import xmlrpclib
import signal

from penchy.util import load_config, load_job
from penchy.log import configure_logging


log = logging.getLogger(__name__)


class Client(object):
    """
    This class represents a client which executes a job
    and sends the results to the server.
    """
    def __init__(self, job, config, identifier, loglevel=logging.INFO):
        """
        :param args: arguments; this would normally be :class:`sys.argv`
        :type args: list
        """
        self.config = load_config(config)
        job_module = load_job(job)
        self.identifier = identifier
        configure_logging(loglevel)

        self.job = job_module.job
        self.job.filename = job_module.__file__

        self.proxy = xmlrpclib.ServerProxy("http://%s:%s/" % \
                (self.config.SERVER_HOST, self.config.SERVER_PORT))
        self._current_composition = None

        signal.signal(signal.SIGHUP, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """
        Handles signals sent to this process.

        :param signum: signal number as defined in the ``signal`` module
        :type signum: int
        :param frame: execution frame
        :type frame: frame object
        """
        log.info("Received signal %s" % signum)
        if signum == signal.SIGHUP:
            self.send_signal_to_composition(signal.SIGTERM)

    def send_signal_to_composition(self, signum):
        """
        Send signal ``signum`` to the composition which is currently running.

        :param signum: signal number as defined in the ``signal`` module
        :type signum: int
        """
        if self._current_composition:
            if self._current_composition.jvm.proc:
                if self._current_composition.jvm.proc.returncode is None:
                    self._current_composition.jvm.proc.send_signal(signum)

    def run(self):
        """
        Runs the client.
        """
        self.job.send = self.proxy.rcv_data

        for composition in self.job.compositions_for_node(self.identifier):
            try:
                self._current_composition = composition
                composition.set_timeout_function(self.proxy.set_timeout)
                self.job.run(composition)
                self._current_composition = None
            except Exception, err:
                log.exception('Exception occured while executing PenchY:')
                self.proxy.report_error(composition.hash(), err)
