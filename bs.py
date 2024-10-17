import machine
import ubluetooth

bt = ubluetooth.BLE()

bt.active(True)

_, mac_address = bt.config('mac')

print(''.join('%02X' % b for b in mac_address))