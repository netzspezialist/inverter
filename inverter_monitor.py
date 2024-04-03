import asyncio
from datetime import datetime
import json
from inverter_commands import InverterCommands
from inverter_influx import InverterInflux
from inverter_mqtt import InverterMqtt


class InverterMonitor:
    def __init__(self, logger, inverterCommands: InverterCommands):
        self.logger = logger
        self.influx = InverterInflux(logger)
        self.inverterCommands = inverterCommands
        self.mqtt = InverterMqtt(logger)

    def start(self):
        self.logger.info('Starting inverter monitoring ...')
        self.serviceRunning = True
        self.mqtt.connect()

        loop = asyncio.new_event_loop()
        loop.create_task(self.loop())
        try:
            loop.run_forever()      
        finally:
            loop.close()

        self.logger.info('Inverter monitoring stopped')

    def stop(self):
        self.logger.info('Stopping inverter monitoring ...')
        self.serviceRunning = False    
        self.mqtt.disconnect()

    async def loop(self):
        self.logger.info('Inverter monitor loop started ')
        while self.serviceRunning:  
            try:
                self.logger.debug('Inverter monitor loop running ...')
                data = self.inverterCommands.qpigs()
                self.influx.upload_qpigs(data["timestamp"], data)
                self.logger.debug(f'Inverter data: {data}')
                data["timestamp"] = data["timestamp"].isoformat()[:-3]
                jsonData = json.dumps(data, default=self.serialize_datetime)
                self.logger.debug(f'Publishing to MQTT: {jsonData}')
                self.mqtt.publish_message("qpigs", jsonData)
                
                await asyncio.sleep(2)
            except Exception as e:
                self.logger.error(f'Inverter monitor loop failed: {e}')
                await asyncio.sleep(10)

        self.logger.info('Inverter monitor loop stopped')

    def serialize_datetime(obj): 
        if isinstance(obj, datetime.datetime): 
            return obj.isoformat() 
        raise TypeError("Type not serializable") 
  
  