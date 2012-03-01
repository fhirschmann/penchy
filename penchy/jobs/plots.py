"""
This module provides plotting filters.

  .. moduleauthor:: Pascal Wittmann <mail@pascal-wittmann.de>

  :copyright: PenchY Developers 2011-2012, see AUTHORS
  :license: MIT License, see LICENSE
"""
import itertools

from penchy.jobs.elements import Filter
from penchy.jobs.typecheck import Types
from penchy.jobs.hooks import Hook
from penchy.util import default, average
from penchy import is_server

if is_server:
    import numpy as np
    import matplotlib.pyplot as plt


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

        if is_server:
            self.fig = plt.figure()
            # Add the (only) subplot
            self.plot = self.fig.add_subplot(1, 1, 1)

            hooks = [lambda: self.plot.set_xlabel(self.xlabel),
                     lambda: self.plot.set_ylabel(self.ylabel),
                     lambda: self.plot.set_title(self.title),
                     lambda: plt.savefig(self.filename)]

            self.hooks.extend(Hook(teardown=f) for f in hooks)


class BarPlot(Plot):
    """
    This class represents a barplot filter. It is possible:

    - to draw horizontal barplots (in that case inputs ``x`` and ``y`` swap)
    - to display error bars

    Inputs:

    - ``x``: Labels for the first dimension of ``y``
    - ``y``: 2d list of bar heights
    - ``z``: Labels for the second dimension of ``y`
    """
    inputs = Types(('x', list, str),
                   ('y', list, list, (int, float)),
                   ('z', list, str))

    def __init__(self, colors=None, error_bars=False, ecolor="red", horizontal=False, width=0.2, *arg, **kwarg):
        super(BarPlot, self).__init__(*arg, **kwarg)
        self.width = width
        self.colors = colors
        self.horizontal = horizontal
        self.error_bars = error_bars

        input_types = [('z', list, str)]
        if self.horizontal:
            input_types.extend([('x', list, list, (int, float)),
                               ('y', list, str)])
        else:
            input_types.extend([('x', list, str),
                               ('y', list, list, (int, float))])

        if self.error_bars:
            self.ecolor = ecolor
            input_types.append(('err', list, list, (int, float)))

        self.inputs = Types(*input_types)

    def _run(self, **kwargs):
        # Swap inputs back on horizontal plots
        if self.horizontal:
            xs = kwargs['y']
            yss = kwargs['x']
        else:
            xs = kwargs['x']
            yss = kwargs['y']

        zs = kwargs['z']
        if self.error_bars:
            errs = zip(*kwargs['err'])

        # Use gray shades if no colors are given
        if self.colors is None:
            step = float(1) / len(zs)
            self.colors = [str(n) for n in np.arange(0, 1, step)]

        ind = np.arange(len(xs))

        bars, rects = [], []
        for i, ys, c in zip(itertools.count(), zip(*yss), self.colors):
            # Draw the bars depending on the configuration
            if self.horizontal:
                if self.error_bars:
                    rects.append(self.plot.barh(ind + self.width * i, ys, self.width,
                                           xerr=errs.pop(), ecolor=self.ecolor, color=c))
                else:
                    rects.append(self.plot.barh(ind + self.width * i, ys, self.width, color=c))
            else:
                if self.error_bars:
                    rects.append(self.plot.bar(ind + self.width * i, ys, self.width,
                                          yerr=errs.pop(), ecolor=self.ecolor, color=c))
                else:
                    rects.append(self.plot.bar(ind + self.width * i, ys, self.width, color=c))
            # Save the bar identifier for assoziation wit zlabels
            bars.append(rects[i][0])

        # Display bar names
        if self.horizontal:
            self.plot.set_yticks(ind + self.width)
            self.plot.set_yticklabels(xs)
        else:
            self.plot.set_xticks(ind + self.width)
            self.plot.set_xticklabels(xs)

        # Draw the legend with zlabels
        self.plot.legend(bars, zs)


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
        xs = kwargs['x']
        ys = kwargs['y']
        zs = kwargs['z']

        for x, y, z in zip(xs, ys, zs):
            self.plot.text(x, y, z, rotation=-45)
        self.plot.plot(xs, ys, 'o')


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
        xs = kwargs['x']
        ys = kwargs['y']
        zs = kwargs['z']

        lines = []
        for x, y, c in zip(xs, ys, self.colors):
            lines.append(self.plot.plot(x, y, c)[0])

        self.plot.legend(lines, zs)
