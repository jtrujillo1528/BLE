import bluetooth
import random
import time
import machine
import ubinascii
from micropython import const
from machine import Pin
import bleBroadcast
import readScan
import asyncio

_TELESCOPE_UUID = bluetooth.UUID(0x0102)
deviceName = 0x1234

# Add a simple ledger to keep track of processed messages
message_ledger = []

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
    scanData = readScan.runScan(ble, deviceType)
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
    return output

def respond(name, hopCount, distance, sender, messageID, ble):
    led = Pin('LED', Pin.OUT)
    led.value(True)

    if hopCount > 0:
        hopCount -= 1
        message_forward = bleBroadcast.BLEPing(ble, name=name, hopCount=hopCount, mfg=_TELESCOPE_UUID, distance=distance, sender=sender, messageID=messageID)
        message_forward.blePing()
        time.sleep_ms(1)
        
    led.value(False)

async def main():
    print('scanning...')
    while True:
        print('...')
        ble = bluetooth.BLE()
        node = readScan.BLENode(ble, _TELESCOPE_UUID)
        result = await read(ble, node)
        if result:
            for device in result:
                # Check if we've already processed this message
                message_key = device['messageID']
                if message_key not in message_ledger:
                    # Process the message
                    respond(name=device['name'], hopCount=device['hops'], distance=device['distance'], sender=device['sender'], messageID=device['messageID'], ble=ble)
                    
                    # Add the message to the ledger
                    message_ledger.append(message_key)
                    
                    if len(message_ledger) > 10:
                        message_ledger.pop(0)
                        print("ledger shortened")
                else:
                    print(f"Skipping already processed message: {message_key}")
        await asyncio.sleep(0.05)

asyncio.run(main())