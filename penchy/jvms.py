class JVM(object):
    """
    Base class for JVMs.

    Inheriting classes must implement:
      - ``get_commandline(*args, **options)`` to return a commandline that
          contains the options and runs the JVM
    """
    def get_commandline(self, *args, **options):
        """
        Return a commandline that can be executed by ``subprocess.Popen``.

        :param args: positional arguments, will be at the end
        :param options: options which should be presend in the command line
        :returns: commandline suitable for ``subprocess.Popen``
        :rtype: list
        """
        raise NotImplementedError("get_commandline has to be implemented by actual jvms")

class OpenJDK(JVM):
    #TODO
    pass

class J9(JVM):
    #TODO
    pass

class Jikes(JVM):
    #TODO
    pass

class SunClient(JVM):
    #TODO
    pass

class SunServer(JVM):
    #TODO
    pass
