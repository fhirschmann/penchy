#!/usr/bin/env python

# Das ganze soll aehnlich aussehen, wie in "da_capo_con_scala.pdf"
# Seite 6 (Figure 4 und 5).
#
# TODO: Irgendwie ist es unelegant, wenn die Punkte und die
# Beschriftungen so unabhaengig voneinander sind.
# Vielleicht kann man auch dirket so etwas, wie
# "beschriftete Punkte" setzen.

import matplotlib.pyplot as plt

data = [
    ('sunflow', 'DaCapo', -0.001, 0.12, 0.025, -0.078),
    ('avrora', 'DaCapo', 0.01, 0.07, 0.018, 0.042),
    ('tradesoap', 'DaCapo', -0.06, 0.02, -0.004, 0.02),
    ('batik', 'DaCapo', -0.14, -0.04, 0.008, -0.018),
    ('tomcat', 'DaCapo', -0.13, -0.02, 0.0, -0.018),
    ('actors', 'ScalaBench', -0.08, -0.06, 0.028, -0.03),
    ('apparat', 'ScalaBench', 0.12, 0.03, -0.057, -0.02),
    ('factorie', 'ScalaBench', 0.1, 0.04, 0.05, -0.01),
    ('tmt', 'ScalaBench', 0.03, 0.012, -0.02, -0.038),
    ('kiama', 'ScalaBench', 0.05, 0.0, 0.02, 0.01)]

circles = [0] * 4
squares = [0] * 4
for i in range(4):
    circles[i] = [tuple_[i + 2] for tuple_ in data
        if tuple_[1] == 'ScalaBench']
    squares[i] = [tuple_[i + 2] for tuple_ in data
        if tuple_[1] == 'DaCapo']

fig = plt.figure()

ax12 = fig.add_subplot(1, 2, 1)
ax12.set_autoscale_on(False)
ax12.set_xbound(-0.17, 0.15)
ax12.set_ybound(-0.1, 0.15)
ax12.set_aspect(1/ax12.get_data_ratio())
for datum in data:
    ax12.text(datum[2], datum[3], datum[0],
        rotation=-45,
        horizontalalignment='left',
        verticalalignment='top',
        size="small")
ax12.plot(circles[0], circles[1], 'o')
ax12.plot(squares[0], squares[1], 's')

ax34 = fig.add_subplot(1, 2, 2)
ax34.set_autoscale_on(False)
ax34.set_xbound(-0.062, 0.06)
ax34.set_ybound(-0.083, 0.06)
ax34.set_aspect(1/ax34.get_data_ratio())
for datum in data:
    ax34.text(datum[4], datum[5], datum[0],
        rotation=-45,
        horizontalalignment='left',
        verticalalignment='top',
        size="small")
ax34.plot(circles[2], circles[3], 'o')
ax34.plot(squares[2], squares[3], 's')

plt.show()
