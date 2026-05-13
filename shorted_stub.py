import numpy as np

f = 7.07
l = 0.66*40/4
vf = 0.66
wl = 300/f
bl = 2*np.pi*l/(wl*vf)
print(bl)

x = 50*np.tan(bl)

w = 2*np.pi*f*1e6
ind = x/w

print(x, ind/1e-6)
