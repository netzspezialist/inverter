import asyncio
import random
import time
import paho.mqtt.client as mqtt

from inverter_commands import InverterCommands
from inverter_config import mqtt as mqttConfig
from inverter_config import smartbms as smartbmsConfig

class SmartBatteryManagementSystem:
    def __init__(self, logger, inverterCommands: InverterCommands):
        self.logger = logger
        self.inverterCommands = inverterCommands
        self.logger.info('Creating mqtt client ...')
        client_id = mqttConfig[f"client_id"]
        client_id += f'_{random.randint(0, 1000)}' 
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id)
  
        self.topic = smartbmsConfig["topic"]
        self.enabled = smartbmsConfig["enabled"]
        self.influxUpload = smartbmsConfig["influxUpload"]
        self.influxUploadMinimumDelaySeconds = smartbmsConfig["influxUploadMinimumDelaySeconds"]
        

    def connect(self):
        if not self.enabled:
            return

        def on_connect(client, userdata, flags, rc, properties):
            if rc == 0:
                self.logger.info("Connected to MQTT Broker!")
                self.logger.debug(f'Data: client {client} userdata {userdata} flags {flags} rc {rc} properties {properties}')
                self.logger.debug(f'Subscribing to topic {self.topic}') 
                self.client.subscribe(self.topic)
            else:
                self.logger.error(f"Failed to connect, return code [{rc}]")

        broker_address = mqttConfig["broker_address"]
        port = mqttConfig["port"]
        self.logger.info(f'Connecting to mqtt broker {broker_address}:{port}')

        self.client.on_connect = on_connect
        self.client.on_message = self.on_message
        self.client.connect(broker_address, port)
        self.client.loop_start()

    def on_message(self, client, userdata, message):
        self.logger.debug(f'Message received: {message.payload.decode()}')

        

    def uploadToInflux(self, data):
        self.logger.debug(f'Uploading data to influx: {data}')


    def setVoltage(self, targetVoltage):
        self.logger.debug(f'Setting voltage to {targetVoltage}')

        currentSettings = self.inverterCommands.qpiri()
        currentBulkVoltage = currentSettings["batteryBulkVoltage"]
        currentFloatVoltage = currentSettings["batteryFloatVoltage"]

        self.logger.debug(f'Current bulk voltage: {currentBulkVoltage}')
        self.logger.debug(f'Current float voltage: {currentFloatVoltage}')

        if targetVoltage == currentBulkVoltage:
            self.logger.debug('Voltage already set to desired value')
            return
        
        if targetVoltage > currentBulkVoltage:
            currentBulkVoltage += 0.1
            self.logger.debug(f'increasing voltage to [{currentBulkVoltage}]')
            return

        self.logger.debug(f'Current settings: {currentSettings}')
        self.inverterCommands.updateSetting("batteryBulkVoltage", targetVoltage)

    def disconnect(self):
        if not self.enabled:
            return
        self.serviceRunning = False    
            
        self.logger.info('Disconnecting from MQTT broker')
        self.client.loop_stop()
        self.client.disconnect()        

    def start(self):
        self.logger.info('Starting battery manager ...')
        self.serviceRunning = True
        self.mqtt.connect()

        loop = asyncio.new_event_loop()
        loop.create_task(self.loop())
        try:
            loop.run_forever()      
        finally:
            loop.close()

        self.logger.info('Inverter battery manager stopped')

    def stop(self):
        self.logger.info('Stopping inverter battery manager ...')

    def loop(self):
        self.logger.info('Inverter battery manager loop started ')
        while self.serviceRunning:
            # check for message validity
            time.sleep(5)