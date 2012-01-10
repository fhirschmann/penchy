"""
This module provides filters.
"""

import re
from itertools import izip
from pprint import pprint

from penchy.jobs.elements import Filter


class Tamiflex(Filter):
    pass


class HProf(Filter):
    pass


class DacapoHarness(Filter):
    """
    Filters output of a DaCapo Harness.

    Inputs:
    - ``stderr``:  List of Paths to stderror output files, or
                   list of file-like objects
    - ``exit_code``: List of program exit codes

    Exports:
    - ``failures``: failure count per invocation ([int])
    - ``times``: execution time per itertion per invocation ([[int]])
    - ``valid``: flag that indicates if execution was valid
    """
    inputs = set(('stderr', 'exit_code'))
    exports = set(('failures', 'times', 'valid'))
    TIME_RE = re.compile(
        r"""
        (?:completed\ warmup\ \d+|        # for iterations
        (?P<success>FAILED|PASSED))       # check if run failed or passed
        \ in\ (?P<time>\d+)\ msec         # time of execution
        """, re.VERBOSE)

    def _run(self, **kwargs):
        exit_codes = kwargs['exit_code']
        stderror = kwargs['stderr']

        for f, exit_code in izip(stderror, exit_codes):
            failures = 0
            times = []
            # not file-like
            if not hasattr(f, 'read'):
                with open(f) as fobj:
                    buf = fobj.read()
            else:
                buf = f.read()
            for match in DacapoHarness.TIME_RE.finditer(buf):
                success, time = match.groups()
                if success is not None and success == 'FAILED':
                    failures += 1
                times.append(int(time))

            self.out['failures'].append(failures)
            self.out['times'].append(times)
            self.out['valid'].append(exit_code == 0 and failures == 0)


class Send(Filter):
    pass


class Receive(Filter):
    pass


class Print(Filter):
    """
    Prints everything fed to it on stdout.
    """
    def run(self, **kwargs):
        pprint(kwargs)
