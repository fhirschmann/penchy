"""
This module provides plotting filters.
"""
import itertools

from penchy.jobs.elements import Filter
from penchy.jobs.typecheck import Types
from penchy.util import default, average


class Plot(Filter):
    def __init__(self, filename, title="", xlabel="",
                 ylabel=""):
        super(Plot, self).__init__()
        self.filename = filename
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel


class BarPlot(Plot):
    """
    A simple and static barplot.  Mainly for testing.
    """
    inputs = Types(('x', list, str), ('y', list, list))

    #FIXME: Better solution to handle args without repeating
    def __init__(self, colors=[], **kwarg):
        super(BarPlot, self).__init__(**kwarg)
        self.width = 0.2
        self.colors = colors

    def _run(self, **kwargs):
        import numpy as np
        import matplotlib.pyplot as plt
        xs = kwargs['x']
        yss = kwargs['y']
        ind = np.arange(len(xs))
        fig = plt.figure()
        plot = fig.add_subplot(1, 1, 1)
        bars, names, rects = [], [], []
        for i, ys, c in zip(itertools.count(), zip(*yss), self.colors):
            rects.append(plot.bar(ind + self.width * i, [average(y) for y in ys],
                                  self.width, color=c))
            bars.append(rects[i][0])
            names.append('Invocation {0}'.format(i + 1))
        plot.set_xlabel(self.xlabel)
        plot.set_ylabel(self.ylabel)
        plot.set_title(self.title)
        plot.set_xticks(ind + self.width)
        plot.set_xticklabels(xs)
        plot.legend(bars, names)
        plt.savefig(self.filename)
