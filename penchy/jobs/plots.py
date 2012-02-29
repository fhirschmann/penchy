"""
This module provides plotting filters.

  .. moduleauthor:: Pascal Wittmann <mail@pascal-wittmann.de>

  :copyright: PenchY Developers 2011-2012, see AUTHORS
  :license: MIT License, see LICENSE
"""
import itertools

from penchy.jobs.elements import Filter
from penchy.jobs.typecheck import Types
from penchy.util import default, average


class Plot(Filter):
    """
    This is the base class for all plotting filters.
    """
    def __init__(self, filename, title="", xlabel="",
                 ylabel=""):
        super(Plot, self).__init__()
        self.filename = filename
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel


class BarPlot(Plot):
    """
    This class represents a barplot filter. It is possible:

    - to draw horizontal barplots
    - to display error bars
    """
    inputs = Types(('x', list, str),
                   ('y', list, list, (int, float)))

    def __init__(self, zlabels, colors=None, error_bars=False, ecolor="red", horizontal=False, width=0.2, *arg, **kwarg):
        super(BarPlot, self).__init__(*arg, **kwarg)
        self.width = width
        self.colors = colors
        self.zlabels = zlabels
        self.horizontal = horizontal
        self.error_bars = error_bars

        if self.colors is not None and len(colors) != len(zlabels):
            raise ValueError("The number of zlables and colors have to be equal.")

        if self.error_bars:
            self.ecolor = ecolor
            self.inputs = Types(('x', list, str),
                                ('y', list, list, (int, float)),
                                ('err', list, list, (int, float)))

    def _run(self, **kwargs):
        import numpy as np
        import matplotlib.pyplot as plt

        # Use gray shades if no colors are given
        if self.colors is None:
            step = float(1) / len(self.zlabels)
            self.colors = [str(n) for n in np.arange(0, 1, step)]

        xs = kwargs['x']
        yss = kwargs['y']
        if self.error_bars:
            errs = zip(*kwargs['err'])

        ind = np.arange(len(xs))
        fig = plt.figure()

        # Add the (only) subplot
        plot = fig.add_subplot(1, 1, 1)

        bars, names, rects = [], [], []
        for i, ys, c, zlabel in zip(itertools.count(), zip(*yss), self.colors, self.zlabels):
            # Draw the bars depending on the configuration
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
            # Save the bar identifier for assoziation wit zlabels
            bars.append(rects[i][0])
            names.append(zlabel)

        plot.set_xlabel(self.xlabel)
        plot.set_ylabel(self.ylabel)
        plot.set_title(self.title)

        # Display bar names
        if self.horizontal:
            plot.set_yticks(ind + self.width)
            plot.set_yticklabels(xs)
        else:
            plot.set_xticks(ind + self.width)
            plot.set_xticklabels(xs)

        # Draw the legend with zlabels
        plot.legend(bars, names)

        plt.savefig(self.filename)


class ScatterPlot(Plot):
    """
    Scatterplot
    """
    inputs = Types(('x', list, (int, float)),
                   ('y', list, (int, float)),
                   ('z', list, str))

    #TODO: allow to draw circles and squares
    def __init__(self, *arg, **kwarg):
        super(ScatterPlot, self).__init__(*arg, **kwarg)

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


class LinePlot(Plot):
    """
    Lineplot
    """
    inputs = Types(('x', list, list, (int, float)),
                   ('y', list, list, (int, float)),
                   ('z', list, str))

    def __init__(self, colors, *arg, **kwarg):
        super(LinePlot, self).__init__(*arg, **kwarg)
        self.colors = colors

    def _run(self, **kwargs):
        import numpy as np
        import matplotlib.pyplot as plt
        xs = kwargs['x']
        ys = kwargs['y']
        zs = kwargs['z']
        fig = plt.figure()
        plot = fig.add_subplot(1, 1, 1)

        lines = []
        for x, y, c in zip(xs, ys, self.colors):
            lines.append(plot.plot(x, y, c)[0])

        plot.legend(lines, zs)

        plot.set_xlabel(self.xlabel)
        plot.set_ylabel(self.ylabel)
        plot.set_title(self.title)
        plt.savefig(self.filename)
