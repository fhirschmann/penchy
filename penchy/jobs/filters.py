"""
This module provides filters.

Inputs are fed to filters via keywords in the ``run`` method.
Outputs are available via the ``out`` attribute.
"""

import logging
import re
from pprint import pprint

from penchy.jobs.elements import Filter, SystemFilter


log = logging.getLogger(__name__)


class WrongInputError(Exception):
    """
    Filter received input it was not expecting and cannot process.
    """
    pass


class Tamiflex(Filter):
    pass


class HProf(Filter):
    pass


class DacapoHarness(Filter):
    """
    Filters output of a DaCapo Harness.

    Inputs:

    - ``stderr``:  List of Paths to stderror output files
    - ``exit_code``: List of program exit codes

    Outputs:

    - ``failures``: failure count per invocation ([int])
    - ``times``: execution time per itertion per invocation ([[int]])
    - ``valid``: flag that indicates if execution was valid
    """
    inputs = [('stderr', list, str),
              ('exit_code', list, int)]

    outputs = [('failures', list, int, int),
               ('times', list, list, int),
               ('valid', list, bool)]

    _TIME_RE = re.compile(
        r"""
        (?:completed\ warmup\ \d+|        # for iterations
        (?P<success>FAILED|PASSED))       # check if run failed or passed
        \ in\ (?P<time>\d+)\ msec         # time of execution
        """, re.VERBOSE)

    _VALIDITY_RE = re.compile(r'^\n?={5} DaCapo .*?={5}\n={5} DaCapo')

    def _run(self, **kwargs):
        exit_codes = kwargs['exit_code']
        stderror = kwargs['stderr']

        for f, exit_code in zip(stderror, exit_codes):
            failures = 0
            times = []
            with open(f) as fobj:
                buf = fobj.read()

            if not self._VALIDITY_RE.search(buf):
                log.error('Received invalid input:\n{0}'.format(buf))
                raise WrongInputError('Received invalid input')

            for match in DacapoHarness._TIME_RE.finditer(buf):
                success, time = match.groups()
                if success is not None and success == 'FAILED':
                    failures += 1
                times.append(int(time))

            self.out['failures'].append(failures)
            self.out['times'].append(times)
            self.out['valid'].append(exit_code == 0 and failures == 0)


class Send(SystemFilter):
    """
    Send data to the server.

    Inputs:

    - ``environment``: see :meth:`Job._build_environment`
    - ``payload``: data to send
    """
    inputs = [('environment', dict),
              ('payload', object)]

    def _run(self, **kwargs):
        send = kwargs['environment']['send']
        send(kwargs['payload'])


class Receive(SystemFilter):
    """
    Makes received data available for the serverside pipeline.

    Inputs:

    - ``environment``: see :meth:`Job._build_environment`

    Outputs:

    - ``results``: dict that maps :class:`SystemComposition` to their results.
    """
    inputs = [('environment', dict)]
    outputs = [('results', dict)]

    def _run(self, **kwargs):
        receive = kwargs['environment']['receive']
        self.out['results'] = receive()


class Print(Filter):
    """
    Prints everything fed to it on stdout.
    """
    inputs = None

    def __init__(self, stream=None):
        """
        :param stream: stream to print to, defaults to sys.stdout
        :type stream: open :class:`file`
        """
        super(Print, self).__init__()

        self.stream = stream

    def _run(self, **kwargs):
        pprint(kwargs, stream=self.stream)


class Plot(Filter):
    pass


class Upload(Filter):
    pass


class Dump(SystemFilter):
    pass
