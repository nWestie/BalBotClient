from tkinter.filedialog import askopenfilename
import numpy as np
from matplotlib import pyplot as plt

# plt.style.use('dark_background')


def main():
    filename: str = ''
    # filename = "C:/Users/westn/Documents/code/BalBotClient/logData/12-31-24/13.58.36-data.csv"
    if not filename:
        filename = askopenfilename(
            initialdir='logData', filetypes=[("CSV", ".csv")])
        if (not filename):
            exit()
    plt.style.use('dark_background')
    print('Opened: ')
    print(f'filename = "{filename}"')
    data = np.loadtxt(filename, dtype=np.float32,
                      delimiter=',', usecols=range(5))

    plot_voltage(data)


def plot_angles(data):
    plt.plot(data[:, 0], data[:, 3], c='b')
    plt.plot(data[:, 0], data[:, 4], c='g')
    plt.show()


def plot_voltage(data):
    # plt.plot(data[:, 0], data[:, 1], c='b')
    plt.plot(data[:, 0], data[:, 2], c='r')
    plt.show()


def plot_time_steps(data):
    t_diff = np.diff(data[:, 0]) * 1000
    plt.plot(data[1:, 0], t_diff, c='b')
    plt.show()


if __name__ == "__main__":
    main()
