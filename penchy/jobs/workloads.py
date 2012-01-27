"""
This module provides configured workloads.
"""

import logging
import shlex

from penchy.jobs.elements import Workload
from penchy.maven import MavenDependency


log = logging.getLogger(__name__)


class Dacapo(Workload):
    """
    This class represents the workload for the `DaCapo Benchmark-Suite
    <http://dacapobench.org/>`_.
    """
    DEPENDENCIES = set((
        MavenDependency(
            'org.scalabench.benchmarks',
            'scala-benchmark-suite',
            '0.1.0-20110908.085753-2',
            'http://repo.scalabench.org/snapshots/',
            filename='scala-benchmark-suite-0.1.0-SNAPSHOT.jar',
            checksum='fb68895a6716cc5e77f62ed7992d027b1dbea355'
        ),
    ))

    BENCHMARKS = set((  'avrora'
                      , 'batik'
                      , 'eclipse'
                      , 'fop'
                      , 'h2'
                      , 'jython'
                      , 'luindex'
                      , 'lusearch'
                      , 'pmd'
                      , 'sunflow'
                      , 'tomcat'
                      , 'tradebeans'
                      , 'tradesoap'
                      , 'xalan'))

    OPTIONS = set(('-c',
                   '--callback',
                   '-C',
                   '--converge',
                   '--ignore-validation',
                   '-k',
                   '--thread-factor',
                   '--max-iterations',
                   '--no-digest-output',
                   '--no-pre-iteration-gc',
                   '--no-validation',
                   '--preserve',
                   '-r',
                   '--release-notes Print the release notes',
                   '-s',
                   '--size',
                   '--scratch-directory',
                   '-t',
                   '--thread-count',
                   '-v',
                   '--verbose',
                   '--validation-report',
                   '--variance',
                   '--window'))

    def __init__(self, benchmark, iterations=1, args=''):
        """
        :param benchmark: benchmark to execute
        :type benchmark: string
        :param iterations: Number of iterations in an invocation.
        :type iterations: int
        :param args: additional arguments for harness (shell escaped)
        :type args: string
        """
        super(Dacapo, self).__init__()

        self.benchmark = benchmark
        self.iterations = iterations

        self.args = args

    @property
    def arguments(self):
        """
        The arguments to call the workload in the current configuration.

        :returns: the arguments for executing
        :rtype: list
        """
        return ['Harness'] + \
               ['-n', str(self.iterations)] + shlex.split(self.args) + \
               [self.benchmark]

    def check(self):
        """
        Check if workload is valid. Will log errors.

        :returns: if workload is valid
        :rtype: bool
        """
        valid_benchmark = self.benchmark in self.__class__.BENCHMARKS
        if not valid_benchmark:
            log.critical("{0} is not a valid benchmark for {1}"
                         .format(self.benchmark, self.__class__.__name__))

        valid_arguments = True
        for arg in shlex.split(self.args):
            if arg.startswith('-'):
                if arg not in self.__class__.OPTIONS:
                    valid_arguments = False
                    log.critical("{0} is not a valid option for {1}"
                                 .format(arg, self.__class__.__name__))

        return all((valid_benchmark, valid_arguments))


class ScalaBench(Dacapo):
    """
    This class represents the workload for the `Scalabench Benchmark-Suite
    <http://scalabench.org/>`_.
    """
    BENCHMARKS = set((
        # dacapo
        'avrora'
        , 'batik'
        , 'eclipse'
        , 'fop'
        , 'h2'
        , 'jython'
        , 'luindex'
        , 'lusearch'
        , 'pmd'
        , 'sunflow'
        , 'tomcat'
        , 'tradebeans'
        , 'tradesoap'
        , 'xalan'
        # scalabench
        , 'actors'
        , 'apparat'
        , 'dummy'
        , 'factorie'
        , 'kiama'
        , 'scalac'
        , 'scaladoc'
        , 'scalap'
        , 'scalariform'
        , 'scalatest'
        , 'scalaxb'
        , 'specs'
        , 'tmt'))
