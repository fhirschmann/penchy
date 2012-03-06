from penchy.compat import unittest
from penchy.statistics import *
from numpy.random import random_integers, random_sample
import numpy as np


class StatisticsTest(unittest.TestCase):
    def setUp(self):
        self.ints = random_integers(0, 50, 50)
        self.floats = random_sample(20)

    def test_average(self):
        self.assertAlmostEqual(average(self.ints), np.average(self.ints))
        self.assertAlmostEqual(average(self.floats), np.average(self.floats))

    def test_standard_deviation(self):
        self.assertAlmostEqual(standard_deviation(self.ints, ddof=1),
                               np.std(self.ints, ddof=1))
        self.assertAlmostEqual(standard_deviation(self.floats, ddof=1),
                               np.std(self.floats, ddof=1))

    def test_coefficient_of_variation(self):
        self.assertAlmostEqual(coefficient_of_variation(self.ints),
                               np.std(self.ints, ddof=1) / np.average(self.ints))
        self.assertAlmostEqual(coefficient_of_variation(self.floats),
                               np.std(self.floats, ddof=1) / np.average(self.floats))
