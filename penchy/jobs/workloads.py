"""
This module provides configured workloads.
"""

import logging
import shlex

from penchy.jobs.elements import Workload
from penchy.maven import MavenDependency


# TODO: we need a module that configures logging
log = logging.getLogger("Workload")


class Dacapo(Workload):
    """
    This class represents the workload for the `DaCapo Benchmark-Suite
    <http://dacapobench.org/>_.
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

    def __init__(self, benchmark, iterations=1,
                 benchmark_args='', harness_args=''):
        """
        :param benchmark: benchmark to execute
        :param iterations: Number of iterations in an invocation.
        :param benchmark_args: String of additional arguments for benchmark
        :param harness_args: String of additional arguments for harness
        """
        self.benchmark = benchmark
        self.iterations = iterations

        self.harness_args = harness_args
        self.benchmark_args = benchmark_args

        # XXX: call check here?

        # initialize output dictionary
        self.out = dict()

    @property
    def arguments(self):
        """
        The arguments to call the workload in the current configuration.
        """
        return ['Harness'] + \
               ['-n', self.iterations] + shlex.split(self.harness_args) + \
               [self.benchmark] + shlex.split(self.benchmark_args)

    def check(self):
        """
        Check if workload is valid. Will log errors.

        :returns: if workload is valid
        :rtype: bool
        """
        valid_benchmark = self.benchmark in self.__class__.BENCHMARKS
        if not valid_benchmark:
            log.critical("{0} is not a valid benchmark for {1}".format(
                self.benchmark, self.__class__.__name__))

        return all((valid_benchmark,))


class ScalaBench(Dacapo):
    """
    This class represents the workload for the `Scalabench Benchmark-Suite
    <http://scalabench.org/>_.
    """
    BENCHMARKS = set((# dacapo
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
