data = {
    'speed': 0,
    'turn': 0,
    'trim': 0,
    'p': -1,
    'i': -1,
    'd': -1,
    'sendPID': False,
    'savePID': False,
    'enable': False
}
def modData(**kwargs):
    for key, val in kwargs.items():
        if key in data.keys():
            data[key] = val
def getData(*args):
    retVals = {}
    for key in args:
        if key in data.keys():
            retVals[key] = data[key]
    return retVals

# modData(p=12,i=10,d=1)
# print(data)