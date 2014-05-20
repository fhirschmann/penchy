"""
This module provides Hook elements that wrap the execution of
:class:`~penchy.jobs.elements.PipelineElement` and
:class:`~penchy.jobs.jvms.JVM`.

 .. moduleauthor:: Michael Markert <markert.michael@googlemail.com>
 .. moduleauthor:: Fabian Hirschmann <fabian@hirschmann.email>

 :copyright: PenchY Developers 2011-2012, see AUTHORS
 :license: MIT License, see LICENSE
"""
from subprocess import Popen
import shlex

from penchy.util import default


class BaseHook(object):  # pragma: no cover
    """
    This is the interface that pipeline hooks have to provide.
    """
    def setup(self):
        """
        A setup method is executed before running a
        :class:`~penchy.jobs.elements.PipelineElement` or a
        :class:`~penchy.jobs.jvms.JVM`
        """
        pass

    def teardown(self):
        """
        A teardown method is executed after running a
        :class:`~penchy.jobs.elements.PipelineElement` or a
        :class:`~penchy.jobs.jvms.JVM`
        """
        pass


class Hook(BaseHook):  # pragma: no cover
    """
    This class wraps setup and teardown callables as a :class:`Hook`.
    """

    def __init__(self, setup=None, teardown=None):
        """
        :param setup: the callable executed as setup
        :type setup: callable or None
        :param teardown: the callable executed as teardown
        :type teardown: callable or None
        """
        super(Hook, self).__init__()
        self.setup = default(setup, lambda: None)
        self.teardown = default(teardown, lambda: None)

    def setup(self):
        """
        Call the passed ``setup`` callable.
        """
        self.setup()

    def teardown(self):
        """
        Call the passed ``teardown`` callable.
        """
        self.teardown()


class ExecuteHook(BaseHook):
    """
    Hook that executes an arbitary command in the setup phase.
    If the command is still running during teardown, it will
    be terminated.
    """
    def __init__(self, args):
        """
        :param args: sequence of program arguments,
                     see :class:`subprocess.Popen` for details
        :type args: string or sequence
        """
        super(ExecuteHook, self).__init__()
        self.args = args
        self.proc = None

    def setup(self):
        self.proc = Popen(shlex.split(self.args) if
                isinstance(self.args, str) else self.args)

    def teardown(self):
        self.proc.poll()
        if self.proc.returncode is None:
            self.proc.terminate()
            self.proc.wait()
