#!/usr/bin/env python

import matplotlib.pyplot as plt

# Bedeutung der Grafik: 5 Elemente zwischen 1 und 7,
# 3 Elemente zwischen 7 und 13 und zwischen 19 und 26
# und 2 Elemente zwischen 26 und 32 (oder so aehnlich).
#
# TODO: Achsenbeschriftung (ticks) sollte besser zu den
# Balken passen

data = [2, 12, 1, 2, 12, 21, 12, 3, 23, 32, 31, 21, 3]
bins = 5

fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)

ax.hist(data, bins=bins)
    

plt.show()
