class Filter(object):
    """
    Base class for filters.

    Inheriting classes must implement:
      - ``run(*inputs)`` to run the filter on inputs which can be Producer or
          Filter instances, after executing self.out has to be set to the
          path of the produced output file
    """

    def run(self, inputs):
        """
        Run the filter on the inputs.

        :param inputs: Producer or Filter classes which output will be processed.
        """
        raise NotImplementedError("run must be implemented by filters")


class WallclockDacapo(Filter):
    #TODO
    pass


class HProf(Filter):
    #TODO
    pass
