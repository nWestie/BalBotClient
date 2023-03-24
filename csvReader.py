from plyer import filechooser
import numpy as np
from matplotlib import pyplot as plt

# plt.style.use('dark_background')

fileName = ''
# fileName = "C:/Users/WESTNB21/Documents/Code/BalBotClient/logData/01-13-23/19.18.02-data.csv"

if not fileName:
    fileName = filechooser.open_file(
        path='logData',
        multiple=False,
        preview=False,
        filters=['*data.csv']
    )[0]
print('Opened: ')
print(fileName, '\n')
b = np.loadtxt(fileName, dtype=np.float32, delimiter=',', usecols=(0,2,3))
plt.plot(b[:,0],b[:,1])
plt.plot(b[:,0],b[:,2])
plt.show()
