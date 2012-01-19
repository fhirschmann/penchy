import logging
import os
from collections import namedtuple
from itertools import groupby, ifilter, chain
from operator import attrgetter

from penchy.jobs.dependency import build_keys, edgesort
from penchy.util import tempdir
from penchy.maven import get_classpath, setup_dependencies


log = logging.getLogger(__name__)


def makeJVMNodeConfiguration(jvm, node, name=None):
    """
    Return a JVMNodeConfiguration.

    :param jvm: :class:`JVM` to execute the job
    :param node: :class:`NodeConfiguration` to execute on
    :param name: decorative name of the configuration
    """

    name = name or "{0} @ {1}".format(jvm, node)

    return JVMNodeConfiguration(jvm, node, name)

JVMNodeConfiguration = namedtuple('JVMNodeConfiguration',
                                  ['jvm', 'node', 'name'])


class Job(object):
    """
    Represents a job.
    """

    def __init__(self, configurations,
                 client_flow, server_flow,
                 invocations=1):
        """
        :param configurations: :class:`JVMNodeConfiguration` to execute jobs on
        :type configurations: List of :class:`JVMNodeConfiguration`
                              or :class:`JVMNodeConfiguration`
        :param client_flow: describes execution of the job on nodes
        :type client_flow: sequence of :class:`Edge`
        :param server_flow: describes the execution of the job on the server
        :type client_flow: sequence of :class:`Edge`
        :param invocations: number of times to run job on each configuration
        :type invocations: int
        """
        self.configurations = configurations if isinstance(configurations, list) \
                              else [configurations]
        self.client_flow = client_flow
        self.server_flow = server_flow
        self.invocations = invocations

    def run(self, configuration):
        """
        Run clientside Job.

        :param configuration: :class:`JVMNodeConfiguration` to run.
        """
        # setup
        pomfile = os.path.join(configuration.node.path, 'pom.xml')
        setup_dependencies(pomfile, self._get_client_dependencies(configuration))
        configuration.jvm.add_to_cp(get_classpath(pomfile))

        configuration.jvm.basepath = configuration.node.basepath

        starts = ifilter(bool, (configuration.jvm.workload,
                                configuration.jvm.tool))
        _, edge_order = edgesort(starts, self.client_flow)

        for i in range(1, self.invocations + 1):
            log.info('Run invocation {0}'.format(i))
            with tempdir(prefix='penchy-invocation{0}-'.format(i)):
                configuration.jvm.run()
        for sink, group in groupby(edge_order, attrgetter('sink')):
            kwargs = build_keys(group)
            sink.run(**kwargs)

    def _get_client_dependencies(self, configuration):
        """
        Return all clientside :class:`MavenDependency` of this job for a given
        :class:`JVMNodeConfiguration`.

        Raises :class:`ValueError` if ``configuration`` is not part of this job.

        :param configuration: configuration to analyze.
        :type configuration::class:`JVMNodeConfiguration`
        :returns: Set of :class:`MavenDependency`.
        :rtype: set
        """
        if configuration not in self.configurations:
            raise ValueError('configuration not part of this job')

        deps = (element.DEPENDENCIES for element
                in chain((e.sink for e in self.client_flow),
                        # only include set workloads & tools
                        ifilter(bool, (configuration.jvm.workload,
                                       configuration.jvm.tool)))
                if element.DEPENDENCIES)

        return set(chain.from_iterable(deps))

    def _get_server_dependencies(self):
        """
        Return the serverside dependencies of the job.

        :returns: Set of :class:`MavenDependency`.
        :rtype: set
        """
        return set((element.DEPENDENCIES for element in self.server_flow))

    def configurations_for_node(self, identifier):
        """
        Return the configurations of this job that are to be run on the node
        that corresponds to ``identifier``.

        :param identifier: identifier for node.
        :type host: str
        :returns: :class:`JVMNodeConfiguration` of job that run on host
        :rtype: list
        """
        return [config for config in self.configurations if
                config.node.identifier == identifier]

    def check(self):
        """
        Check job for plausibility.

        :returns: if job is plausible, i.e. no failure is expected.
        :rtype: bool
        """
        # FIXME: implement me!
        pass
