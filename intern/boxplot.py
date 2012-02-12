#!/usr/bin/env python

import matplotlib.pyplot as plt
import random

# generate random data
random.seed()
data = []
for i in range(3):
    set_ = []
    for j in range(30):
        set_.append(random.randint(1, 50))
    data.append(set_)
    set_ = []

# print data for comparison
for set_ in data:
    sorted_set = sorted(set_)
    length = len(sorted_set)
    print "data:", sorted_set
    print "upper quantile:", sorted_set[(length * 3) / 4]
    print "median:        ", sorted_set[length / 2]
    print "upper quantile:", sorted_set[length / 4]

fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)

ax.boxplot(data)

plt.show()
