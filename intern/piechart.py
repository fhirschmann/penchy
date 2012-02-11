#!/usr/bin/env python

import matplotlib.pyplot as plt

input_ = [("abc", 200), ("def", 300), ("ghi", 200)]

fig = plt.figure(1, figsize=(6,6))

ax = fig.add_subplot(1,1,1)
ax.set_title('Kuchen!')

labels = [i[0] for i in input_]
values = [i[1] for i in input_]

ax.pie(values, labels=labels, autopct='%1.1f%%')

plt.show()
