from tkinter.filedialog import askopenfilename
import numpy as np
from matplotlib import pyplot as plt

# plt.style.use('dark_background')

filename:str = ''
# fileName = "C:/Users/WESTNB21/Documents/Code/BalBotClient/logData/01-13-23/19.18.02-data.csv"

if not filename:
    filename = askopenfilename(initialdir='logData',filetypes=[("CSV", ".csv")])
    if(not filename):
        exit()

print('Opened: ')
print(filename, '\n')
b = np.loadtxt(filename, dtype=np.float32, delimiter=',', usecols=(0,3,4))
plt.plot(b[:,0],b[:,1])
plt.plot(b[:,0],b[:,2])
plt.show()
