influx = {
    "enabled": True,
    "url": "http://192.168.88.2:8086",
    "org": "org",
    "bucket": "energy",
    "token": '8NSTtcmBwEUUoOl5E3nhvoIOwIzZgNbUbOpdhN7UOMY452Y7srgClN5JZBerPSBBlelIR2Q6ZSukRqPg77GZOA==',
}
mqtt = { 
    "enabled": True,
    "broker_address": "localhost",
    "port": 1883,
    "client_id": "inverter",
    "topic": "inverter",
    "username": "user",
    "password": "password"
}
inverterBatteryManager = {
    "enabled": True,
    "topic": "bms-commands",
    "defaultVoltage": "54.8"
}
inverter = {
    "connectionType": "serial",  # serial or usb
    "port": "/dev/ttyUSB0" # serial port /dev/ttyUSB0" or usb device /dev/hidraw0
}