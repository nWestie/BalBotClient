import serial
from time import time


def main():
    """Opens BT Serial Connection"""
    try:
        print("Connecting...")
        with serial.Serial(port="COM6", baudrate=38400, timeout=0.25) as bt:
            print("Connected")
            startTime = time()
            lastSendTime = time()
            while time() - startTime < 20:
        
                print(bt.readall().decode())

                if time() - lastSendTime > 1:
                    bt.write(f"testing: {int(time()-startTime)} /".encode("ascii"))
                    lastSendTime = time()
        
        print("Disconnected")
    except:
        print("Bluetooth Connection Error")


if __name__ == "__main__":
    exit(main())
