#!/usr/bin/env python

# Das ganze soll aehnlich aussehen, wie in "da_capo_con_scala.pdf"
# Seite 6 (Figure 4 und 5).

import matplotlib.pyplot as plt

data = [
    ('sunflow', 'DaCapo', -0.001, 0.12, 0.025, -0.078),
    ('avrora', 'DaCapo', 0.01, 0.03, 0.025, -0.078),
    ('tradesoap', 'DaCapo', -0.06, 0.02, 0.025, -0.078),
    ('batik', 'DaCapo', -0.14, -0.04, 0.025, -0.078),
    ('tomcat', 'DaCapo', -0.13, -0.02, 0.025, -0.078),
    ('actors', 'ScalaBench', -0.08, -0.06, 0.025, -0.078),
    ('apparat', 'ScalaBench', 0.12, 0.03, 0.025, -0.078),
    ('factorie', 'ScalaBench', 0.1, 0.04, 0.025, -0.078),
    ('tmt', 'ScalaBench', 0.03, 0.012, 0.025, -0.078),
    ('kiama', 'ScalaBench', 0.05, 0.0, 0.025, -0.078)]

circles = [0, 0, 0, 0]
squares = [0, 0, 0, 0]
for i in range(4):
    circles[i] = [tuple_[i + 2] for tuple_ in data if tuple_[1] == 'DaCapo']
    squares[i] = [tuple_[i + 2] for tuple_ in data if tuple_[1] == 'DaCapo']

fig = plt.figure()

ax12 = fig.add_subplot(1,2,1)
for datum in data:
    ax12.text(datum[2], datum[3], datum[0])
#ax12.plot(circles[0], circles[1], 'o')
#ax12.plot(squares[0], squares[1], 's')

ax34 = fig.add_subplot(1,2,2)
for datum in data:
    ax34.text(datum[4], datum[5], datum[0])
#ax12.plot(circles[0], circles[1], 'o')
#ax12.plot(squares[0], squares[1], 's')

plt.show()
