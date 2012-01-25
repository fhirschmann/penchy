"""
This module provides JVMs to run programs.
"""
import itertools
import logging
import os
import shlex
import subprocess
from hashlib import sha1
from tempfile import NamedTemporaryFile

from penchy.compat import update_hasher, nested
from penchy.jobs.elements import PipelineElement


log = logging.getLogger(__name__)


class JVMNotConfiguredError(Exception):
    """
    Signals that a JVM is not sufficiently configured, i.e. a workload is
    missing or no classpath is set.
    """
    pass


class JVM(object):
    """
    This class represents a JVM.

    :attr:`jvm.prehooks` callables (e.g. functions or methods) that are executed
                         before execution
    :attr:`jvm.posthooks` callables (e.g. functions or methods) that are executed
                         after execution
    """

    def __init__(self, path, options=""):
        """
        :param path: path to jvm executable relative to node's basepath
                     (can also be absolute)
        :param options: string of options that will be passed to JVM needs to be
                        properly escaped for a shell
        :type options: str
        """
        self.basepath = '/'
        self._path = path
        # keep user_options for log messages and comparisons around
        self._user_options = options

        self._options = shlex.split(options)
        self._classpath = _extract_classpath(self._options)

        self.prehooks = []
        self.posthooks = []

        # for tools and workloads
        self._tool = None
        self._workload = None

    @property
    def workload(self):
        return self._workload

    @workload.setter
    def workload(self, workload):
        if self._workload is not None:  # pragma: no cover
            log.warn("Overwriting workload!")

        self._workload = workload

    @property
    def tool(self):
        return self._tool

    @tool.setter
    def tool(self, tool):
        if not self._tool:  # pragma: no cover
            log.warn("Overwriting Tool!")

        self._tool = tool

    def add_to_cp(self, path):
        """
        Adds a path to the classpath.

        :param path: classpath to add
        :type path: string
        """
        self._classpath.extend(path.split(os.pathsep))

    def run(self):
        """
        Run the JVM in the current configuration.

        :raises: :exc:`JVMNotConfiguredError` if no workload or classpath is set
        """
        prehooks, posthooks = self._get_hooks()

        if not self._classpath:
            log.error('No classpath configured')
            raise JVMNotConfiguredError('no classpath configured')

        if not self.workload:
            log.error('No workload configured')
            raise JVMNotConfiguredError('no workload configured')

        log.debug("executing prehooks")
        for hook in prehooks:
            hook()

        log.debug("executing {0}".format(self.cmdline))
        with nested(NamedTemporaryFile(delete=False, dir='.'),
                    NamedTemporaryFile(delete=False, dir='.')) \
            as (stderr, stdout):
            exit_code = subprocess.call(self.cmdline,
                                        stderr=stderr,
                                        stdout=stdout)

            self.workload.out['exit_code'].append(exit_code)
            self.workload.out['stdout'].append(stdout.name)
            self.workload.out['stderr'].append(stderr.name)

        log.debug("executing posthooks")
        for hook in posthooks:
            hook()

    @property
    def cmdline(self):
        """
        The command line suitable for `subprocess.Popen` based on the current
        configuration.
        """
        executable = os.path.join(self.basepath, self._path)
        cp = ['-classpath', os.pathsep.join(self._classpath)] if self._classpath \
             else []
        if self.tool:
            options = self._options + self.tool.arguments
        else:
            options = self._options
        args = self.workload.arguments if self.workload else []
        return [executable] + options + cp + args

    def _get_hooks(self):
        """
        Return hooks of jvm together with possible workload and tool hooks.

        :returns: hooks of configuration grouped as pre- and posthooks
        :rtype: tuple of :func:`itertools.chain`
        """
        if self.workload is None:
            workload_prehooks = []
            workload_posthooks = []
        else:
            workload_prehooks = self.workload.prehooks
            workload_posthooks = self.workload.posthooks

        if self.tool is None:
            tool_prehooks = []
            tool_posthooks = []
        else:
            tool_prehooks = self.tool.prehooks
            tool_posthooks = self.tool.posthooks

        prehooks = itertools.chain(self.prehooks, tool_prehooks,
                                   workload_prehooks)
        posthooks = itertools.chain(self.posthooks, tool_posthooks,
                                    workload_posthooks)
        return prehooks, posthooks

    def __eq__(self, other):
        try:
            return all((
                # executing the equal jvm
                self._path == other._path,
                # with equal options
                self._user_options == other._user_options,
                # check if both workloads or none is set
                (self.workload is None and other.workload is None
                 or self.workload and other.workload),
                # check if both tools or none is set
                (self.tool is None and other.tool is None
                 or self.tool and other.tool)))
        except AttributeError:
            log.exception('Comparing JVM to non-JVM: ')
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(hash(self._path) + hash(self._user_options))

    def __repr__(self):
        return 'JVM({0}, {1})'.format(self._path, self._user_options)

    def hash(self):
        """
        Return the sha1 hexdigest.

        Used for identifying :class:`SystemComposition` across server and
        client.

        :returns: sha1 hexdigest of instance
        :rtype: str
        """
        hasher = sha1()
        update_hasher(hasher, self._path)
        update_hasher(hasher, self._user_options)
        return hasher.hexdigest()


class WrappedJVM(JVM, PipelineElement):  # pragma: no cover
    """
    This class is an abstract base class for a JVM that is wrapped by another
    Program.

    Inheriting classes must expose this attributes:

      - ``out``: dictionary that maps logical output names to paths of output
        files
      - ``outputs``: set of logical outputs (valid keys for ``out``)
    """

    def __init__(self):
        """
        Inheriting classes must:

          - have compatible arguments with JVM.__init__
          - call JVM.__init__
        """
        raise NotImplementedError("must be implemented")

    def run(self):
        """
        Run with wrapping.
        """
        raise NotImplementedError("must be implemented")


class ValgrindJVM(WrappedJVM):
    """
    This class represents a JVM which is called by valgrind.
    """
    #TODO
    pass


def _extract_classpath(options):
    """
    Return the jvm classpath from a sequence of option strings.

    :param options: sequence of jvm options to search
    :type options: list
    :returns: classpath as list of parts
    :rtype: list
    """
    classpath = ''
    prev = ''
    # a later classpath overwrites previous definitions so we have to search
    # from the end
    for i, x in enumerate(reversed(options)):
        if x in ('-cp', '-classpath'):
            classpath = prev
            break
        prev = x

    return classpath.split(os.pathsep) if classpath else []
