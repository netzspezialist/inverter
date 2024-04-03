# inverter

## description
Control and monitor (Voltronic) Axpert Max inverter or similar from raspberry pi.\
Use USB to RS232 converter and connect to inverters RS232 (RJ45) connector.\
Do not use USB to USB!\
Inverters USB is OTG and feeds RP PI with 5V. Reboot is not possible anymore until 5V wire is cut.\
Inverters USB do not support all commands (QPIGS2).


## requirements
```
sudo apt install python3-pip
sudo apt install mosquitto
pip3 install influxdb-client
pip3 install paho-mqtt
pip3 install flask
pip3 install crcmod
```

## install and start inverter service for monitoring
```
sudo cp inverter.service /etc/systemd/system/inverter.service
sudo systemctl daemon-reload
sudo systemctl enable inverter.service
sudo systemctl start inverter.service
```


## kill hanging service
```
top -c -p $(pgrep -d',' -f python3)
kill <pid>
```

## add user tty permission
```
sudo usermod -a -G plugdev <username>

sudo nano /etc/udev/rules.d/99-usb-serial-permissions.rules
CONTENT:
KERNEL=="hidraw*", SUBSYSTEM=="hidraw", MODE="0660", GROUP="plugdev"
KERNEL=="ttyUSB*", SUBSYSTEM=="tty", MODE="0660", GROUP="plugdev"
```