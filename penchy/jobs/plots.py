"""
This module provides plotting filters.

  .. moduleauthor:: Pascal Wittmann <mail@pascal-wittmann.de>

  :copyright: PenchY Developers 2011-2012, see AUTHORS
  :license: MIT License, see LICENSE
"""
from __future__ import division

import itertools
import logging

from penchy.jobs.elements import Filter
from penchy.jobs.typecheck import Types
from penchy.jobs.hooks import Hook
from penchy.compat import path
from penchy.util import unify
from penchy import is_server


log = logging.getLogger(__name__)

if is_server:
    import numpy as np
    from matplotlib import pyplot as plt
    from matplotlib import cm


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
        :param filename: filename of the resulting SVG image
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

            self.hooks.append(Hook(teardown=lambda: self._savefig(self.filename)))

    def _savefig(self, filename):
        """
        :param filename: location to save the plot
        :type filename: path
        """
        plt.savefig(filename)
        log.info("Plot is saved at {0}".format(filename))


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

            # Save the bar identifier for association wit zlabels
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
    This class represents a scatterplot filter. It is possible:

    - to draw a label for each point
    - to set the color for a group of points
    - to set the shape of a group of points

    If you use ``colors`` or ``markers`` you have to specifiy a ``legend``.

    Inputs:

    - ``x``: x coordinates of the points
    - ``y``: y coordinates of the points
    - ``labels``: list of labels for each point (only available if ``labels`` is True)
    - ``markers``: list of shapes for each point (only available if ``markers`` is True)
    - ``colors``: list of colors for each point (only available if ``colors`` is True)
    - ``legend``: list of strings describing the what the markers and colors stand for
                  (only avaibable if ``colors`` or ``markers`` is True)

    Valid colors can be obtained from ``matplotlib.colors`` and valid shapes from
    ``matplotlib.lines.line2D.set_marker``.

    Outputs:

    - ``filename``: Filename of the generated image
    """

    def __init__(self, labels=True, markers=False, colors=False, *arg, **kwarg):
        """
        :param labels: draw labels (default is True)
        :type labels: bool
        :param markers: draw different markers (default is False,
                        thus normal dots are drawn)
        :type markers: bool
        :param colors: draw different colors (default is False,
                       all dots are blue)
        :type colors: bool
        """
        super(ScatterPlot, self).__init__(*arg, **kwarg)
        self.labels = labels
        self.markers = markers
        self.colors = colors

        input_types = [('x', list, list, (int, float)),
                       ('y', list, list, (int, float))]

        if labels:
            input_types.append(('labels', list, str))
        if markers:
            input_types.append(('markers', list, str))
        if colors:
            input_types.append(('colors', list, str))
        if markers or colors:
            input_types.append(('legend', list, str))

        self.inputs = Types(*input_types)

    def _run(self, **kwargs):
        xss = kwargs['x']
        yss = kwargs['y']

        keys = []
        if self.markers:
            keys.append(kwargs['markers'])
            markers = unify(kwargs['markers'])
        if self.colors:
            keys.append(kwargs['colors'])
            colors = unify(kwargs['colors'])

        if self.labels:
            for xs, ys in zip(xss, yss):
                label = kwargs['labels'].pop()
                for x, y in zip(xs, ys):
                    self.plot.text(x, y, label, rotation=-45)

        if self.colors or self.markers:
            legend = kwargs['legend']
            keys = zip(*keys)
            x_values = []
            y_values = []
            colors = []
            markers = []
            print keys
            print legend
            keys, legend, xss, yss = zip(*sorted(zip(keys, legend, xss, yss), key=lambda x: x[0]))
            print legend
            for _, group in itertools.groupby(zip(keys, xss), lambda x: x[0]):
                xs = []
                for key, values in group:
                    xs.extend(values)
                    if self.colors:
                        colors.append(key[1])
                    if self.markers:
                        markers.append(key[0])

                x_values.append(xs)

            markers = unify(markers)
            colors = unify(markers)

            for _, group in itertools.groupby(zip(keys, yss), lambda x: x[0]):
                ys = []
                for _, values in group:
                    ys.extend(values)
                y_values.append(ys)

            xss = x_values
            yss = y_values

        handles = []
        for xs, ys in zip(xss, yss):
            options = dict()
            if self.colors:
                options['color'] = colors.pop()

            if self.markers:
                options['marker'] = markers.pop()
            else:
                options['marker'] = 'o'

            handles.append(self.plot.scatter(xs, ys, **options))

        if self.markers or self.colors:
            self.fig.legend(handles, legend, self.legend_position)


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
        :param bins: if ``bins`` is a number ``bins`` + 1 edges are
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
