"""
This module provides tools.
"""

from penchy.jobs.elements import Tool


class Tamiflex(Tool):
    """
    Currently only the play-out-agent is supported.
    
    The argument "-javaagent:poa-2.0.0.0.jar" effects that the following get's
    created during the execution of the workload:
    * a log file of all uses of the reflection-api
    * a folder of all classes that were used (including generated classes)
    """
    
    DEPENDENCIES = set((
    #    MavenDependency(
    #        # TODO: add dependencies (poa-2.0.0.0.jar)
    #        'org.???',
    #        '???',
    #        '2.0.0.0?',
    #        'http://mvn.0x0b.de ... ?',
    #        filename='poa-2.0.0.0.jar',
    #        checksum='df4418bed92205e4f27135bbf077895bd4c8c652'
    #    ),
    ))
    
    exports = ["reflection_log", "classfolder"]
    
    def __init__(self):
        super(Tamiflex, self).__init__()
        self.out = {}
        self.posthooks.append(after_execution)
              
    def after_execution(self):
        if True:  # if successful:
            self.out = {
                "reflection_log" : "out/refl.log",
                    # provides info/log about reflective calls
                "classfolder" : "out"
                    # contains all classes of which objects were created (?)
            }   
    
    def check(self):
        # some jmv's might not support java.lang.instrument
        pass
    
    @property
    def arguments(self):
        return ["-javaagent:poa-2.0.0.0.jar"]


class HProf(Tool):
    pass
