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

    Outputs:

    - ``reflection log``: log file of all uses of the reflection API
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
        self.posthooks.extend([
            lambda: self.out['reflection log'].append(os.path.abspath('out/refl.log')) ,
            lambda: self.out['classfolder'].append(os.path.abspath('out/')) ,
        ])

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

    Outputs:

    - ``hprof``: HProf output
    """

    DEPENDENCIES = set()

    outputs = Types(('hprof', list, str))

    def __init__(self, option):
        """
        :param option: the argument for hprof
        """
        super(HProf, self).__init__()
        # always the right file because a new dir is generated for each invocation
        self.posthooks.append(lambda: self.out['hprof']
                              .append(os.path.abspath('java.hprof.txt')))
        self.option = option

    @property
    def arguments(self):
        return ["-agentlib:hprof={0}".format(self.option)]
