# import bluetooth as bt


# if __name__ == "__main__":
#     nearby_devices = bt.discover_devices(lookup_names=True, duration=3)
#     print("Found {} devices.".format(len(nearby_devices)))

#     for addr, name in nearby_devices:
#         print("  {}({})".format(name, addr))
import serial
import time

port = "COM8"
print("waiting for connection on " + port)
travis = serial.Serial(port=port, baudrate=38400)
print("Connected")
endTime = time.time()+20
while time.time()<endTime:
    data = travis.read()
    if data:
        if(data.decode('utf-8') == "q"):
            break
        print(data.decode(), end = "")
print("closing...")
travis.close()