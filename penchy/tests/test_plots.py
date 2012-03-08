import sys

from matplotlib.pyplot import xlim, ylim
from penchy.compat import unittest
from penchy.jobs.plots import Plot


class PlotTest(unittest.TestCase):
    def test_wrong_scale(self):
        with self.assertRaises(ValueError):
            Plot(filename='', x_scale='foo')
        with self.assertRaises(ValueError):
            Plot(filename='', y_scale='bar')

    def test_xlim(self):
        p = Plot(filename='', x_min=30)
        x_min, _ = xlim()
        self.assertEqual(x_min, 30)

        p = Plot(filename='', x_max=30)
        _, x_max = xlim()
        self.assertEqual(x_max, 30)

        p = Plot(filename='', x_min=30, x_max=40)
        x_min, x_max = xlim()
        self.assertEqual(x_max, 40)
        self.assertEqual(x_min, 30)

    def test_ylim(self):
        p = Plot(filename='', y_min=30)
        y_min, _ = ylim()
        self.assertEqual(y_min, 30)

        p = Plot(filename='', y_max=30)
        _, y_max = ylim()
        self.assertEqual(y_max, 30)

        p = Plot(filename='', y_min=30, y_max=40)
        y_min, y_max = ylim()
        self.assertEqual(y_max, 40)
        self.assertEqual(y_min, 30)
