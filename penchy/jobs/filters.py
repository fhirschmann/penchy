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


class Evaluation(Filter):
    """
    Filter to evaluate values with an evaluation function.

    You should set ``inputs`` and ``outputs`` or no checking will take place.
    If ``inputs`` is set to ``None``, will run evaluator on ``input``.
    """

    def __init__(self, evaluator, inputs=None, outputs=None):
        """
        :param evaluator: function that evaluates
        :type evaluator: function
        :param inputs: input type specification
        :type inputs: list
        :param outnputs: output type specification
        :type outnputs: list
        """
        super(Evaluation, self).__init__()
        self.evaluator = evaluator
        self.inputs = inputs
        self.outputs = outputs

    def _run(self, **kwargs):
        if self.inputs is None:
            if 'input' not in kwargs:
                raise ValueError('Evaluation inputs not set, expected input in arguments')
            else:
                args = {'input' : kwargs['input']}
        else:
            try:
                args = dict([(input_[0], kwargs[input_[0]]) for input_ in inputs])
            except KeyError:
                log.exception('Evaluator: expected arguments "{0}"'
                              ', got "{1}"'.format(', '.join(i[0] for i in self.inputs),
                                                   ', '.join(k for k in kwargs)))
                raise ValueError('Missing input')

        self.out = self.evaluator(**args)


class StatisticRuntimeEvaluation(Evaluation):
    """
    Filter to evaluate runtime statistically.
    """
    inputs = [('times', list, list, int)]
    outputs = [('averages', list, int),
               ('maximals', list, int),
               ('minimals', list, int),
               ('positive_deviations', list, int),
               ('negative_deviations', list, int)]

    def __init__(self):
        super(StatisticRuntimeEvaluation, self).__init__(evaluate_runtimes,
                                                         self.inputs,
                                                         self.outputs)


def evaluate_runtimes(times):
    """
    Return the

    - averages: average times of iteration
    - maximals: the max times
    - positive_deviations: greatest positive deviation
    - minimals: the min times
    - negative_deviations: greatest negative deviations

    per iteration of all times.

    :param times: runtimes of all iterations of all iterations
    :type invocation: n*m 2D list
    :returns: the metrics described above in their order
    :rtype: dict
    """
    grouped_by_iteration = [[invocation[i] for invocation in times]
                            for i in range(len(times[0]))]

    maxs = list(map(max, grouped_by_iteration))
    mins = list(map(min, grouped_by_iteration))
    avgs = list(map(lambda invocation: float(sum(invocation)) / len(invocation),
                    grouped_by_iteration))
    pos_deviations = [abs(max_ - avg) / avg for max_, avg in zip(maxs, avgs)]
    neg_deviations = [abs(min_ - avg) / avg for min_, avg in zip(mins, avgs)]

    return {'averages' : avgs,
            'maximals' : maxs,
            'minimals' : mins,
            'positive_deviations' : pos_deviations,
            'negative_deviations' : neg_deviations}


class Plot(Filter):
    pass


class Upload(Filter):
    pass


class Dump(SystemFilter):
    pass
