from csv import reader
from plyer import filechooser

fileName = filechooser.open_file(
    path='logData',
    multiple=False,
    preview=False,
    filters=['*.csv']
    )[0]
print('Opened: ')
print(fileName,'\n')
with open(fileName, 'r') as file:
    inp = reader(file)
    for line in inp:
        nums = [float(num) for num in line]
        print(nums)