import serial
import time


class BTHandler:
    def __init__(self, port: str) -> None:
        self.btDataStr = ""
        self.btRecData = {
            "voltage": 0,
            "setAngle": 90,
            "actualAngle": 90,
            "p": 0,
            "i": 0,
            "d": 0,
            "message": ""
        }
        self.bt = serial.Serial(port=port, baudrate=38400)
        # for i in range(3):
        #     try:
        #     except:
        #         if i == 2:
        #             exit("Bluetooth Connection Failed, exiting...")
        #         print("Bluetooth Connection Error, retrying...")

    def readBT(self) -> None:
        numBytes = self.bt.in_waiting
        if numBytes > 0:
            self.btDataStr = self.btDataStr + self.bt.read(numBytes).decode()

    def parse(self):
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


def __del__(self):
    self.bt.close()
    print("closed BT COM Port")


if __name__ == "__main__":
    bt = BTHandler("COM8")
    # bt.btDataStr = "123.45/Mabcdefg/P23.45,12,45/U12.5,13.45,0.45/"

    endTime = time.time()+20
    while time.time() < endTime:
        bt.readBT()
        bt.parse()
        print(bt.btRecData)
        time.sleep(1/10)
    
    del bt
