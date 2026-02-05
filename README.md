# inverter

## description
Control and monitor (Voltronic) Axpert Max inverter or similar from raspberry pi.\
Use USB to RS232 converter and connect to inverters RS232 (RJ45) connector.\
Do not use USB to USB!\
Inverters USB is OTG and feeds RP PI with 5V. Reboot is not possible anymore until 5V wire is cut.\
Inverters USB do not support all commands (QPIGS2).


## requirements
```
at home: mkdir energy
cd energy
sudo apt install python3-pip
sudo apt install mosquitto

sudo nano /etc/mosquitto/mosquitto.conf

add to bottom: --------------------------
listener 1883 0.0.0.0
allow_anonymous true
-----------------------------------------

sudo apt install sqlite3
git clone https://github.com/netzspezialist/inverter.git
cd inverter
python3 -m venv venv
source venv/bin/activate
pip3 install pyserial
pip3 install influxdb-client
pip3 install paho-mqtt
pip3 install flask
pip3 install crcmod
pip3 install schedule
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

udevadm info -a -n /dev/ttyUSB0 | grep -E "idVendor|idProduct|manufacturer"
udevadm info -a -n /dev/ttyUSB1 | grep -E "idVendor|idProduct|manufacturer"

sudo nano /etc/udev/rules.d/99-usb-serial-permissions.rules
CONTENT:
KERNEL=="ttyUSB*", SUBSYSTEM=="tty", MODE="0660", GROUP="plugdev" 
SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523" SYMLINK+="usbBMS"
SUBSYSTEM=="tty", ATTRS{idVendor}=="067b", ATTRS{idProduct}=="2303" SYMLINK+="usbINVERTER"
```

sudo reboot