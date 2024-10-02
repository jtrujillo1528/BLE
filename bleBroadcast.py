# This example demonstrates a simple temperature sensor peripheral.
#
# The sensor's local value is updated, and it will notify
# any connected central every 10 seconds.

import bluetooth
import random
import struct
import time
import machine
import ubinascii
from advertisementPacket import advertising_payload, decode_id
from micropython import const
from machine import Pin


_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_INDICATE_DONE = const(20)

_FLAG_READ = const(0x0002)
_FLAG_NOTIFY = const(0x0010)
_FLAG_INDICATE = const(0x0020)

deviceID = bluetooth.UUID(ubinascii.hexlify(machine.unique_id()).decode('utf-8'))
fakeDistance = 23
transmittingDevice = bluetooth.UUID("36336261-3336-6234-3230-313431366969")

# org.bluetooth.service.environmental_sensing
_TELESCOPE_UUID = bluetooth.UUID(0x0102)

_DISTANCE_CHAR = (
    bluetooth.UUID(0x1847),
    _FLAG_READ | _FLAG_NOTIFY | _FLAG_INDICATE,
)

_AUTORANGING_UUID = bluetooth.UUID(0x0001)
_AUTORANGING_SERVICE = (
    _AUTORANGING_UUID,
    (_DISTANCE_CHAR,),
)

_MONITERING_SERVICE = (
    bluetooth.UUID(0x0002)
)

_SENSOR_SERVICE = (
    bluetooth.UUID(0x0003)
)


class BLEPing:
    def __init__(self, ble, mfg=None, name=None, hopCount=0, distance=None, sender=None, messageID=0):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        ((self._handle,),) = self._ble.gatts_register_services((_AUTORANGING_SERVICE,))
        self._connections = set()
        self._payload = advertising_payload(
            services=[_AUTORANGING_UUID],
            name=name,
            manufacturer_data=mfg,
            hopCount=int(hopCount),
            distance=float(distance) if distance is not None else None,
            sender=sender,
            messageID=int(messageID)
        )

    def _irq(self, event, data):
        # Track connections so we can send notifications.
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            self._connections.add(conn_handle)
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            self._connections.remove(conn_handle)
            # Start advertising again to allow a new connection.
            self._advertise()
        elif event == _IRQ_GATTS_INDICATE_DONE:
            conn_handle, value_handle, status = data

    def _advertise(self, interval_us=500000):
        self._ble.gap_advertise(interval_us, adv_data=self._payload)
        print(self._payload)
    
    def blePing(self):
        self._advertise()
        
        
def demo():
    name = 0x1234  # 4460 in decimal
    messageIdentifier = 4321
    ble = bluetooth.BLE()
    led = Pin('LED', Pin.OUT)
    temp = BLEPing(ble, name=name, hopCount=4, mfg=_TELESCOPE_UUID, distance=7.94, sender=0x5678, messageID=messageIdentifier)
    while True:
        temp.blePing()
        led.value(True)
        time.sleep_ms(50)
        led.value(False)
        time.sleep_ms(950)  # Sleep for the rest of the second

if __name__ == "__main__":
    demo()