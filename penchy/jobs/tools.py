"""
This module provides tools.
"""

from penchy.jobs.elements import Tool


class Tamiflex(Tool):
    """
    Currently only the play-out-agent is supported.
    
    """
    DEPENDENCIES = set((
        MavenDependency(
            # TODO: add dependencies (poa-2.0.0.0.jar)
        ),
    ))
    
    exports = ["reflection_log", "classfolder"]
    
    # TODO: do not set 'out' until the files are created
    out = {
        "reflection" : "out/refl.log", 
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
