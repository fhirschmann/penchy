"""
This module provides JVMs to run programs.
"""

import itertools
import os
import shlex
import subprocess

from penchy.jobs.elements import PipelineElement, Tool, Workload
from penchy.maven import get_classpath
from penchy.util import extract_classpath


class JVM(object):
    """
    This class represents a JVM.
    """

    def __init__(self, path, options=""):
        """
        :param path: path to jvm executable relative to basepath
        :param options: string of options that will be passed to jvm
        :type options: string
        """

        self.basepath = '/'
        self._path = path
        # keep user_options for user messages around
        self._user_options = options

        self._options = shlex.split(options)
        self._classpath = extract_classpath(self._options)

        self.prehooks = []
        self.posthooks = []

        # for tools and workloads
        self._tool_options = []
        self._temporary_prehooks = []
        self._temporary_posthooks = []
        self._current_workload = None

    def configure(self, *args):
        """
        Configure jvm options that allows `args` to run

        :param *args: :class:`Tool` or :class:`Workload` instances that should be
                      run.
        """
        for arg in args:
            if isinstance(arg, Workload):
                if self._current_workload is None:
                    self._current_workload = arg
                else:
                    # XXX: use error flags and wait for check?
                    raise ValueError("JVM can only execute one Workload")

            elif isinstance(arg, Tool):
                self._tool_options = arg.arguments
            else:
                # XXX: use error flags and wait for check?
                raise ValueError("JVM can only be configured by Workloads and"
                                 " Tools")
            self._temporary_prehooks.extend(arg.prehooks)
            self._temporary_posthooks.extend(arg.posthooks)


    def run(self):
        """
        Run the jvm with the current configuration.
        """
        for hook in itertools.chain(self.prehooks, self._temporary_prehooks):
            hook()

        # FIXME:add temp files for stdout and stderr
        self._current_workload.out['error code'] = subprocess.call(self.cmdline)

        for hook in itertools.chain(self.posthooks, self._temporary_posthooks):
            hook()

        # reset temporaries
        self._temporary_prehooks = list()
        self._temporary_posthooks = list()
        self._tool_options = list()
        self._current_workload = None

    @property
    def cmdline(self):
        """
        The command line suitable for `subprocess.Popen` based on the current
        configuration.
        """
        executable = os.path.join(self.basepath, self._path)
        cp = ['-classpath', self._classpath + ":" + get_classpath()]
        options = self._options + self._tool_options
        return [executable] + options + cp + self._current_workload.arguments


class WrappedJVM(JVM, PipelineElement):
    """
    This class is an abstract base class for a JVM that is wrapped by another
    Program.

    Inheriting classes must expose this attributes:

      - ``out``: dictionary that maps logical output names to paths of output
        files
      - ``exports``: set of logical outputs (valid keys for ``out``)
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
