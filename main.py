import bluetooth
import time
from machine import Pin
from bleBroadcast import BLEPing, BLEDeviceInit
import readScan
import asyncio

# Initialize BLE device
_TELESCOPE_UUID = bluetooth.UUID(0x0102)
deviceName = 0x1234
device_type = 1  # Example device type

# Set up LED for visual feedback
led = Pin('LED', Pin.OUT)
    

class Advertiser:
    def __init__(self, data):
        self.mac = data[0]
        self.mfg = data[1]
        self.hops = data[2]
        self.distance = data[3]
        self.sender = data[4]
        self.name = data[5]
        self.messageID = data[6]

    def getName(self):
        return self.name

    def getHops(self):
        return self.hops

    def getDistance(self):
        return self.distance

    def getSender(self):
        return self.sender

    def getMessageID(self):
        return self.messageID

async def read(ble, deviceType):
    scanData, ledger = readScan.runScan(ble, deviceType)
    print("Scan Data:", scanData)
    output = []
    for data in scanData:
        accessedData = Advertiser(data)
        output.append({
            'name': accessedData.getName(),
            'hops': accessedData.getHops(),
            'distance': accessedData.getDistance(),
            'sender': accessedData.getSender(),
            'messageID': accessedData.getMessageID()
        })
    return output, ledger

def respond(name, hopCount, distance, sender, messageID, ble):
    led = Pin('LED', Pin.OUT)
    led.value(True)

    hopCount -= 1
    message_forward = BLEPing(ble, name=name, hopCount=hopCount, mfg=_TELESCOPE_UUID, distance=distance, sender=sender, messageID=messageID)
    message_forward.blePing()
    time.sleep(0.001)
        
    led.value(False)

async def init_device(device_type, manufacturer):

    #update later once mobil app is working

    led.on()  # Turn on LED for visual feedback

    # Initialize BLE
    ble = bluetooth.BLE()
    device = BLEDeviceInit(ble, device_type=device_type, manufacturer=manufacturer)

    # Broadcast the BLE advertisement
    device.broadcast()

    
    time.sleep_ms(10)
    
    led.off()  # Turn off LED
    
    # Add a small delay to prevent multiple broadcasts on a single press
    time.sleep_ms(200)
    return True

async def read_and_respond(ledger):
    ble = bluetooth.BLE()
    node = readScan.BLENode(ble, _TELESCOPE_UUID, ledger)
    result, ledger = await read(ble, node)
    if result:
        for device in result:
            # Process the message
            respond(name=device['name'], hopCount=device['hops'], distance=device['distance'], sender=device['sender'], messageID=device['messageID'], ble=ble)
    await asyncio.sleep(0.05)
    return ledger

async def main():
    ledger = []
    while True:
        ledger = await read_and_respond(ledger)

asyncio.run(main())