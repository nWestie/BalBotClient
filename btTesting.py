import serial
from time import time


def main():
    """Opens BT Serial Connection"""
    try:
        print("Connecting...")
        with serial.Serial(port="COM6", baudrate=38400, timeout=0.25) as bt:
            print("Connected")
            while True:
                print(bt.read_until(b'/').decode())
                
        print("Disconnected")
    except:
        print("Bluetooth Connection Error")


if __name__ == "__main__":
    exit(main())
