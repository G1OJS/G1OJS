x1=0.230148
x2=0.147022
x3=0.160759
x4=0.165047
x5=0.194591
x6=0.225173
x7=0.30008
x8=0.406134
x9=0.571177
x10=1.107588

import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots()
x = np.arange(0,1,0.1)

ax.plot(x, np.array([x1,x2,x3,x4,x5,x6,x7,x8,x9,x10]))

print(np.exp(x)/np.exp(1))
ax.plot(x, 0.15+0.8*x**3+0.1*x**5)

plt.show()
