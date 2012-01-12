"""
This module provides tools.
"""

import os.path

from penchy.jobs.elements import Tool
from penchy.maven import MavenDependency


class Tamiflex(Tool):
    """
    Currently only the play-out-agent is supported.

    The argument "-javaagent:poa-2.0.0.0.jar" effects that the following gets
    created during the execution of the workload:
    * a log file of all uses of the reflection-api
    * a folder of all classes that were used (including generated classes)
    """

    _POA = MavenDependency(
        'de.tu_darmstadt.penchy',
        'poa',
        '2.0.0.0',
        'http://mvn.0x0b.de',
        checksum='df4418bed92205e4f27135bbf077895bd4c8c652')

    DEPENDENCIES = set((_POA,))

    outputs = [('reflection_log', list, str),
               ('classfolder', list, str)]

    def __init__(self):
        super(Tamiflex, self).__init__()
        self.posthooks.append(self._after_execution)

    def _after_execution(self):
        # provides info/log about reflective calls
        out['reflection log'].append(os.path.abspath("out/refl.log"))
        # contains all classes of which objects were created (?)
        out['classfolder'].append(os.path.abspath("out"))

    def check(self):
        # some jmv's might not support java.lang.instrument
        pass

    @property
    def arguments(self):
        return ["-javaagent:%s" % __class__._POA.filename]


class HProf(Tool):
    """
    HProf must be called with exactly one option. Valid
    options can be obtained with the command::

       java -agentlib:hprof=help

    After execution a file with the full hprof output
    is exported.
    """

    # hprof has no dependencies, because it is included
    # in the hotspot jvm.
    DEPENDENCIES = set()

    outputs = [('java_hprof_txt', list, str)]

    def __init__(self, option):
        """
        :param option: the argument for hprof
        """
        super(HProf, self).__init__()
        self.posthooks.append(self._after_execution)
        self.option = option

    def _after_execution(self):
        # Provides the full hprof output
        out['java_hprof_txt'].append(os.path.abspath("java.hprof.txt"))
        # FIXME: Should stdout be included?

    def check(self):
        # Only Hotspot supports/includes hprof
        # FIXME: Check this in a reliable way.
        pass

    @property
    def arguments(self):
        # We use -agentlib:hprof because -Xrunhprof is
        # deprecated and will be removed in a future release
        # of the hotspot jvm.
        # FIXME: If javac is executed, the argument has to
        # be prefixed with -J
        return ["-agentlib:hprof=%s" % self.option]
