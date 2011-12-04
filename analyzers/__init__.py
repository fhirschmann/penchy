""" Package that harbors benchmark analyzers. """

from penchy.analyzers import dacapo

def get_analyzer(benchmark):
    """
    Return analyzer for :param:`benchmark`.

    :param benchmark: benchmark that will be analyzed
    :returns: function that analyzes the benchmark
    :rtype: function
    """
    if benchmark in dacapo.BENCHMARKS:
        return dacapo.dacapo_wallclock
