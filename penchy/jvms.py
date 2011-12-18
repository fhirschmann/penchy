"""
This module provides JVMs to run programs.
"""

import os
import shlex

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
        self._classpath = extract_classpath(self.options)
        self._tool_options = []
        self._payload_options = []

    def configure(self, *args):
        """
        Configure jvm options that allows `args` to run

        :param *args: :class:`Tool` or :class:`Workload` instances that should be
                      run.
        """
        #TODO
        pass

    def run(self):
        """
        Run the jvm with the current configuration.
        """
        #TODO
        pass

    @property
    def cmdline(self):
        """
        The command line suitable for `subprocess.Popen` based on the current
        configuration.
        """
        executable = os.path.join(self.basepath, self._path)
        cp = ['-classpath', self._classpath + ":" get_classpath()]
        return executable + self._options + cp


class WrappedJVM(JVM):
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
