import serial
from time import time, sleep
from threading import Thread, Lock
from datetime import datetime
from csv import writer
from os.path import isdir
from os import makedirs
from kivy.clock import Clock
import queue
from typing import Callable
from main import ControllerMain
# ENABLECODE = 213
# DISABLECODE = 226


class BTHandler:
    """Controls all communication between GUI and Robot\n
    The interface must provide/request the data it needs using set() and get() methods"""

    def __init__(self, port: str, gui: ControllerMain, loopSpeed: float = 1/20):
        self.action_queue: queue.Queue[Callable[..., None]] = queue.Queue()
        self._gui: ControllerMain = gui
        self._lock = Lock()
        self._connected = False
        self._requestExit = False

        # # Lock required when reading/writing to any of these variables
        # self._requestConnect = False
        # self._connectionStatus = ''
        # self._dataWriter = None
        self._enable = False
        # self._pendingEnable = False
        # self._toController = {
        #     'p': -1,
        #     'i': -1,
        #     'd': -1,
        #     'logs': [],
        #     'messages': [],
        #     'PIDenable': False,
        # }
        # self._fromController = {
        #     'p': -1,
        #     'i': -1,
        #     'd': -1,
        #     'speed': 0,
        #     'turn': 0,
        #     'trim': 0,
        #     'sendPID': False,
        #     'savePID': False,
        # }
        # Lock not needed for vars below, only used by worker thread
        self._port = port
        self._lastPacketTime = time()
        self._btReceiveStr = ""
        # Start handler Thread
        self._loopSpeed = loopSpeed
        self._workerThread = Thread(target=self._btWorker)
        self._workerThread.start()
    def request_action(self, action: Callable):
        self.action_queue.put(action)

    # def getMany(self, *args):
    #     retVals = {}
    #     with self._lock:
    #         for key in args:
    #             if key in self._toController.keys():
    #                 retVals[key] = self._toController[key]
    #     return retVals

    # def get(self, arg):
    #     with self._lock:
    #         if arg in self._toController.keys():
    #             return self._toController[arg]

    # def set(self, **kwargs):
    #     with self._lock:
    #         for key, val in kwargs.items():
    #             if key in self._fromController.keys():
    #                 self._fromController[key] = val

    # def clearLists(self, *args):
    #     if len(args) == 0:
    #         args = ['messages', 'logs']
    #     with self._lock:
    #         for listName in args:
    #             if listName in self._toController.keys():
    #                 self._toController[listName] = []

    def isEnabled(self):
        with self._lock:
            return self._enable

    def setEnable(self, enable):
        print(f"Enable: {enable}")
        with self._lock:
            self._enable = enable
            self._pendingEnable = True

    def requestConnect(self, disconnect=False):
        """Notifies the worker thread to attempt to connect/disconnect bluetooth"""
        with self._lock:
            self._requestConnect = not disconnect

    def connectionStatus(self):
        """Returns a string with new connection status, or empty string if no change"""
        with self._lock:
            status = self._connectionStatus
            self._connectionStatus = ''
            return status

    def exit(self):
        """Notifys the worker thread to exit, and blocks until the thread closes"""
        with self._lock:
            self._requestExit = True
        self._workerThread.join()
        sleep(.5)

    def _btWorker(self):
        """Control loop that runs in a seprate thread, handling bluetooth communications"""
        print("BT worker started")
        dateStr = datetime.now().strftime('%m-%d-%y')
        timeStr = datetime.now().strftime('%H.%M.%S')
        folderName = '.\\logData\\'+dateStr
        if not isdir(folderName):
            makedirs(folderName)

        sendInterval = self._loopSpeed
        nextSendTime = time()+sendInterval
        while (True):
            # Get the next task from the queue and execute it (blocking call)
            if(self.action_queue.qsize()>0):
                task = self.action_queue.get(timeout=1)  # Wait max 1 second for a task
                print(f"Running task: {task}")
                task()  # Execute the function
            # with self._lock:
            #     status = (self._requestConnect,
            #               self._connected, self._requestExit)
            # if status[0] and not status[1]:
            #     if self._connect():
            #         # Logging rate is roughly 1.6 MB/hr
            #         self._datFile = open(
            #             folderName+'\\'+timeStr+'-data.csv', 'w', newline='')
            #         self._pidFile = open(
            #             folderName+'\\'+timeStr+'-pid.csv', 'w', newline='')
            #         self._dataWriter = writer(self._datFile)
            #         # TODO: pid save doesn't seem to be working?
            #         self._pidWriter = writer(self._pidFile)
            #     continue
            # elif status[1] and (status[2] or not status[0]):
            #     self._disconnect()
            #     try:
            #         self._datFile.close()
            #         self._pidFile.close()
            #         self._dataWriter = None
            #         self._pidWriter = None
            #     except:
            #         print('failed to close files')
            #     print("Data Saved as \"{}\\{}-*.csv\"".format(folderName, timeStr))
            #     continue
            with self._lock:
                if self._requestExit:
                    break
            # if status[1]:  # if connected
            #     self._recieveBtData()
            #     self._sendBTData()

            #     if (time() - self._lastPacketTime) > .25:
            #         with self._lock:
            #             self._requestConnect = False
            #             self._connectionStatus = 'Error: Connection Lost'
            # wait for time before looping
            sleeptime = nextSendTime-time()
            if (sleeptime > 0):  # sits here for 99.9% of time
                # print(sleeptime/sendInterval)
                sleep(sleeptime)
            nextSendTime = time()+sendInterval
        print("bt worker closing")

    def _sendBTData(self):
        pass
        # with self._lock:
        #     sData = self._fromController.copy()
        #     reqPID = not self._toController['PIDenable']
        #     sendEnable = ENABLECODE if self._enable else DISABLECODE
        # updateStr = "U{},{},{:.2f},{}/".format(
        #     int(sData['speed']), int(sData['turn']), sData['trim'], sendEnable)
        # self.bt.write(updateStr.encode('ascii'))
        # if reqPID:
        #     self.bt.write("R/".encode('ascii'))
        # elif sData['sendPID']:
        #     pidStr = "P{},{},{}/".format(sData['p'], sData['i'], sData['d'])
        #     self.bt.write(pidStr.encode('ascii'))
        #     with self._lock:
        #         self._fromController['sendPID'] = False

        # if sData['savePID']:
        #     self.bt.write("S/".encode('ascii'))
        #     with self._lock:
        #         self._fromController['savePID'] = False
    def sendPID(self, kP: float, kI:float, kD:float, save = False)->None:
        if(save):
            print(f"Saving PID: {[kP, kI, kD]}")
        else:
            print(f"Sending PID: {[kP, kI, kD]}")

    def _recieveBtData(self):
        # Read BT Data
        # numBytes = self.bt.in_waiting
        # if numBytes > 0:
        #     self._btReceiveStr = self._btReceiveStr + \
        #         self.bt.read(numBytes).decode()
        # parse BT data
        data = self._btReceiveStr
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
                "M": self._parseM,
                "A": self._parseA
            }
            try:
                parseSwitch.get(
                    packet[0], lambda __: print('badpacket'))(packet)
                self._lastPacketTime = time()
            except:
                print('Bad Packet, ignoring')
            endInd = data.find("/")
        self._btReceiveStr = data

    def _parseU(self, packet: str):
        packet = packet[1:-1]
        tokens = packet.split(",")
        logPacket = [float(val) for val in tokens]
        logPacket[0] /= 1000
        logPacket[4] = int(logPacket[4])
        botReportEnable = bool(logPacket[4])
        if (self._dataWriter):
            self._dataWriter.writerow(logPacket)
        with self._lock:
            if not self._pendingEnable and not botReportEnable:
                self._enable = False
            self._toController["logs"].append(logPacket)

    def _parseP(self, packet: str):
        packet = packet[1:-1]
        tokens = packet.split(",")
        pidLogPacket = [float(val) for val in tokens]
        pidLogPacket[0] /= 1000
        print(pidLogPacket)
        if (self._pidWriter):
            self._pidWriter.writerow(pidLogPacket)

        with self._lock:
            self._toController['PIDenable'] = True
            self._toController["p"] = float(tokens[1])
            self._toController["i"] = float(tokens[2])
            self._toController["d"] = float(tokens[3])

    def _parseM(self, packet: str):
        with self._lock:
            self._toController["messages"].append(packet[1:-1])

    def _parseA(self, packet):
        print('enable confirmed')
        with self._lock:
            self._pendingEnable = False

    def connect(self):
        """Opens BT Serial Connection - DO NOT CALL DIRECTLY, load into queue\n
        Returns true if connection was successful"""
        try:
            print('connecting...')
            Clock.schedule_once(lambda dt :self._gui.connect_gui_update(False,True, "Connecting..."), -1)
            sleep(1.5)
            # self.bt = serial.Serial(
            #     port=self._port, baudrate=38400, timeout=.25)
            Clock.schedule_once(lambda dt :self._gui.connect_gui_update(True,False, f"Connected on {self._port}"), -1)
            print('connected')
            # TODO: remove - testing - disable pid lock after being connected for a bit
            Clock.schedule_once(lambda dt:self._gui.set_pid_status(1,2,3,True), 3)

            self._lastPacketTime = time()
            with self._lock:
                self._connected = True
            return True
        except:
            print("Bluetooth Connection Error")
            with self._lock:
                self._connected = False
            Clock.schedule_once(lambda dt :self._gui.connect_gui_update(False,False, "Could not connect"), -1)
            return False

    def disconnect(self):
        """Closes BT connection\n
        Returns true if disconnection is sucessful."""
        try:
            print('disconnecting')
            Clock.schedule_once(lambda dt :self._gui.connect_gui_update(True, True, "Disconnecting..."), -1)
            # self.bt.close()
            sleep(1)
            print("Closed BT COM Port")
            Clock.schedule_once(lambda dt :self._gui.connect_gui_update(False, False, "Disconnected"), -1)
            with self._lock:
                self._connected = False
        except:
            print("Error Closing BT connection")
            Clock.schedule_once(lambda dt :self._gui.connect_gui_update(False, False, "Error Disconnecting"), -1)
            with self._lock:
                self._connected = True