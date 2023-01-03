import serial
import time
import threading

class BTHandler:
    def __init__(self, port: str):
        self.btDataStr = ""
        self.port = port
        self.btRecData = {
            "voltage": 0,
            "setAngle": 90,
            "actualAngle": 90,
            "p": 0,
            "i": 0,
            "d": 0,
            "message": ""
        }
        self.connected = False

    def connect(self):
        try:
            print('connecting...')
            self.bt = serial.Serial(port=self.port, baudrate=38400)
            self.connected = True
            print('connected')
        except:
            print("Bluetooth Connection Error")
            # if (self.bt):
            #     self.bt.close()
            #     del self.bt
            self.connected = False
        return self.connected

    def disconnect(self):
        try:
            print('disconnecting')
            self.bt.close()
            self.connected = False
            print("Closed BT COM Port")
            return True
        except:
            print("Error Closing BT connection")
            return False

    def parseBtData(self):
        data = self.btDataStr
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
            bt.btDataStr = data
            parseSwitch = {
                "U": self._parseU,
                "P": self._parseP,
                "M": self._parseM
            }
            parseSwitch.get(packet[0], lambda __: None)(packet)
            endInd = data.find("/")

    def _parseU(self, packet: str):
        packet = packet[1:-1]
        tokens = packet.split(",")
        self.btRecData["voltage"] = float(tokens[0])
        self.btRecData["setAngle"] = float(tokens[1])
        self.btRecData["actualAngle"] = float(tokens[2])

    def _parseP(self, packet: str):
        packet = packet[1:-1]
        tokens = packet.split(",")
        self.btRecData["p"] = float(tokens[0])
        self.btRecData["i"] = float(tokens[1])
        self.btRecData["d"] = float(tokens[2])

    def _parseM(self, packet: str):
        self.btRecData["message"] = packet[1:-1]

    def readBT(self):
        if (not self.connected):
            return
        numBytes = self.bt.in_waiting
        if numBytes > 0:
            self.btDataStr = self.btDataStr + self.bt.read(numBytes).decode()
    
if __name__ == "__main__":
    bt = BTHandler("COM8")
    # bt.btDataStr = "123.45/Mabcdefg/P23.45,12,45/U12.5,13.45,0.45/"
    while (not bt.connected):
        input("Press enter to attempt BT connection")
        print("connecting...")
        bt.connect()
    endTime = time.time()+20
    while time.time() < endTime:
        bt.readBT()
        print(bt.btRecData)
        time.sleep(1/10)

    del bt
