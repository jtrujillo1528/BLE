import bluetooth
import struct
import time
from micropython import const
from machine import Pin
import ubinascii

_IRQ_SCAN_RESULT = const(5)
_IRQ_SCAN_DONE = const(6)

_ADV_TYPE_FLAGS = const(0x01)
_ADV_TYPE_NAME = const(0x09)
_ADV_TYPE_UUID16_COMPLETE = const(0x03)
_ADV_TYPE_UUID32_COMPLETE = const(0x05)
_ADV_TYPE_UUID128_COMPLETE = const(0x07)
_ADV_TYPE_UUID16_MORE = const(0x02)
_ADV_TYPE_UUID32_MORE = const(0x04)
_ADV_TYPE_UUID128_MORE = const(0x06)
_ADV_TYPE_APPEARANCE = const(0x19)
_ADV_TYPE_MANUFACTURER = const(0xFF)
_ADV_TYPE_INT = const(0x0A)
_ADV_TYPE_DIST = const(0x16)
_ADV_TYPE_SENDER = const(0x17)
_ADV_TYPE_ID = const(0x18)

class BLENode:
    def __init__(self, ble, target_manufacturer_id=None, ledger=[]):
        if target_manufacturer_id is not None and not isinstance(target_manufacturer_id, bluetooth.UUID):
            raise ValueError("target_manufacturer_id must be a bluetooth.UUID object or None")
        
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        self._reset()
        self._led = Pin('LED', Pin.OUT)
        self.advertisement_data = []
        self.target_manufacturer_id = target_manufacturer_id
        self.message_ledger = ledger  # New: Add message ledger

    def _reset(self):
        self._name = None
        self._addr_type = None
        self._addr = None
        self._scan_callback = None

    def _irq(self, event, data):
        if event == _IRQ_SCAN_RESULT:
            addr_type, addr, adv_type, rssi, adv_data = data
            try:
                decoded_data = self._decode_adv_data(adv_data)
                if decoded_data:
                    mfg_id, hop_count, _, _, _, message_id = decoded_data
                    # Check if it's the target device, hop count > 0, and message not in ledger
                    if (mfg_id == self.target_manufacturer_id and 
                        hop_count > 0 and 
                        message_id not in self.message_ledger):
                        self.advertisement_data.append((ubinascii.hexlify(addr).decode(),) + decoded_data)
                        # Add message to ledger
                        self.message_ledger.append(message_id)
                        # Keep ledger size limited
                        if len(self.message_ledger) > 10:
                            self.message_ledger.pop(0)
                        self._ble.gap_scan(None)
                        event = _IRQ_SCAN_DONE
            except Exception as e:
                print(f"Error decoding advertisement data: {e}")
        if event == _IRQ_SCAN_DONE:
            #print("Scan complete")
            if self._scan_callback:
                if self.advertisement_data:
                    self._scan_callback(self.advertisement_data)
                else:
                    self._scan_callback(None)
            self._scan_callback = None

    def _decode_adv_data(self, adv_data):
        i = 0
        result = {}
        while i + 1 < len(adv_data):
            length = adv_data[i]
            type = adv_data[i + 1]
            value = bytes(adv_data[i + 2:i + length + 1])
            
            try:
                if type == _ADV_TYPE_MANUFACTURER:
                    result['mfg'] = bluetooth.UUID(int.from_bytes(value[:2], 'little'))
                elif type == _ADV_TYPE_NAME:
                    result['name'] = int.from_bytes(value, 'big')
                elif type == _ADV_TYPE_INT:
                    result['hop'] = int.from_bytes(value, 'big') if value else None
                elif type == _ADV_TYPE_DIST:
                    result['distance'] = struct.unpack('f', value)[0] if len(value) == 4 else None
                elif type == _ADV_TYPE_SENDER:
                    result['sender'] = int.from_bytes(value, 'big') if value else None
                elif type == _ADV_TYPE_ID:
                    result['message_id'] = int.from_bytes(value, 'big') if value else None
            except Exception as e:
                print(f"Error decoding field type {type}: {e}")
            
            i += length + 1
        
        if result:
            return (result.get('mfg'), result.get('hop'), result.get('distance'), 
                    result.get('sender'), result.get('name'), result.get('message_id'))
        return None

    def scan(self, callback=None):
        self._reset()
        self._scan_callback = callback
        self.advertisement_data = []
        self._ble.gap_scan(500, 10000, 9000)  # Scan duration: 10 seconds

class Advertiser:
    def __init__(self, data):
        if data and len(data) >= 7:
            self.mac = data[0]
            self.mfg = data[1]
            self.hops = data[2]
            self.dist = data[3]
            self.sender = data[4]
            self.name = data[5]
            self.messageID = data[6]
        else:
            self.mac = self.mfg = self.hops = self.dist = self.sender = self.name = self.messageID = None

    def getHops(self):
        return self._decode_value(self.hops)

    def getDistance(self):
        return self._decode_value(self.dist)
    
    def getSender(self):
        return self._decode_value(self.sender)
    
    def getMessageID(self):
        return self._decode_value(self.messageID)

    def getName(self):
        return self._decode_value(self.name)

    def _decode_value(self, value):
        if isinstance(value, (int, float)):
            return value
        elif isinstance(value, str):
            try:
                return int(value, 16)  # Try to decode as hex
            except ValueError:
                try:
                    return int(value)  # Try to decode as decimal
                except ValueError:
                    return value  # Return as is if it can't be converted
        return None

def runScan(ble, central):
    scan_complete = False
    
    def on_scan(result):
        nonlocal scan_complete
        if result:
            '''            print("Scan complete. Found devices:")
            for device in result:
                advertiser = Advertiser(device)
                print(f"MAC: {advertiser.mac}")
                print(f"MFG: {advertiser.mfg}")
                print(f"Hops: {advertiser.getHops()}")
                print(f"Distance: {advertiser.getDistance()}")
                print(f"Sender: {advertiser.getSender()}")
                print(f"Name: {advertiser.getName()}")
                print(f"MessageID: {advertiser.getMessageID()}")
        else:
            print("No devices found.")'''
        scan_complete = True

    central.scan(callback=on_scan)
    
    # Wait for scan to complete or timeout after 10 seconds
    start_time = time.ticks_ms()
    while not scan_complete and time.ticks_diff(time.ticks_ms(), start_time) < 100000:
        time.sleep_ms(10)
    
    if not scan_complete:
        print("Scan timed out")
    
    return central.advertisement_data, central.message_ledger

if __name__ == "__main__":
    ble = bluetooth.BLE()
    TARGET_MANUFACTURER_ID = bluetooth.UUID(0x0102)  # This is equivalent to 258
    central = BLENode(ble, TARGET_MANUFACTURER_ID)
    while True:
        print("\nStarting new scan cycle...")
        runScan(ble, central)
        time.sleep_ms(5)