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
        MavenDependency(
            # TODO: add dependencies (poa-2.0.0.0.jar)
        ),
    ))
    
    exports = ["reflection_log", "classfolder"]
    
    # TODO: do not set 'out' until the files are created
    out = {
        "reflection_log" : "out/refl.log", 
            # provides info/log about reflective calls
        "classfolder" : "out",
            # contains all classes of which objects were created (?)
          }
    
    def __init__(self):
        super(Tamiflex, self).__init__()
    
    @property
    def arguments(self):
        return ["-javaagent:poa-2.0.0.0.jar"]


class HProf(Tool):
    pass
