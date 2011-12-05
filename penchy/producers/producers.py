class Producer(object):
    """
    Base class for producers. __init__ must be called by inheriting classes.

    Inheriting classes must implement:
      - ``_run`` to run the producer, after running `out` attribute has to be
          set to path to produced output
      - ``configure(jvm, *options)``  to configure itself with the given jvm
          and options (must set configured to True if fully configured)
      - ``is_runable`` to state if producer can be run in current state
    """
    DEPENDENCIES = []
    def __init__(self):
        self._pre_hooks = []
        self._post_hooks = []
        self.configured = False

    def add_pre_hooks(self, *hooks):
        self._pre_hooks.extend(hooks)

    def add_post_hooks(self, *hooks):
        self._post_hooks.extend(hooks)

    def _run():
        raise NotImplementedError("_run must be implemented by actual producers")

    def is_runable():
        """
        :returns: if producer is runable
        :rtype: bool
        """
        raise NotImplementedError("runable must be implemented by actual producers")


    def configure(jvm, **options):
        """
        Configure producer with :param:`jvm` and :param:`options`.

        :param jvm: Instance of an JVM-Class
        :param options: keywords that are understood by ``JVM.get_commandline()``
        """
        raise NotImplementedError("configure must be implemented by actual producers")

    def run():
        """
        Run Producer
        """
        for hook in self._pre_hooks:
            hook()

        self.run_()

        for hook in self._post_hooks:
            hook()

class Dacapo(Producer):
    #TODO
    pass

class Tamiflex(Producer):
    #TODO
    pass

class HProf(Producer):
    #TODO
    pass
