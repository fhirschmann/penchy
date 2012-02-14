#!/usr/bin/env python

import numpy as np
import matplotlib.pyplot as plt

# equal lenght of datasets is assumed
openJDK = [21, 42, 32]
hotspot = [20, 43, 32]

ind = np.arange(len(openJDK))
width = 0.35

fig = plt.figure()
ax = fig.add_subplot(1,1,1)

rect1 = ax.bar(ind, openJDK, width, color='blue')
rect2 = ax.bar(ind+width, hotspot, width, color='red')

ax.set_ylabel('Wallclocktime')
ax.set_xlabel('Benchmarks')
ax.set_title('openJDK vs. hotspot')
ax.set_xticks(ind+width)
ax.set_xticklabels( ('fop', 'batik', 'eclipse') )
ax.legend( (rect1[0], rect2[0]) , ('openJDK', 'hotspot') )

plt.savefig("pylab_example.svg")
plt.show()
