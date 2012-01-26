import logging
import os
from functools import partial
from hashlib import sha1
from itertools import groupby, chain
from operator import attrgetter

from penchy.compat import update_hasher
from penchy.jobs.dependency import build_keys, edgesort
from penchy.jobs.elements import PipelineElement, SystemFilter
from penchy.jobs.filters import Receive
from penchy.maven import get_classpath, setup_dependencies
from penchy.util import tempdir, dict2string


log = logging.getLogger(__name__)


class NodeSetting(object):
    """
    This class represents a configuration of a node.
    """

    def __init__(self, host, ssh_port, username, path,
                 basepath, description="", password=None,
                 keyfile=None):
        """
        :param host: hostname (or IP) of node
        :type host: string
        :param ssh_port: port number of ssh server on node
        :type ssh_port: int
        :param username: login name for penchy on node
        :type username: string
        :param path: working directory on the node (this is where
                     the job will be uploaded to and where the
                     temporary files and directories will be created)
        :type path: string
        :param basepath: basepath for JVMs on this node
        :type basepath: string
        :param description: Textual description of node
        :type description: string
        :param password: this is either the password for a given username
                         or the passphrase to unlock the keyfile
        :type password: string
        :param keyfile: path to the ssh keyfile to use
        :type keyfile: string
        """
        self.host = host
        self.ssh_port = ssh_port
        self.username = username
        self.path = path
        self.basepath = basepath
        self.description = description
        self.password = password
        self.keyfile = keyfile

    @property
    def identifier(self):
        """
        A unique identifier for this node.
        """
        return self.host

    def __eq__(self, other):
        return isinstance(other, NodeSetting) and \
                self.identifier == other.identifier

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.identifier)

    def __str__(self):  # pragma: no cover
        return "<%s: %s>" % (self.__class__.__name__,
                dict2string(self.__dict__, ['host', 'ssh_port']))

    def hash(self):
        """
        Return the sha1 hexdigest.

        Used for identifying :class:`SystemComposition` across server and
        client.

        :returns: sha1 hexdigest of instance
        :rtype: str
        """
        hasher = sha1()
        update_hasher(hasher, self.identifier)
        return hasher.hexdigest()


class SystemComposition(object):
    """
    This class represents a combination of a :class:`JVM` and a
    :class:`NodeSetting`.

    A :class:`SystemComposition` is a unique identifier that groups the
    results of its execution for server consumation.
    """

    def __init__(self, jvm, node_setting, name=None):
        """
        """
        self.name = name if name is not None else "{0} @ {1}".format(jvm, node_setting)
        self.jvm = jvm
        self.node_setting = node_setting

    def __eq__(self, other):
        return self.jvm == other.jvm and self.node_setting == other.node_setting

    def __ne__(self, other):
        return self.jvm != other.jvm or self.node_setting != other.node_setting

    def __hash__(self):
        return hash(hash(self.jvm) + hash(self.node_setting))

    def __str__(self):  # pragma: no cover
        return self.name

    def hash(self):
        """
        Return the sha1 hexdigest.

        Used for identifying :class:`SystemComposition` across server and
        client.

        :returns: sha1 hexdigest of instance
        :rtype: str
        """
        hasher = sha1()
        update_hasher(hasher, self.jvm.hash())
        update_hasher(hasher, self.node_setting.hash())
        return hasher.hexdigest()


class Job(object):
    """
    Represents a job.

    #TODO: include spec of those funs (atm see _build_environment)
    ``job.send`` has to be set on client
    ``job.receive`` has to be set on server
    """

    def __init__(self, compositions,
                 client_flow, server_flow,
                 invocations=1):
        """
        :param compositions: :class:`SystemComposition` to execute jobs on
        :type compositions: List of :class:`SystemComposition`
                              or :class:`SystemComposition`
        :param client_flow: describes execution of the job on nodes
        :type client_flow: sequence of :class:`Edge`
        :param server_flow: describes the execution of the job on the server
        :type client_flow: sequence of :class:`Edge`
        :param invocations: number of times to run job on each configuration
        :type invocations: int
        """
        self.compositions = compositions if isinstance(compositions, list) \
                              else [compositions]
        self.client_flow = client_flow
        self.server_flow = server_flow
        self.invocations = invocations
        self.send = None
        self.receive = None

    def run(self, composition):
        """
        Run clientside Job.

        :param composition: composition to run.
        :type composition: :class:`SystemComposition`
        """
        # setup
        pomfile = os.path.join(composition.node_setting.path, 'pom.xml')
        setup_dependencies(pomfile, self._get_client_dependencies(composition))
        composition.jvm.add_to_cp(get_classpath(pomfile))

        # save send for restoring
        send = self.send
        # replace with one that knows how to identify the composition if it is set
        if self.send is not None:
            self.send = partial(self.send, composition.hash())

        composition.jvm.basepath = composition.node_setting.basepath

        starts = filter(bool, (composition.jvm.workload,
                               composition.jvm.tool))
        _, edge_order = edgesort(starts, self.client_flow)

        for i in range(1, self.invocations + 1):
            # TODO: Use os.time() or resource.getrusage()

            # measure cputime before
            with open('/proc/self/stat') as f:
                before = f.read().split()[13]  # utime is field 14
            log.debug('CPU time before invocation: {0}'.format(before))

            log.info('Run invocation {0}'.format(i))
            with tempdir(prefix='penchy-invocation{0}-'.format(i)):
                composition.jvm.run()

            # measure cputime after
            with open('/proc/self/stat') as f:
                after = f.read().split()[13]
            log.debug('CPU time after invocation: {0}, difference: '
                      '{1}'.format(after, int(after) - int(before)))

        log.info('Run pipeline')
        for sink, group in groupby(edge_order, attrgetter('sink')):
            kwargs = build_keys(group)
            if isinstance(sink, SystemFilter):
                kwargs['environment'] = self._build_environment()
            sink.run(**kwargs)

        # reset state of filters for running multiple configurations
        self._reset_client_pipeline()
        # restore send
        self.send = send

    def _get_client_dependencies(self, composition):
        """
        Return all clientside :class:`MavenDependency` of this job for a given
        :class:`SystemComposition`.

        :raises: :exc:`ValueError` if ``composition`` is not part of this job

        :param composition: composition to analyze.
        :type composition::class:`SystemComposition`
        :returns: Set of :class:`MavenDependency`.
        :rtype: set
        """
        if composition not in self.compositions:
            raise ValueError('composition not part of this job')

        deps = (e.DEPENDENCIES for e in self._get_client_elements(composition))
        return set(chain.from_iterable(deps))

    def _get_client_elements(self, composition=None):
        """
        Return the clientside element of this job.

        :param composition: composition to collect elements for, None for all
        :type composition: None or :class:`SystemComposition`
        :returns: all elements that are part of the clientside job.
        :rtype: set
        """
        compositions = self.compositions if composition is None else [composition]
        elements = chain((e.source for e in self.client_flow),
                         (e.sink for e in self.client_flow),
                         filter(bool, (c.jvm.workload for c in compositions)),
                         filter(bool, (c.jvm.tool for c in compositions)),
                         (c.jvm for c in compositions))

        return set(filter(lambda e: isinstance(e, PipelineElement),
                          elements))

    def _reset_client_pipeline(self):
        """
        Reset the clientside pipeline.
        """
        for e in self._get_client_elements():
            e.reset()

    def run_server_pipeline(self):
        """
        Run the serverside pipeline.

        :raise: :exc:`ValueError` if there is no
                :class:`~penchy.jobs.filters.Receive` in the serverside pipeline
        """
        starts = filter(lambda e: isinstance(e, Receive),
                        (e.source for e in self.server_flow))

        if not starts:
            log.error('There is no Receiver in the serverside flow. Aborting.')
            raise ValueError('There is no Receiver in the serverside flow')

        _, edge_order = edgesort(starts, self.server_flow)

        # all starts are receivers, run them with the environment
        for start in starts:
            start.run(environment=self._build_environment())

        # run other filters, here should be no system filters
        # TODO: maybe check for them and log?
        for sink, group in groupby(edge_order, attrgetter('sink')):
            kwargs = build_keys(group)
            sink.run(**kwargs)

    def _get_server_dependencies(self):
        """
        Return the serverside dependencies of the job.

        :returns: Set of :class:`MavenDependency`.
        :rtype: set
        """
        return set((element.DEPENDENCIES for element in self.server_flow))

    def _build_environment(self):
        """
        Return the environment for a :class:`SystemFilter`.

        Contains:
        - ``receive``: to get all data that has been received, takes no arguments
                       returns a dict with :class:`SystemComposition` as keys
        - ``send``: to send data to the server, takes one datum as argument
        - ``job``: this job

        :returns: environment for a SystemFilter
        :rtype: dict
        """
        # replace receive and send with dummy functions if not set to avoid
        # corner cases in pipeline
        receive = self.receive if self.receive is not None else lambda: {}
        send = self.send if self.send is not None else lambda data: None

        return dict(receive=receive,
                    send=send,
                    job=self)

    def compositions_for_node(self, identifier):
        """
        Return the compositions of this job that are to be run on the node
        that corresponds to ``identifier``.

        :param identifier: identifier for node.
        :type host: str
        :returns: :class:`SystemComposition` of job that run on host
        :rtype: list
        """
        return [c for c in self.compositions if c.node_setting.identifier == identifier]

    def check(self):
        """
        Check job for plausibility.

        :returns: if job is plausible, i.e. no failure is expected.
        :rtype: bool
        """
        # FIXME: implement me!
        pass
