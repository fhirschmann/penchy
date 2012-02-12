#!/usr/bin/env python

import matplotlib.pyplot as plt
import random

# generate random data
names = ["aaa", "bbb", "ccc"]
random.seed()
data = []
for i in range(len(names)):
    set_ = []
    for j in range(30):
        set_.append(random.randint(1, 50))
    data.append(set_)

# print data for comparison
for set_ in data:
    sorted_set = sorted(set_)
    length = len(sorted_set)
    print "data:", sorted_set
    print "upper quantile:", sorted_set[(length * 3) / 4]
    print "median:        ", sorted_set[length / 2]
    print "lower quantile:", sorted_set[length / 4]

fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)

ax.boxplot(data)
ax.set_xticklabels(names)

plt.show()
