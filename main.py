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

class Advertiser:
    def __init__(self, data):
        self.mac = data[0]
        self.mfg = data[1]
        self.hops = data[2]
        self.distance = data[3]
        self.sender = data[4]
        self.name = data[5]
        self.messageID = data[6]

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
            'hops': accessedData.getHops(),
            'distance': accessedData.getDistance(),
            'sender': accessedData.getSender(),
            'messageID': accessedData.getMessageID()
        })
    return output

def broadcast(hopCount, distance, sender, messageID, ble):
    led = Pin('LED', Pin.OUT)
    led.value(True)

    temp = bleBroadcast.BLEPing(ble, name=deviceName, hopCount=hopCount, mfg=_TELESCOPE_UUID, distance=distance, sender=sender, messageID=messageID)
    
    temp.blePing()
    time.sleep_ms(1)
        
    led.value(False)

async def main():
    print('scanning...')
    while True:
        print('...')
        ble = bluetooth.BLE()
        central = readScan.BLENode(ble, _TELESCOPE_UUID)
        result = await read(ble, central)
        print("Processed result:", result)
        '''        if result:
            for device in result:
                broadcast(hopCount=device['hops'], distance=device['distance'], sender=device['sender'], messageID=device['messageID'], ble=ble)'''
        await asyncio.sleep(0.05)

asyncio.run(main())