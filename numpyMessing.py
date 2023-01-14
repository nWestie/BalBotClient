import matplotlib.pyplot as plt
import numpy as np

# plt.style.use('dark_background')

x = np.linspace(0, 2 * np.pi, 200)
y = np.sin(x)

fig, ax = plt.subplots()
ax.plot(x, y)
plt.show()