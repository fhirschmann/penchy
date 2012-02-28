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
    BarPlot
    """
    inputs = Types(('x', list, str),
                   ('y', list, list, (int, float)))

    #FIXME: Better solution to handle args without repeating
    def __init__(self, colors, zlabels, error_bars=False, ecolor="red", horizontal=False, width=0.2, **kwarg):
        super(BarPlot, self).__init__(**kwarg)
        self.width = width
        self.colors = colors
        self.zlabels = zlabels
        self.horizontal = horizontal
        self.error_bars = error_bars

        if self.error_bars:
            self.ecolor = ecolor
            self.inputs = Types(('x', list, str),
                                ('y', list, list, (int, float)),
                                ('err', list, list, (int, float)))

    def _run(self, **kwargs):
        import numpy as np
        import matplotlib.pyplot as plt
        xs = kwargs['x']
        yss = kwargs['y']
        if self.error_bars:
            errs = zip(*kwargs['err'])
        ind = np.arange(len(xs))
        fig = plt.figure()
        plot = fig.add_subplot(1, 1, 1)
        bars, names, rects = [], [], []
        for i, ys, c, zlabel in zip(itertools.count(), zip(*yss), self.colors, self.zlabels):
            if self.horizontal:
                if self.error_bars:
                    rects.append(plot.barh(ind + self.width * i, ys, self.width,
                                           xerr=errs.pop(), ecolor=self.ecolor, color=c))
                else:
                    rects.append(plot.barh(ind + self.width * i, ys, self.width, color=c))
            else:
                if self.error_bars:
                    rects.append(plot.bar(ind + self.width * i, ys, self.width,
                                          yerr=errs.pop(), ecolor=self.ecolor, color=c))
                else:
                    rects.append(plot.bar(ind + self.width * i, ys, self.width, color=c))
            bars.append(rects[i][0])
            names.append(zlabel)
        plot.set_xlabel(self.xlabel)
        plot.set_ylabel(self.ylabel)
        plot.set_title(self.title)
        if self.horizontal:
            plot.set_yticks(ind + self.width)
            plot.set_yticklabels(xs)
        else:
            plot.set_xticks(ind + self.width)
            plot.set_xticklabels(xs)
        plot.legend(bars, names)
        plt.savefig(self.filename)


class ScatterPlot(Plot):
    """
    Scatterplot
    """
    inputs = Types(('x', list, (int, float)),
                   ('y', list, (int, float)),
                   ('z', list, str))

    #FIXME: Better solution to handle args without repeating
    #TODO: allow to draw circles and squares
    def __init__(self, **kwarg):
        super(ScatterPlot, self).__init__(**kwarg)

    def _run(self, **kwargs):
        import numpy as np
        import matplotlib.pyplot as plt
        xs = kwargs['x']
        ys = kwargs['y']
        zs = kwargs['z']
        fig = plt.figure()
        plot = fig.add_subplot(1, 1, 1)

        for x, y, z in zip(xs, ys, zs):
            plot.text(x, y, z, rotation=-45)
        plot.plot(xs, ys, 'o')

        plot.set_xlabel(self.xlabel)
        plot.set_ylabel(self.ylabel)
        plot.set_title(self.title)
        plt.savefig(self.filename)
