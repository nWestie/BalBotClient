import serial
import time


class BTHandler:
    def __init__(self, port: str) -> None:
        self.btDataStr = ""
        self.bot = serial.Serial(port=port, baudrate=38400)

    def readBT(self) -> None:
        numBytes = self.bot.in_waiting
        if numBytes > 0:
            self.btDataStr = self.btDataStr + self.bot.read(numBytes).decode()
    def parse(self):
        data = self.btDataStr
        if(data[0] != "*"):
            data = data[data.index("*"):]
        
    def __del__(self):
        self.bot.close()
        print("closed BT COM Port")


if __name__ == "__main__":
    bt = BTHandler("COM8")
    endTime = time.time()+5
    while time.time() < endTime:
        bt.readBT()
        print(len(bt.btDataStr))
        time.sleep(1/10)
    print(bt.btDataStr)
    del bt
