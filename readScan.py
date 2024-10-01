import bluetooth
import random
import struct
import time
import micropython
from advertisementPacket import decode_services, decode_name, decode_field, decode_hop, decode_mfg, decode_distance, decode_sender
from micropython import const
from machine import Pin
import ubinascii



_IRQ_SCAN_RESULT = const(5)
_IRQ_SCAN_DONE = const(6)

_ADV_IND = const(0x00)
_ADV_DIRECT_IND = const(0x01)
_ADV_SCAN_IND = const(0x02)
_ADV_NONCONN_IND = const(0x03)
_ADV_TYPE_MANUFACTURER = const(0xFF)
_ADV_TYPE_TIME = const(0x4)
_ADV_TYPE_INT = const(0x9)
_ADV_TYPE_STAMP = const(0x6)

_FLAG_READ = const(0x0002)
_FLAG_NOTIFY = const(0x0010)
_FLAG_INDICATE = const(0x0020)


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

class BLENode:
    def __init__(self, ble):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        self._reset()
        self._led = Pin('LED', Pin.OUT)
        self.advertisement_data = []

    def _reset(self):
        # Cached name and address from a successful scan.
        self._name = None
        self._addr_type = None
        self._addr = None

        # Cached value (if we have one)
        self._value = None

        # Callbacks for completion of various operations.
        # These reset back to None after being invoked.
        self._scan_callback = None
        self._conn_callback = None
        self._read_callback = None

        # Persistent callback for when new data is notified from the device.
        self._notify_callback = None

        # Connected device.
        self._conn_handle = None
        self._start_handle = None
        self._end_handle = None
        self._value_handle = None

    def _irq(self, event, data):
        if event == _IRQ_SCAN_RESULT:
            addr_type, addr, adv_type, rssi, adv_data = data
            if adv_type in (_ADV_IND, _ADV_DIRECT_IND):
                type_list = decode_services(adv_data)
                if _AUTORANGING_UUID in type_list:
                    try:
                        # Found a potential device, remember it and stop scanning.
                        self._addr_type = addr_type
                        self._addr = bytes(addr)  # Note: addr buffer is owned by caller so need to copy it.
                        self._name = decode_name(adv_data) or "?"
                        self._mfg = decode_mfg(adv_data)
                        self._hop = decode_hop(adv_data)
                        self._distance = decode_distance(adv_data)
                        self._sender = decode_sender(adv_data)
                        self.advertisement_data.append((ubinascii.hexlify(addr).decode(), self._mfg, self._hop, 
                                                        self._distance, self._sender, decode_name(adv_data)))
                        self._ble.gap_scan(None)
                    except: 
                        print('data is un-readable')

        elif event == _IRQ_SCAN_DONE:
            if self._scan_callback:
                if self._addr:
                    # Found a device during the scan (and the scan was explicitly stopped).
                    self._scan_callback(self._addr_type, self._addr, self._name)
                    self._scan_callback = None
                    #print(self.advertisement_data)
                else:
                    # Scan timed out.
                    self._scan_callback(None, None, None)

    def get_advertisement_data(self):
        scanData = self.advertisement_data.copy()
        self.advertisement_data.clear()
        return scanData


    # Find a device advertising the environmental sensor service.
    def scan(self, callback=None):
        self._addr_type
        self._addr = None
        self._scan_callback = callback
        self._ble.gap_scan(2000, 30000, 30000)

def sleep_ms_flash_led(self, flash_count, delay_ms):
    self._led.off()
    while(delay_ms > 0):
        for i in range(flash_count):            
            self._led.on()
            time.sleep_ms(100)
            self._led.off()
            time.sleep_ms(100)
            delay_ms -= 200
        time.sleep_ms(1000)
        delay_ms -= 1000

not_found = False

def on_scan( addr_type, addr, name):
    if addr_type is not None:
        print("Found sensor: %s" % name)
    else:
        print("No sensor found lol.")

def runScan(ble, central):
    not_found = False
    central.scan(callback=on_scan)
    while central._scan_callback is not None and not_found == False:
        dataGathered = central.get_advertisement_data()
        if dataGathered == []:
            not_found = True
    return dataGathered

if __name__ == "__main__":
    ble = bluetooth.BLE()
    central = BLENode(ble)
    while(True):
        runScan(ble, central)
        sleep_ms_flash_led(central, 1, 2000)  