#!/usr/bin/env python

import matplotlib.pyplot as plt

data = {
    'metric a':
        [22, 3, 2, 12, 3, 13, 11, 23, 21, 12, 23, 24],
    'metric b':
        [2, 12, 1, 2, 12, 21, 12, 3, 23, 32, 31, 21]
    }

fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)

legend_lines = []

for key in data.keys():
    legend_lines.append(ax.plot(data[key])[0])
    
ax.legend(legend_lines, data.keys())
plt.show()
