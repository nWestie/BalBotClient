import serial
from time import time, sleep
from threading import Thread, Lock
from datetime import datetime
from csv import writer


class BTHandler:
    """Controls all communication between GUI and Robot\n
    The interface must provide/request the data it needs using set() and get() methods"""

    def __init__(self, port: str, loopSpeed=1/20):
        self.lock = Lock()
        # Lock required when reading/writing to any of these variables
        self._requestConnect = False
        self._connected = False
        self._connectionStatus = ''
        self._requestExit = False
        self._dataSave = None
        self._toController = {
            'logs': [],
            'p': -1,
            'i': -1,
            'd': -1,
            'PIDenable': False,
            'isEnabled': False,
            'messages': []
        }
        self._fromController = {
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
        # Lock not needed for these, only used by worker thread
        self._port = port
        self._btRecieveStr = ""
        # Start handler Thread
        self.loopSpeed = loopSpeed
        self.workerThread = Thread(target=self._btWorker)
        self.workerThread.start()

    def getMany(self, *args):
        retVals = {}
        with self.lock:
            for key in args:
                if key in self._toController.keys():
                    retVals[key] = self._toController[key]
        return retVals

    def get(self, arg):
        with self.lock:
            if arg in self._toController.keys():
                return self._toController[arg]

    def set(self, **kwargs):
        with self.lock:
            for key, val in kwargs.items():
                if key in self._fromController.keys():
                    self._fromController[key] = val

    def clearLists(self, *args):
        if len(args) == 0:
            args = ['messages', 'logs']
        with self.lock:
            for listName in args:
                if listName in self._toController.keys():
                    self._toController[listName] = []

    def requestConnect(self, disconnect=False):
        """Notifies the worker thread to attempt to connect over bluetooth"""
        with self.lock:
            self._requestConnect = not disconnect

    def connectionStatus(self):
        with self.lock:
            status = self._connectionStatus
            self._connectionStatus = ''
            return status

    def exit(self):
        """Notifys the worker thread to exit, and blocks until the thread closes"""
        with self.lock:
            self._requestExit = True
        self.workerThread.join()

    def _btWorker(self):
        """Control loop that runs in a seprate thread, handling bluetooth communications"""
        print("BT worker started")
        fileName = datetime.now().strftime('%d-%m-%y_%H.%M.%S')
        fileName = 'logData\\'+fileName+'.csv'
        with open(fileName, 'w', newline='') as file:
            self._dataSave = writer(file)
            sendInterval = self.loopSpeed
            nextSendTime = time()+sendInterval
            while (True):
                with self.lock:
                    status = (self._requestConnect,
                              self._connected, self._requestExit)
                if status[0] and not status[1]:
                    self._connect()
                    continue
                elif status[1] and (status[2] or not status[0]):
                    self._disconnect()
                    continue
                if status[2]:
                    break
                if status[1]:  # if connected
                    self._recieveBtData()
                    self._sendBTData()

                # wait for time before looping
                sleeptime = nextSendTime-time()
                if (sleeptime > 0):  # sits here for 99.9% of time
                    # print(sleeptime/sendInterval)
                    sleep(sleeptime)
                nextSendTime = time()+sendInterval
        print("bt worker closing")
        print("Data Saved to \""+fileName+"\"")

    def _sendBTData(self):
        with self.lock:
            sData = self._fromController.copy()
            reqPID = not self._toController['PIDenable']
        updateStr = "U{},{},{:.2f},{}/".format(
            int(sData['speed']), int(sData['turn']), sData['trim'], 1 if sData['enable'] else 0)
        self.bt.write(updateStr.encode('ascii'))
        # print("Tx: ", updateStr)
        if reqPID:
            self.bt.write("R/".encode('ascii'))
        elif sData['sendPID']:
            pidStr = "P{},{},{}/".format(sData['p'], sData['i'], sData['d'])
            self.bt.write(pidStr.encode('ascii'))
            with self.lock:
                self._fromController['sendPID'] = False

        if sData['savePID']:
            self.bt.write("S/".encode('ascii'))
            with self.lock:
                self._fromController['savePID'] = False

    def _recieveBtData(self):
        # Read BT Data
        numBytes = self.bt.in_waiting
        if numBytes > 0:
            self._btRecieveStr = self._btRecieveStr + \
                self.bt.read(numBytes).decode()
        # parse BT data
        data = self._btRecieveStr
        if len(data) == 0:
            return
        if (not data[0].isalpha()):
            for i, c in enumerate(data):
                if c.isalpha():
                    data = data[i:]
                    break
        endInd = data.find("/")
        while endInd != -1:
            packet = data[0:endInd+1]
            data = data[endInd+1:]
            # print("Rx: ", packet)
            parseSwitch = {
                "U": self._parseU,
                "P": self._parseP,
                "M": self._parseM
            }
            parseSwitch.get(packet[0], lambda __: print('badpacket'))(packet)
            endInd = data.find("/")
        self._btRecieveStr = data

    def _parseU(self, packet: str):
        packet = packet[1:-1]
        tokens = packet.split(",")
        logPacket = [float(val) for val in tokens[0:3]]
        print(logPacket)
        if (self._dataSave):
            self._dataSave.writerow(logPacket)
        with self.lock:
            self._toController["logs"].append(logPacket)
            self._toController["isEnabled"] = bool(tokens[4])

    def _parseP(self, packet: str):
        packet = packet[1:-1]
        tokens = packet.split(",")
        with self.lock:
            self._toController['PIDenable'] = True
            self._toController["p"] = float(tokens[0])
            self._toController["i"] = float(tokens[1])
            self._toController["d"] = float(tokens[2])

    def _parseM(self, packet: str):
        with self.lock:
            self._toController["message"].append(packet[1:-1])

    def _connect(self):
        """Opens BT Serial Connection\n
        Returns true if connection was successful"""
        try:
            print('connecting...')
            self.bt = serial.Serial(port=self._port, baudrate=38400)
            print('connected')
            with self.lock:
                self._connected = True
                # will not keep trying until it succeeds, needs to be requested again
                self._connectionStatus = "Connected on "+self._port
        except:
            print("Bluetooth Connection Error")
            with self.lock:
                self._connected = False
                self._requestConnect = False
                self._connectionStatus = "Connection Error"

    def _disconnect(self):
        """Closes BT connection\n
        Returns true if disconnection is sucessful."""
        try:
            print('disconnecting')
            self.bt.close()
            print("Closed BT COM Port")
            with self.lock:
                self._connected = False
                self._requestConnect = False
                self._connectionStatus = "Disconnected"
                self._toController['PIDenable'] = False
        except:
            print("Error Closing BT connection")
            with self.lock:
                self._connected = True
                self._requestConnect = True
                self._connectionStatus = "Failed to Disconnect"
