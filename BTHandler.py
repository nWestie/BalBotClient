import math
import serial
from time import time, sleep
from threading import Thread, Event
from datetime import datetime
import csv
from os.path import isdir
from os import makedirs
from kivy.clock import Clock
import queue
from typing import Callable
from main import ControllerMain
from enum import Enum

ENABLE_LOGGING = True


class BTHandler:
    """Controls all communication between GUI and Robot\n
    The interface must provide/request the data it needs using set() and get() methods"""

    def __init__(self, port: str, gui: ControllerMain, loopSpeed: float = 1/20):
        self.action_queue: queue.Queue[Callable[..., None]] = queue.Queue()
        self._gui: ControllerMain = gui
        self._exit = Event()
        self._connected = False
        self._last_enable: bool = False
        self._port = port

        self._lastPacketTime = time()

        self._pidWriter = None
        self._dataWriter = None
        # Start handler Thread
        self._joy_send_interval = loopSpeed
        self._workerThread = Thread(target=self._btWorker)
        self._workerThread.start()

    def request_action(self, action: Callable):
        """Adds a command to the  BT worker's queue to send to the bot"""
        self.action_queue.put(action)

    def exit(self):
        """Notifys the worker thread to exit, and blocks until the thread closes."""
        self._exit.set()
        self._workerThread.join()
        sleep(.25)

    def print_console(self, msg: str):
        """Prints a message to the GUI console window"""
        Clock.schedule_once(lambda dt: self._gui.print_console(msg), -1)

    def _btWorker(self):
        """Control loop that runs in a seprate thread, handling bluetooth communications"""
        print("BT worker started")

        nextJoySend = time()+self._joy_send_interval
        while (True):
            # Get the next task from the queue and execute it (blocking call)
            if (self.action_queue.qsize() > 0):
                task = self.action_queue.get(block=False)
                task()  # Execute the function

            if (self._connected):
                self._recieveBtData()
                if (time() > nextJoySend):
                    self._send_joystick()
                    nextJoySend = time()+self._joy_send_interval

            # if main thread is exiting(window closed)
            if self._exit.is_set():
                self.disconnect()
                break
        print("bt worker closing")

    def _send(self, cmd):
        self.bt.write(f"{cmd}/".encode('ascii'))
        # print(f" - sending: {cmd}/")

    def _send_joystick(self) -> None:
        """Called regularly by the BT worker to send latest joystick position"""
        joy_speed, joy_turn = self._gui.get_joystick()
        updateStr = f"X{joy_turn:.0f},Y{joy_speed:.0f}"
        self._send(updateStr)

    def _req_PID(self):
        """Instructs the bot to send it's current PID values"""
        self._send("R")

    def send_trim(self, trim: float):
        self._send(f"T{trim:.2f}")

    def sendPID(self, kP: float, kI: float, kD: float, save=False) -> None:
        """MUST be called through request_action. Updates the PID values on the robot"""
        vals: str = f"{kP:.3f},{kI:.3f},{kD:.3f}"
        if (save):
            self._send("S"+vals)
        else:
            self._send("P"+vals)

    def set_enable(self, enable):
        """MUST be called through the request_action. Enables or disables the robot"""
        self._send("E" if enable else "D")

    def _recieveBtData(self):
        # Read BT Data
        numBytes = self.bt.in_waiting
        if numBytes > 0:
            self._btReceiveStr = self._btReceiveStr + \
                self.bt.read(numBytes).decode()
        # parse BT data
        data = self._btReceiveStr
        if len(data) == 0:
            return
        
        endInd = data.find("/")
        while endInd != -1:  # while there are more fully sent packets
            # Remove packet from datastream
            packet = data[0:endInd+1]
            data = data[endInd+1:]
            # print("Rx: ", packet)
            parseSwitch = {
                "U": self._parseU,
                "P": self._parseP,
                "M": self._parseM,
                "V": lambda packet: self.print_console(packet)
            }
            try:
                parser = parseSwitch.get(
                    packet[0], lambda __: self.print_console(f'bad-packet: {packet}'))
                parser(packet)
                self._lastPacketTime = time()
            except:
                self.print_console(f'ERR on packet: {packet}')
            endInd = data.find("/")
        self._btReceiveStr = data

    def _parseU(self, packet: str) -> None:
        packet = packet[1:-1]
        tokens = packet.split(",")
        dat = [float(val) for val in tokens]
        dat[0] /= 1000

        if (self._dataWriter):
            self._dataWriter.writerow(dat)

        Clock.schedule_once(lambda dt: self._gui.graph_gui_update(
            dat[0], dat[2], dat[3], dat[4]), -1)

        # Update GUI button if enable state changes
        bot_enabled = bool(dat[1])
        if bot_enabled != self._last_enable:
            Clock.schedule_once(
                lambda dt: self._gui.gui_update_en(bot_enabled), -1)
        self._last_enable = bot_enabled

    def _parseP(self, packet: str) -> None:
        packet = packet[1:-1]
        tokens = packet.split(",")
        pidVals = [float(val) for val in tokens]
        pidVals[0] /= 1000
        self.print_console(f"REC Bot PID")
        if (self._pidWriter):
            self._pidWriter.writerow(pidVals)

        Clock.schedule_once(lambda dt: self._gui.pid_gui_update(
            pidVals[1], pidVals[2], pidVals[3], True), -1)

    def _parseM(self, packet: str) -> None:
        """Print received message to GUI console"""
        Clock.schedule_once(
            lambda dt: self._gui.print_console("BOT> " + packet[1:-1]), -1)

    def connect(self) -> bool:
        """Opens BT Serial Connection - DO NOT CALL DIRECTLY, load into queue\n
        Returns true if connection was successful"""
        if (self._connected):
            return True
        try:
            self.print_console('connecting...')
            Clock.schedule_once(lambda dt: self._gui.connect_gui_update(
                False, True, "Connecting..."), -1)
            self.bt = serial.Serial(
                port=self._port, baudrate=38400, timeout=.25)
            Clock.schedule_once(lambda dt: self._gui.connect_gui_update(
                True, False, f"Connected on {self._port}"), -1)
            self.print_console('connected')

            if (ENABLE_LOGGING):
                self._open_logs()

            sleep(.1)
            self._btReceiveStr = ""
            self._lastPacketTime = time()
            self._connected = True
            self._req_PID()
            return True
        except:
            print("Bluetooth Connection Error")
            Clock.schedule_once(lambda dt: self._gui.connect_gui_update(
                False, False, "Could not connect"), -1)
            return False

    def disconnect(self) -> None:
        """Closes BT connection\n
        Returns true if disconnection is sucessful."""
        if (not self._connected):
            return
        try:
            print('disconnecting')
            Clock.schedule_once(lambda dt: self._gui.connect_gui_update(
                True, True, "Disconnecting..."), -1)

            # Always send a disable command to ensure bot shuts down
            self.set_enable(False)
            self.bt.close()

            print("Closed BT COM Port")
            Clock.schedule_once(lambda dt: self._gui.connect_gui_update(
                False, False, "Disconnected"), -1)

            if (ENABLE_LOGGING):
                self._close_logs()
            self._connected = False
        except:
            print("Error Closing BT connection")
            Clock.schedule_once(lambda dt: self._gui.connect_gui_update(
                False, False, "Error Disconnecting"), -1)

    def _open_logs(self)->None:
        dateStr = datetime.now().strftime('%m-%d-%y')
        timeStr = datetime.now().strftime('%H.%M.%S')
        folderName = '.\\logData\\'+dateStr
        if not isdir(folderName):
            makedirs(folderName)
        self._datFile = open(
            folderName+'\\'+timeStr+'-data.csv', 'w', newline='')
        self._pidFile = open(
            folderName+'\\'+timeStr+'-pid.csv', 'w', newline='')
        self._dataWriter = csv.writer(self._datFile)
        self._dataWriter.writerow(
            ["#Millis", "enable", "Voltage", "setAngle", "actAngle"])
        self._pidWriter = csv.writer(self._pidFile)

    def _close_logs(self)->None:
        try:
            self._datFile.close()
            self._pidFile.close()
            self._dataWriter = None
            self._pidWriter = None
        except:
            print('failed to close files')
        print(f"Data Saved as {self._datFile.name}")
