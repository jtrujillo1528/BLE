import bluetooth
import random
import struct
import time
import machine
import ubinascii
from advertisementPacket import advertising_payload
from micropython import const
from machine import Pin
import network
import bleBroadcast
import readScan
import asyncio


_TELESCOPE_UUID = bluetooth.UUID(0x0102)
deviceName = 0x1234

class Advertiser:
    def __init__(self, dataList):
        if dataList != []:
            '''        print(len(dataList))
            print(type(dataList[0][2]))
            print(repr(dataList[0][3]))'''
            self.mac = dataList[0][0]
            self.hops = dataList[0][2]
            self.dist = dataList[0][3]
            self.sender = dataList[0][4]
            self.name = dataList[0][5]
            self.messageID = dataList[0][6]
        else: 
            return

    def getHops(self):
        data_bytes = self.hops.encode('latin-1')
        number = int.from_bytes(data_bytes, 'big')
        return number 

    def getDistance(self):
        data_bytes = self.dist.encode('latin-1')
        number = int.from_bytes(data_bytes, 'big')
        return number 
    
    def getSender(self):
        data_bytes = self.sender.encode('latin-1')
        number = int.from_bytes(data_bytes, 'big')
        return number 
    
    def getMessageID(self):
        data_bytes = self.messageID.encode('latin-1')
        number = int.from_bytes(data_bytes, 'big')
        return number 
            


async def read(ble, deviceType):
    scanData = readScan.runScan(ble, deviceType)
    print(scanData)
    output = []
    if scanData != []:
        accessedData = Advertiser(scanData)
        output.append(accessedData.getHops())
        output.append(accessedData.getDistance())
        output.append(accessedData.getSender())
        output.append(accessedData.getMessageID())
    return output

def broadcast(name, hopCount, distance, sender, messageID, ble):
    led = Pin('LED', Pin.OUT)
    led.value(True)

    temp = bleBroadcast.BLEPing(ble, name=name, hopCount=hopCount, mfg=_TELESCOPE_UUID, distance=distance, sender=sender, messageID=messageID)
    
    temp.blePing()
    time.sleep_ms(1)
        
    led.value(False)

async def main():
    print('broadcasting')
    while True:
        #messageIdentifier = random.randint(0000,9999)
        ble = bluetooth.BLE()
        broadcast(name= deviceName, hopCount=1, distance=7.94, sender=0x5678, messageID= 4321, ble=ble)
        await asyncio.sleep(1)
        
asyncio.run(main())