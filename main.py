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
            self.runTime = dataList[0][3]
            self.name = dataList[0][4]
            self.messageID = dataList[0][5]
        else: 
            return

    def getHops(self):
        data_bytes = self.hops.encode('latin-1')
        number = int.from_bytes(data_bytes, 'big')
        return number 

    def getDistance(self):
        data_bytes = self.runTime.encode('latin-1')
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
        output.append(accessedData.getMessageID())
    return output

def broadcast(hopCount, distance, sender, messageID, ble):
    startTime = time.ticks_ms()
    led = Pin('LED', Pin.OUT)
    led.value(True)
    i = 0
    if hopCount != 0:
        hopCount -= 1
        temp = bleBroadcast.BLEPing(ble, name=deviceName, hopCount=hopCount, mfg=_TELESCOPE_UUID, distance=distance, sender=sender, messageID=messageID)
        
        temp.blePing()
        time.sleep_ms(1)
            
        led.value(False)

async def main():
    while True:
        ble = bluetooth.BLE()
        central = readScan.BLENode(ble)
        print('scanning...')
        result = await read(ble,central)
        print(result)
        if result != []:
            broadcast(hopCount=result[0], distance=result[1], sender=result[2], messageID= result[3], ble=ble)
            result = []
        await asyncio.sleep(0.01)
        
asyncio.run(main())