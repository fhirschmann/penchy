"""
This module provides Hook elements that wrap the execution of
:class:`~penchy.jobs.elements.PipelineElement` and
:class:`~penchy.jobs.jvms.JVM`.

 .. moduleauthor:: Michael Markert <markert.michael@googlemail.com>

 :copyright: PenchY Developers 2011-2012, see AUTHORS
 :license: MIT License, see LICENSE
"""
from penchy.util import default


class BaseHook(object):
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


class Hook(BaseHook):
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
