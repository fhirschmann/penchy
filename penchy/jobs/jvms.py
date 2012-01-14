"""
This module provides JVMs to run programs.
"""

import itertools
import os
import shlex
import subprocess
import logging
from tempfile import NamedTemporaryFile
from contextlib import nested

from penchy.jobs.elements import PipelineElement
from penchy.util import extract_classpath

log = logging.getLogger(__name__)


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
        if not self._tool:
            log.warn("Overwriting Tool!")

        self._tool = tool

    def add_to_cp(self, path):
        """
        Adds a path to the classpath.

        :param path: classpath to add
        :type path: string
        """
        if self._classpath:
            self._classpath += ":" + path
        else:
            self._classpath = path

    def run(self):
        """
        Run the jvm with the current configuration.
        """
        prehooks, posthooks = self._get_hooks()

        log.info("executing prehooks")
        for hook in prehooks:
            hook()

        log.info("executing {0}".format(self.cmdline))
        with nested(NamedTemporaryFile(delete=False, dir='.'),
                    NamedTemporaryFile(delete=False, dir='.')) \
            as (stderr, stdout):
            exit_code = subprocess.call(self.cmdline,
                                        stderr=stderr,
                                        stdout=stdout)

            self.workload.out['exit_code'].append(exit_code)
            self.workload.out['stdout'].append(stdout.name)
            self.workload.out['stderr'].append(stderr.name)

        log.info("executing posthooks")
        for hook in posthooks:
            hook()

    @property
    def cmdline(self):
        """
        The command line suitable for `subprocess.Popen` based on the current
        configuration.
        """
        executable = os.path.join(self.basepath, self._path)
        cp = ['-classpath', self._classpath] if self._classpath else []
        if self.tool:
            options = self._options + self.tool.arguments
        else:
            options = self._options
        args = self.workload.arguments if self.workload else []
        return [executable] + options + cp + args

    def _get_hooks(self):
        """
        Return hooks of jvm together with possible workload and tool hooks.
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


class WrappedJVM(JVM, PipelineElement):
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
