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
    #print("Scan Data:", scanData)
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
    message_forward = bleBroadcast.BLEPing(ble, name=name, hopCount=hopCount, mfg=_TELESCOPE_UUID, distance=distance, sender=sender, messageID=messageID)
    message_forward.blePing()
    time.sleep(0.001)
        
    led.value(False)

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
    print("scanning...")
    while True:
        ledger = await read_and_respond(ledger)

asyncio.run(main())