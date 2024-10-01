import serial
from time import time, sleep
from threading import Thread, Event
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
        self._exit = Event()
        self._connected = False
        self._enable = False
        self._port = port

        self._lastPacketTime = time()
        self._btReceiveStr = ""
        # Start handler Thread
        self._loopSpeed = loopSpeed
        self._workerThread = Thread(target=self._btWorker)
        self._workerThread.start()

    def request_action(self, action: Callable):
        self.action_queue.put(action)

    def set_enable(self, enable):
        """Should be called through the request_action"""
        # DECIDE: should this block until enable is acknowledged?
        print(f"sending enable: {enable}")
        # Clock.schedule_once(lambda dt:self._gui.enable_gui_update(not enable), 1.5)

    def exit(self):
        """Notifys the worker thread to exit, and blocks until the thread closes."""
        self._exit.set()
        self._workerThread.join()
        sleep(.25)

    def _btWorker(self):
        """Control loop that runs in a seprate thread, handling bluetooth communications"""
        print("BT worker started")
        dateStr = datetime.now().strftime('%m-%d-%y')
        timeStr = datetime.now().strftime('%H.%M.%S')
        folderName = '.\\logData\\'+dateStr
        if not isdir(folderName):
            makedirs(folderName)
        # TODO: this happens on connect?
        # self._datFile = open(
        #     folderName+'\\'+timeStr+'-data.csv', 'w', newline='')
        # self._pidFile = open(
        #     folderName+'\\'+timeStr+'-pid.csv', 'w', newline='')
        # self._dataWriter = writer(self._datFile)
        # self._pidWriter = writer(self._pidFile)
        # # TODO: this happens on disconnect?
        # try:
        #     self._datFile.close()
        #     self._pidFile.close()
        #     self._dataWriter = None
        #     self._pidWriter = None
        # except:
        #     print('failed to close files')
        # print("Data Saved as \"{}\\{}-*.csv\"".format(folderName, timeStr))

        nextSendTime = time()+self._loopSpeed
        while (True):
            # Get the next task from the queue and execute it (blocking call)
            if (self.action_queue.qsize() > 0):
                task = self.action_queue.get(timeout=1)
                # print(f"Running task: {task}")
                task()  # Execute the function
                # Logging rate is roughly 1.6 MB/hr

            if (self._connected):
                self._recieveBtData()

                if (time() > nextSendTime):
                    self._send_joystick()
                    nextSendTime = time()+self._loopSpeed

            # if main thread is exiting(window closed)
            if self._exit.is_set():
                self.disconnect()
                break
            # If connection seems to have timed out:
            # if self._connected and (time() - self._lastPacketTime) > .25:
            #     # attempt to disconnect and exit
            #     # TODO: TBD if this is the right way to handle this, or if it can be handled.
            #     print("connection lost, disconnecting")
            #     self.disconnect()
            #     break
        print("bt worker closing")

    def _send_joystick(self):
        pass
        joy_speed, joy_turn = self._gui.get_joystick()
        updateStr = "U{},{}/".format(joy_speed, joy_turn)
        # print(updateStr)
        # self.bt.write(updateStr.encode('ascii'))

    def send_trim(self, trim:float):
        print(f"Sending trim: {trim}")

    def sendPID(self, kP: float, kI: float, kD: float, save=False) -> None:
        if (save):
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
        if (self._connected):
            return
        try:
            print('connecting...')
            Clock.schedule_once(lambda dt: self._gui.connect_gui_update(
                False, True, "Connecting..."), -1)
            sleep(1.5)
            # self.bt = serial.Serial(
            #     port=self._port, baudrate=38400, timeout=.25)
            Clock.schedule_once(lambda dt: self._gui.connect_gui_update(
                True, False, f"Connected on {self._port}"), -1)
            print('connected')
            # TODO: remove - testing - disable pid lock after being connected for a bit
            Clock.schedule_once(
                lambda dt: self._gui.pid_gui_update(1, 2, 3, True), 3)

            self._lastPacketTime = time()
            self._connected = True
            return True
        except:
            print("Bluetooth Connection Error")
            self._connected = False
            Clock.schedule_once(lambda dt: self._gui.connect_gui_update(
                False, False, "Could not connect"), -1)
            return False

    def disconnect(self):
        """Closes BT connection\n
        Returns true if disconnection is sucessful."""
        if (not self._connected):
            return
        try:
            print('disconnecting')
            Clock.schedule_once(lambda dt: self._gui.connect_gui_update(
                True, True, "Disconnecting..."), -1)
            # self.bt.close()
            sleep(1)
            print("Closed BT COM Port")
            Clock.schedule_once(lambda dt: self._gui.connect_gui_update(
                False, False, "Disconnected"), -1)
            self._connected = False
        except:
            print("Error Closing BT connection")
            Clock.schedule_once(lambda dt: self._gui.connect_gui_update(
                False, False, "Error Disconnecting"), -1)
            self._connected = True
