"""
This module provides tools.

 .. moduleauthor:: Felix Mueller
 .. moduleauthor:: Pascal Wittmann

 :copyright: PenchY Developers 2011-2012, see AUTHORS
 :license: MIT License, see LICENSE
"""
import os.path

from penchy.jobs.elements import Tool
from penchy.jobs.typecheck import Types
from penchy.maven import MavenDependency


class Tamiflex(Tool):
    """
    The Hotspot in at least version 1.6.0_29-b11 for 64-bit is currently
    unsupported.

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

    outputs = Types(('reflection_log', list, str),
                    ('classfolder', list, str))

    def __init__(self):
        super(Tamiflex, self).__init__()
        self.posthooks.append(self._after_execution)

    def _after_execution(self):
        # provides info/log about reflective calls
        self.out['reflection log'].append(os.path.abspath("out/refl.log"))
        # contains all classes of which objects were created (?)
        self.out['classfolder'].append(os.path.abspath("out"))

    def check(self):
        # some jmv's might not support java.lang.instrument
        pass

    @property
    def arguments(self):
        return ["-javaagent:%s" % Tamiflex._POA.filename]


class HProf(Tool):
    """
    HProf must be called with exactly one option. Valid
    options can be obtained with the command::

       java -agentlib:hprof=help

    For example: The instruction::

       t = tools.HProf('heap=dump')

    extends the commandline of the jvm about::

       -agentlib:hprof=heap=dump

    After execution a file with the full hprof output
    is exported.
    """

    # hprof has no dependencies, because it is included
    # in the hotspot jvm.
    DEPENDENCIES = set()

    outputs = Types(('hprof', list, str))

    def __init__(self, option):
        """
        :param option: the argument for hprof
        """
        super(HProf, self).__init__()
        self.posthooks.append(self._after_execution)
        self.option = option

    def _after_execution(self):
        # Provides the full hprof output
        # Note: This is always the right file, because every job
        # is started in a new directory.
        self.out['hprof'].append(os.path.abspath("java.hprof.txt"))

    def check(self):
        # TODO: check for arguments
        pass

    @property
    def arguments(self):
        # We use -agentlib:hprof because -Xrunhprof is
        # deprecated and will be removed in a future release
        # of the hotspot jvm.
        return ["-agentlib:hprof=%s" % self.option]
