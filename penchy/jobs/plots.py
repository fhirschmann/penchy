"""
This module provides plotting filters.

  .. moduleauthor:: Pascal Wittmann <mail@pascal-wittmann.de>

  :copyright: PenchY Developers 2011-2012, see AUTHORS
  :license: MIT License, see LICENSE
"""
from __future__ import division

import itertools

from penchy.jobs.elements import Filter
from penchy.jobs.typecheck import Types
from penchy.jobs.hooks import Hook
from penchy.compat import path
from penchy import is_server
from colorsys import hsv_to_rgb

if is_server:
    import numpy as np
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm


class Plot(Filter):
    """
    This is the base class for all plotting filters.

    Notice: It is possible to set ``x_max`` < ``x_min`` and
    ``y_max`` < ``y_min``.
    """
    outputs = Types(('filename', path))

    def __init__(self, filename, title="", xlabel="", ylabel="",
                 x_max=None, x_min=None, y_max=None, y_min=None,
                 x_scale="linear", y_scale="linear",
                 grid=False, legend_position=None,
                 cmap='prism'):
        """
        :param filename: filename of the resulting svg image
        :type filename: string
        :param title: title of the plot
        :type title: string
        :param xlabel: x axis label
        :type xlabel: string
        :param ylabel: y axis label
        :type ylabel: string
        :param x_max: maximum value of the x axis
        :type x_max: int, float
        :param x_min: minimum value of the x axis
        :type x_min: int, float
        :param y_max: maximum value of the y axis
        :type y_max: int, float
        :param y_min: minimum value of the y axis
        :type y_min: int, float
        :param x_scale: scale of the x axis, either linear, log or symlog
        :type x_scale: string
        :param y_scale: scale of the y axis, either linear, log or symlog
        :type y_scale: string
        :param grid: show grid
        :type grid: bool
        :param legend_position: position of the legend (see ``matplotlib.legend.legend``)
        :type legend_position: string or integer
        :param cmap: colormap to use (see ``matplotlib.cm``)
        :type cmap: colormap
        """
        super(Plot, self).__init__()
        self.filename = filename
        self.out['filename'] = filename
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.legend_position = legend_position

        if is_server:
            self.cmap = cm.get_cmap(cmap)
            if not self.cmap:
                raise ValueError("Color map not found!")
            self.fig = plt.figure()
            # Add the (only) subplot
            self.plot = self.fig.add_subplot(1, 1, 1)

            # Set minimums and maximums of the axes
            if x_min is not None:
                self.plot.set_xlim(left=x_min)
            if x_max is not None:
                self.plot.set_xlim(right=x_max)
            if y_min is not None:
                self.plot.set_ylim(bottom=y_min)
            if y_max is not None:
                self.plot.set_ylim(top=y_max)

            # Set the scale of the axes
            if x_scale in ['linear', 'log', 'symlog']:
                self.plot.set_xscale(x_scale)
            else:
                raise ValueError("x_scale must be either 'linear', 'log',"
                                 " or 'symlog'")

            if y_scale in ['linear', 'log', 'symlog']:
                self.plot.set_yscale(y_scale)
            else:
                raise ValueError("y_scale must be either 'linear', 'log',"
                                 " or 'symlog'")
            # Set grid
            self.plot.grid(grid)

            # Set labels
            self.plot.set_xlabel(self.xlabel)
            self.plot.set_ylabel(self.ylabel)

            # Set title
            self.plot.set_title(self.title)

            #TODO: log where the plot is saved
            self.hooks.append(Hook(teardown=lambda: plt.savefig(self.filename)))


class BarPlot(Plot):
    """
    This class represents a barplot filter. It is possible:

    - to draw horizontal barplots (in that case inputs ``x`` and ``y`` swap)
    - to draw stacked barplots
    - to display error bars

    Inputs:

    - ``x``: Labels for the first dimension of ``y``
    - ``y``: 2d list of bar heights
    - ``z``: Labels for the second dimension of ``y``
    - ``err``: list of error values (only visible if ``error_bars`` is True)

    Outputs:

    - ``filename``: Filename of the generated image
    """

    def __init__(self, error_bars=False, ecolor="red",
                 horizontal=False, stacked=False, width=0.2, *arg, **kwarg):
        """
        :param error_bars: draw error bars
        :type error_bars: bool
        :param ecolor: color of the error bars
        :type ecolor: ``matplotlib.colors``
        :param horizontal: draw the diagram horizontal
        :type horizontal: bool
        :param stacked: draw a stacked barplot
        :type stacked: bool
        :param width: width of the bars
        :type width: float
        """
        super(BarPlot, self).__init__(*arg, **kwarg)
        self.width = width
        self.horizontal = horizontal
        self.error_bars = error_bars
        self.stacked = stacked

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

        ind = np.arange(len(xs))

        bars, rects, bottoms = [], [], ()
        for i, ys in enumerate(zip(*yss)):
            # Configure the plot function
            options = {'height': ys, 'width': self.width, 'color': self.cmap(i / len(yss))}

            if self.error_bars:
                if self.horizontal:
                    options['xerr'] = errs.pop()
                else:
                    options['yerr'] = errs.pop()
                options['ecolor'] = self.ecolor

            if self.stacked:
                if i > 0:
                    options['bottom'] = bottoms
                options['left'] = ind + self.width
            else:
                options['left'] = ind + self.width * i

            # Draw the bars
            if self.horizontal:
                rects.append(self.plot.barh(**options))
            else:
                rects.append(self.plot.bar(**options))

            if self.stacked:
                bottoms += bottoms + ys

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
        self.fig.legend(bars, zs, self.legend_position)


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

    Inputs:

    - ``x``: 2d list of x-values
    - ``y``: 2d list of y-values
    - ``z``: labels for the first dimension of ``x`` and ``y`` values
    - ``xerr``: list of error values (only visible if ``xerror_bars`` is True)
    - ``yerr``: list of error values (only visible if ``yerror_bars`` is True)

    Outputs:

    - ``filename``: Filename of the generated image
    """

    def __init__(self, xerror_bars=False, yerror_bars=False,
                 xecolor='red', yecolor='red', *arg, **kwarg):
        """
        :param xerror_bars: enable x error bars
        :type xerror_bars: bool
        :param yerror_bars: enable y error bars
        :type yerror_bars: bool
        :param xecolor: color of x error bars
        :type xecolor: ``matplotlib.color``
        :param yecolor: color of y error bars
        :type yecolor: ``matplotlib.color``
        """
        super(LinePlot, self).__init__(*arg, **kwarg)
        self.xerror_bars = xerror_bars
        self.yerror_bars = yerror_bars
        self.xecolor = xecolor
        self.yecolor = yecolor

        input_types = [('x', list, list, (int, float)),
                       ('y', list, list, (int, float)),
                       ('z', list, str)]

        if xerror_bars:
            input_types.append(('xerr', list, list, (int, float)))
        if yerror_bars:
            input_types.append(('yerr', list, list, (int, float)))

        self.inputs = Types(*input_types)

    def _run(self, **kwargs):
        xs = kwargs['x']
        ys = kwargs['y']
        zs = kwargs['z']

        if self.xerror_bars:
            xerr = kwargs['xerr']
        if self.yerror_bars:
            yerr = kwargs['yerr']

        lines = []
        for i, x, y in zip(itertools.count(), xs, ys):
            lines.append(self.plot.plot(x, y, color=self.cmap(i / len(xs)))[0])
            if self.xerror_bars:
                self.plot.errorbar(x, y, xerr=xerr.pop(),
                                   ecolor=self.xecolor)
            if self.yerror_bars:
                self.plot.errorbar(x, y, yerr=yerr.pop(),
                                   ecolor=self.yecolor)

        self.fig.legend(lines, zs, self.legend_position)


class Histogram(Plot):
    """
    Histogram

    Inputs:

    - ``x``: list of values

    Outputs:

    - ``filename``: Filename of the generated image
    """
    inputs = Types(('x', list, (int, float)))

    def __init__(self, bins, normed=False, *arg, **kwargs):
        """
        :param bins: if ``bins`` is a number ``bins`` + 1 egdes are
                     drawn. Unequally spaced bins are supported by sequences.
        :type bins: integer or list integers
        :param normed: draw a normalized histogram
        :type normed: bool
        """
        super(Histogram, self).__init__(*arg, **kwargs)
        self.bins = bins
        self.normed = normed

    def _run(self, **kwargs):
        xs = kwargs['x']
        self.plot.hist(xs, bins=self.bins, normed=self.normed)
