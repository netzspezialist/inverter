import asyncio
import datetime
import json
import random
import time
import traceback
import paho.mqtt.client as mqtt

from inverter_commands import InverterCommands
from inverter_config import mqtt as mqttConfig
from inverter_config import smartbms as smartbmsConfig
from inverter_config import influx as influxConfig

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

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
        self.influxUploadEnabled = smartbmsConfig["influxUploadEnabled"]
        self.influxUploadMinimumDelaySeconds = smartbmsConfig["influxUploadMinimumDelaySeconds"]
        self.influxLastUploadTime = None  # Initialize the last upload time

        self.enabled = influxConfig["enabled"]
        token = influxConfig["token"]
        org = influxConfig["org"]
        bucket = influxConfig["bucket"]
        url = influxConfig["url"]
        write_client = InfluxDBClient(url=url, token=token, org=org)

        self.org=org
        self.bucket=bucket
        self.write_api = write_client.write_api(write_options=SYNCHRONOUS)
        

    def _connect(self):

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
        try:
            payload = message.payload.decode()
            self.logger.debug(f'Message received: {payload}')
        
            data = json.loads(payload)

            timestamp = datetime.datetime.now()

            soc = float(data['Pack']['SOC'])
            voltage = float(data['Pack']['Voltage'])
            current = float(data['Pack']['Current'])
            temperature = data['Pack']['BMS_Temp']
            voltages = [data['CellV'][f'CellV_{i}'] for i in range(1, 17)]

            highestCellVoltage = max(voltages)
            lowestCellVoltage = min(voltages)

            self.logger.debug(f'Voltage: {voltage}V, SOC: {soc}%, Current: {current}A, Temperature: {temperature}°C, Cell voltages: {voltages}')

            if not self.influxUploadEnabled:
                return
            
            if self.influxLastUploadTime and (timestamp - self.influxLastUploadTime).total_seconds() < self.influxUploadMinimumDelaySeconds:
                self.logger.debug('Minimum delay not reached, skipping upload.')
                return

            point = (
                Point("bms")
                .field("voltage", voltage)
                .field("soc", soc)
                .field("current", current)
                .field("temperature", temperature)
                .field("cellVoltage01", voltages[0])
                .field("cellVoltage02", voltages[1])
                .field("cellVoltage03", voltages[2])
                .field("cellVoltage04", voltages[3])
                .field("cellVoltage05", voltages[4])
                .field("cellVoltage06", voltages[5])
                .field("cellVoltage07", voltages[6])
                .field("cellVoltage08", voltages[7])
                .field("cellVoltage09", voltages[8])
                .field("cellVoltage10", voltages[9])
                .field("cellVoltage11", voltages[10])
                .field("cellVoltage12", voltages[11])
                .field("cellVoltage13", voltages[12])
                .field("cellVoltage14", voltages[13])
                .field("cellVoltage15", voltages[14])
                .field("cellVoltage16", voltages[15])
                .field("highestCellVoltage", highestCellVoltage)
                .field("lowestCellVoltage", lowestCellVoltage)            
                .time(int(timestamp.timestamp()), WritePrecision.S)
            )
            
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            self.influxLastUploadTime = timestamp

        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            self.logger.error(traceback.format_exc())

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
        if not self.enabled:
            self.logger.info('Smart BMS Client is disabled')
            return

        self.logger.info('Starting Smart BMS Client ...')

        self.serviceRunning = True
        self._connect()

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
            time.sleep(2)