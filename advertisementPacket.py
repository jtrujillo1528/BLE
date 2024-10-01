# Helpers for generating BLE advertising payloads.

from micropython import const
import struct
import bluetooth
from machine import unique_id
import ubinascii
import network
import time
import random


# Advertising payloads are repeated packets of the following form:
#   1 byte data length (N + 1)
#   1 byte type (see constants below)
#   N bytes type-specific data

_ADV_TYPE_FLAGS = const(0x01)
_ADV_TYPE_NAME = const(0x02)
_ADV_TYPE_SENDER = const(0x08)
_ADV_TYPE_UUID16_COMPLETE = const(0x3)
_ADV_TYPE_UUID32_COMPLETE = const(0x5)
_ADV_TYPE_UUID128_COMPLETE = const(0x7)
_ADV_TYPE_INT = const(0x9)
_ADV_TYPE_ID = const(0x4)
_ADV_TYPE_DIST = const(0x6)
'''
_ADV_TYPE_UUID16_MORE = const(0x2)
_ADV_TYPE_UUID32_MORE = const(0x4)
_ADV_TYPE_UUID128_MORE = const(0x6)
_ADV_TYPE_APPEARANCE = const(0x19)'''
_ADV_TYPE_MANUFACTURER = const(0xFF)


# Generate a payload to be passed to gap_advertise(adv_data=...).
def advertising_payload(name=None, services=None, manufacturer_data=None, hopCount=0, distance=None, sender=None, messageID=0):
    payload = bytearray()
   
    def _append(adv_type, value):
        nonlocal payload
        if isinstance(value, int):
            data = struct.pack("B", value)
        elif isinstance(value, float):
            data = struct.pack("f", value)
        elif isinstance(value, str):
            data = value.encode()
        else:
            data = bytes(value)
        payload += struct.pack("BB", len(data) + 1, adv_type) + data

    if manufacturer_data:
        _append(_ADV_TYPE_MANUFACTURER, manufacturer_data)

    if services:
        for uuid in services:
            b = bytes(uuid)
            if len(b) == 2:
                _append(_ADV_TYPE_UUID16_COMPLETE, b)
            elif len(b) == 4:
                _append(_ADV_TYPE_UUID32_COMPLETE, b)
            elif len(b) == 16:
                _append(_ADV_TYPE_UUID128_COMPLETE, b)

    if name:
        _append(_ADV_TYPE_NAME, name)
   
    _append(_ADV_TYPE_INT, hopCount)
  
    if distance is not None:
        _append(_ADV_TYPE_DIST, distance)

    if sender:
        _append(_ADV_TYPE_SENDER, sender)

    _append(_ADV_TYPE_ID, messageID)

    return payload

def decode_field(payload, adv_type):
    i = 0
    result = []
    while i + 1 < len(payload):
        if payload[i + 1] == adv_type:
            result.append(payload[i + 2 : i + payload[i] + 1])
        i += 1 + payload[i]
    return result


def decode_name(payload):
    n = decode_field(payload, _ADV_TYPE_NAME)
    return str(n[0], "utf-8") if n else ""

def decode_mfg(payload):
    n = decode_field(payload, _ADV_TYPE_MANUFACTURER)
    return str(n[0], "utf-8") if n else ""

def decode_hop(payload):
    n = decode_field(payload, _ADV_TYPE_INT)
    return str(n[0], "utf-8") if n else ""

def decode_distance(payload):
    n = decode_field(payload, _ADV_TYPE_DIST)
    return str(n[0], "utf-16") if n else ""

def decode_sender(payload):
    n = decode_field(payload, _ADV_TYPE_SENDER)
    return str(n[0], "utf-8") if n else ""

def decode_id(payload):
    n = decode_field(payload, _ADV_TYPE_ID)
    return str(n[0], "utf-16") if n else ""


def decode_services(payload):
    services = []
    for u in decode_field(payload, _ADV_TYPE_UUID16_COMPLETE):
        services.append(bluetooth.UUID(struct.unpack("<h", u)[0]))
    for u in decode_field(payload, _ADV_TYPE_UUID32_COMPLETE):
        services.append(bluetooth.UUID(u))
    for u in decode_field(payload, _ADV_TYPE_UUID128_COMPLETE):
        services.append(bluetooth.UUID(u))
    return services


def demo():
    while True:
        hopCount = 1
        messageIdentifier = random.randint(0000,1111)
        payload = advertising_payload(
            name= 0x1234,
            manufacturer_data=bluetooth.UUID(0x0102),
            hopCount=hopCount,
            distance=7.94,
            sender = 0x5678,
            messageID=messageIdentifier
        )
        print(payload)
        time.sleep_ms(5000)

if __name__ == "__main__":
    demo()