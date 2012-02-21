"""
This module provides JVMs to run programs.

 .. moduleauthor:: Michael Markert <markert.michael@googlemail.com>

 :copyright: PenchY Developers 2011-2012, see AUTHORS
 :license: MIT License, see LICENSE
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
from penchy.jobs.typecheck import Types


log = logging.getLogger(__name__)


class JVMNotConfiguredError(Exception):
    """
    Signals that a JVM is not sufficiently configured, i.e. a workload is
    missing or no classpath is set.
    """
    pass


class JVMExecutionError(Exception):
    """
    Signals that a execution of JVM failed, that is return non zero exit code.
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

    def __init__(self, path, options="", timeout_factor=1):
        """
        :param path: path to jvm executable relative to node's basepath
                     (can also be absolute)
        :param options: string of options that will be passed to JVM needs to be
                        properly escaped for a shell
        :type options: str
        """
        self.basepath = '/'
        self.timeout_factor = timeout_factor
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

        # jvm process
        self.proc = None

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
        if self._tool is not None:  # pragma: no cover
            log.warn("Overwriting Tool!")

        self._tool = tool

    @property
    def timeout(self):
        """
        Timeout of this JVM and the current workload.
        """
        if not self.workload:
            return 0
        return float(self.workload.timeout) * self.timeout_factor

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
            self.proc = subprocess.Popen(self.cmdline,
                    stdout=stdout, stderr=stderr)
            self.proc.communicate()

            self.workload.out['exit_code'].append(self.proc.returncode)
            self.workload.out['stdout'].append(stdout.name)
            self.workload.out['stderr'].append(stderr.name)
            if self.proc.returncode != 0:
                log.error('jvm execution failed, stderr:')
                stderr.seek(0)
                log.error(stderr.read())
                raise JVMExecutionError('non zero exit code: {0}'
                                        .format(exit_code))

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
        return "{2}({0}, '{1}')".format(self._path, self._user_options,
                                        self.__class__.__name__)

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
        update_hasher(hasher, ' '.join(self.workload.arguments)
                              if self.workload else '')
        update_hasher(hasher, self._user_options)
        return hasher.hexdigest()

    def information(self):
        """
        Collect and return information about the JVM.

        :returns: information about the JVM, the execution and the workload
        :rtype: dict
        """
        executable = os.path.join(self.basepath, self._path)
        cp = ['-classpath', os.pathsep.join(self._classpath)] if self._classpath  else []
        call = [executable] + cp
        p = subprocess.Popen(call + ['-version'], stderr=subprocess.PIPE)
        _, jvm = p.communicate()

        if self._workload is None:
            workload = ''
        elif not hasattr(self._workload, 'information_arguments'):
            workload = str(self._workload)
        else:
            p = subprocess.Popen(call + self._workload.information_arguments,
                                 stderr=subprocess.PIPE)
            _, workload = p.communicate()

        tool = str(self._tool) if self._tool else ''
        return {
            'jvm' : jvm,
            'cmdline' : ' '.join(self.cmdline),
            'workload' : workload,
            'tool' : tool
        }


class WrappedJVM(JVM, PipelineElement):  # pragma: no cover
    """
    This class is an abstract base class for a JVM that is wrapped by another
    Program.

    Inheriting classes must expose this attributes:

    - ``out`` a dictionary that maps logical names for output to actual.
    - ``outputs`` a :class:`~penchy.jobs.typecheck.Types` that describes the
                  output with a logical name and its types
    - ``cmdline`` that returns the cmdline suitable for :class:`subprocess.Popen`
    """

    def _run(self):
        raise ValueError('This is not your normal element, but a JVM')


class ValgrindJVM(WrappedJVM):
    """
    This class represents a JVM which is called by valgrind.

    Outputs:

    - ``valgrind_log``: paths to valgrind log file.
    """
    outputs = Types(('valgrind_log', list, str))
    arguments = []

    def __init__(self, path, options='',
                 valgrind_path='valgrind', valgrind_options=''):
        """
        :param path: path to jvm executable relative to node's basepath
                     (can also be absolute)
        :type path: str
        :param options: options for JVM (needs to be escaped for a shell)
        :type options: str
        :param valgrind_path: path to valgrind executable
        :type valgrind_path: str
        :param valgrind_options: options for valgrind (needs to be escaped for
                                 shell)
        :type valgrind_options: str
        """
        super(ValgrindJVM, self).__init__(path, options)
        PipelineElement.__init__(self)

        self.valgrind_path = valgrind_path
        self.valgrind_options = valgrind_options
        self.log_name = 'penchy-valgrind.log'

        self.posthooks.append(lambda: self.out['valgrind_log']
                              .append(os.path.abspath(self.log_name)))
        if hasattr(self, '_before_execution'):
            self.posthooks.append(self._before_execution)
        if hasattr(self, '_after_execution'):
            self.posthooks.append(self._after_execution)

    @property
    def cmdline(self):
        """
        The command line suitable for `subprocess.Popen` based on the current
        configuration.
        """
        cmd = [self.valgrind_path,
               '--log-file={0}'.format(self.log_name),
               '--smc-check=all',  # to support reflection, really slow
               '--trace-children=yes']
        if self.__class__.arguments:
            cmd.extend(self.__class__.arguments)
        cmd.extend(shlex.split(self.valgrind_options))
        return cmd + super(ValgrindJVM, self).cmdline

    def information(self):
        """
        Collect and return information about the JVM and Valgrind.

        :returns: information about the JVM, the execution and the workload
        :rtype: dict
        """
        d = super(ValgrindJVM, self).information()
        p = subprocess.Popen([self.valgrind_path, '--version'], stdout=subprocess.PIPE)
        valgrind, _ = p.communicate()
        d['valgrind'] = valgrind
        return d


class MemcheckJVM(ValgrindJVM):
    """
    This is a valgrind JVM that checks memory usage.

    Outputs:

    - ``valgrind_log``: paths to Memcheck log file.
    """
    arguments = ['--tool=memcheck']


class CacheGrindJVM(ValgrindJVM):
    """
    This is a valgrind JVM that checks cache usage.

    Outputs:

    - ``valgrind_log``: paths to Valgrind log file.
    - ``cachegrind``: paths to Cachegrind log file.
    """
    outputs = Types(('valgrind_log', list, str),
                    ('cachegrind', list, str))
    _cachegrind_file = 'penchy-cachegrind'
    arguments = ['--tool=cachegrind',
                 '--cachegrind-out-file={0}'.format(_cachegrind_file)]

    def _after_execution(self):
        self.out['cachegrind'] = os.path.abspath(CacheGrindJVM._cachegrind_file)


class CallGrindJVM(ValgrindJVM):
    """
    This is a valgrind JVM that generates a call graph.

    Outputs:

    - ``valgrind_log``: paths to Valgrind log file.
    - ``callgrind``: paths to Callgrind log file.
    """
    outputs = Types(('valgrind_log', list, str),
                    ('callgrind', list, str))
    _callgrind_file = 'penchy-callgrind'
    arguments = ['--tool=callgrind',
                 '--callgrind-out-file={0}'.format(_callgrind_file)]

    def _after_execution(self):
        self.out['callgrind'] = os.path.abspath(CallGrindJVM._callgrind_file)


class MassifJVM(ValgrindJVM):
    """
    This is a valgrind JVM that runs the heap profiler Massif.

    Outputs:

    - ``valgrind_log``: paths to Valgrind log file.
    """
    arguments = ['--tool=massif']


def _extract_classpath(options):
    """
    Return the jvm classpath from a sequence of option strings.

    :param options: sequence of jvm options to search
    :type options: list
    :returns: classpath as list of parts
    :rtype: list
    """
    prev = ''
    # a later classpath overwrites previous definitions so we have to search
    # from the end
    for option in reversed(options):
        if option in ('-cp', '-classpath'):
            # check prev for emptyness to prevent returning [''] if classpath is
            # only option
            return prev.split(os.pathsep) if prev else []
        prev = option

    return []
