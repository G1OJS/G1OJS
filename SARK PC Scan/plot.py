import numpy as np
import matplotlib.pyplot as plt

with open("VDPHF.csv", "r") as f:
    lines = f.readlines()
lines = lines[2:]
x,y = [], []
for l in lines:
    ls = l.split(',')
    z = float(ls[1]) + 1j * float(ls[2])
    mg = np.abs(50-z)/np.abs(50+z)
    s = (1+mg)/(1-mg)
    x.append(float(ls[0]))
    y.append(s)


fig, ax = plt.subplots()
ax.plot(x,y)
ax.set_xlim(25,30)
ax.set_ylim(1,10)
plt.show()
