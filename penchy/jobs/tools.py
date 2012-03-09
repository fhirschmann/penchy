"""
This module provides tools.

 .. moduleauthor:: Felix Mueller
 .. moduleauthor:: Pascal Wittmann

 :copyright: PenchY Developers 2011-2012, see AUTHORS
 :license: MIT License, see LICENSE
"""
import os.path

from penchy.jobs.elements import Tool
from penchy.jobs.hooks import Hook
from penchy.jobs.typecheck import Types
from penchy.maven import MavenDependency


class Tamiflex(Tool):
    """
    This tool implements the play-out agent of tamiflex. The play-out agent has no
    configuration options. For general usage information visit the
    `tamiflex homepage <http://code.google.com/p/tamiflex/>`_.

    Outputs:

    - ``reflection_log``: log file of all uses of the reflection API
    - ``classfolder``: folder of all classes that were used (including generated)
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
        self.hooks.extend([
            Hook(teardown=lambda: self.out['reflection_log']
                            .append(os.path.abspath('out/refl.log'))),
            Hook(teardown=lambda: self.out['classfolder']
                            .append(os.path.abspath('out/')))])

    @property
    def arguments(self):
        return ["-javaagent:%s" % Tamiflex._POA.filename]


class HProf(Tool):
    """
    This tool implements the hprof agent. Valid
    options can be obtained with the command::

       java -agentlib:hprof=help

    For example: The instruction::

       t = tools.HProf('heap=dump')

    extends the commandline of the jvm about::

       -agentlib:hprof=heap=dump

    Outputs:

    - ``hprof``: HProf output, i.e. the path to the java.hprof.txt file
    """

    DEPENDENCIES = set()

    outputs = Types(('hprof', list, str))

    def __init__(self, option):
        """
        :param option: the argument for hprof
        """
        super(HProf, self).__init__()
        # chooses always the right file because a new directory
        # is generated for each invocation
        self.hooks.append(Hook(teardown=lambda: self.out['hprof']
                                          .append(os.path.abspath('java.hprof.txt'))))
        self.option = option

    @property
    def arguments(self):
        return ["-agentlib:hprof={0}".format(self.option)]
