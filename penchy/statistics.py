"""
This module provides common statistical functions.

 .. moduleauthor:: Pascal Wittmann <mail@pascal-wittmann.de>

 :copyright: PenchY Developers 2011-2012, see AUTHORS
 :license: MIT License, see LICENSE
"""
from __future__ import division

import math


def average(xs):
    """
    Average the numbers in ``xs``.

    :param xs: numbers to average
    :type xs: list of numbers
    :returns: averaged numbers
    :rtype: float
    """
    return sum(xs) / len(xs)


def standard_deviation(xs, ddof):
    """
    Computes the sample standard deviation of the samples ``xs``.

    :param xs: sample values
    :type xs: list of numbers
    :param ddof: Delta Degrees of Freedom (ddof): ``ddof``
    is substracted from the divisor.
    :type ddof: integer
    :returns: sample standard deviation
    :rtype: float
    """
    avg = average(xs)
    return math.sqrt(sum((x - avg) ** 2 for x in xs) / (len(xs) - ddof))


def coefficient_of_variation(xs):
    """
    Computes the coefficient of variation of the samples ``xs``,
    i.e. the standard deviation divided by the mean.

    :param xs: sample values
    :type xs: list of numbers
    :returns: coefficient of variation
    :rtype: float
    """
    return standard_deviation(xs, ddof=1) / average(xs)
