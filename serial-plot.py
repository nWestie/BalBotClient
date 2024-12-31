import numpy as np
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
import serial
from functools import partial
import threading
import datetime
import os
from tkinter import filedialog
import time
from random import randint


############ PROGRAM CONFIG ################
openSerial = True  # If data should be read from the serial port
autoscale_for_serial = True  # If the graph should scale automatically
port = 'COM6'  # Change this to the appropriate port
baudrate = 38400  # Change this to match the baudrate of your device
############################################

plt.style.use('dark_background')

dataMutex = threading.Lock()
exit_event = threading.Event()
graphData = np.array([], dtype=np.uint16).reshape(0, 3)


def read_serial_data(exit_flag):
    global graphData

    print("starting serial thread")
    with serial.Serial(port, baudrate, timeout=1) as serialPort:
        while (not exit_flag.is_set()):
            dataLine = serialPort.read_until(b'/').decode()
            if (not dataLine[0].isalpha()):
                print(f"Skip: {dataLine}")
                continue
            dataLine = dataLine[1:-1]
            newData = np.fromstring(dataLine, dtype=np.float64, sep=",")
            line_dat = [newData[0]/1000, newData[3], newData[4]]
            with dataMutex:
                graphData = np.vstack([graphData, line_dat])
        print("closing serial")
    print("serial thread closing")


fig, ax = plt.subplots()
ax.set_xlabel('Red')
ax.set_ylabel('Green')
ax.set_title('Real-Time Plot of RGB Sensor Vals')
ax.set_xlim(0, 15)
targ_line, = ax.plot([], [], c='g')
set_line, = ax.plot([], [], c='b')


def update(frame):
    """Redraws the plot if using serial data"""
    global graphData

    with dataMutex:
        set_line.set_data(graphData[:, 0], graphData[:, 1])
        targ_line.set_data(graphData[:, 0], graphData[:, 2])
        if (openSerial and autoscale_for_serial and len(graphData) > 1):
            maxes = np.max(graphData, axis=0)
            mins = np.min(graphData, axis=0)
            # mins = [0, 0, 0]
            if (maxes[0] > 14.5):
                ax.set_xlim(maxes[0]-14.5, maxes[0]+0.5)
            ax.set_ylim(np.min(mins[1:])-5, np.max(maxes[1:])+5)
    return targ_line,


# Start data gathering threads.
thread = threading.Thread(target=read_serial_data, args=(exit_event,))

animation = FuncAnimation(fig, update, frames=10, interval=1000/20)
thread.start()

plt.show()

exit_event.set()
if thread:
    thread.join()
print("done")

dateStr = datetime.datetime.now().strftime('%m-%d-%y')
timeStr = datetime.datetime.now().strftime('%H-%M-%S')
folderName = '.\\serial_logs\\'+dateStr
if not os.path.isdir(folderName):
    os.makedirs(folderName)
savePath = os.path.join(
    folderName, f"{timeStr}-data.csv")

np.savetxt(savePath, np.unique(graphData, axis=0),
           delimiter=", ", fmt="%.2f")
print("Saved to", savePath)
