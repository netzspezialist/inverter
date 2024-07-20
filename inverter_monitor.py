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
        self.last_execution_date = None  # Initialize last execution date

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

                # Reset bulk and float voltage to standard values at 20:00
                now = datetime.now()
                specific_time = now.replace(hour=20, minute=00, second=0, microsecond=0)

                # Check if current date is different from last execution date
                if self.last_execution_date != now.date():
                    # If current time is close to the specific time (within 600 seconds here)
                    if abs((now - specific_time).total_seconds()) < 600:
                        self.logger.info("Resetting inverter settings to standard values")
                        response = self.inverterCommands.updateSetting("batteryFloatVoltage", "54.6")
                        response_string = str(response)
                        self.logger.info(f'Update batteryFloatVoltage response: {response_string}')
                        if "ACK" in response_string:
                            await asyncio.sleep(2)
                            response = self.inverterCommands.updateSetting("batteryBulkVoltage", "54.6")
                            response_string = str(response)
                            self.logger.info(f'Update batteryBulkVoltage response: {response_string}')
                            if "ACK" in response_string.strip():
                                self.logger.info("Inverter settings updated successfully")
                                # Update last execution date to today
                                self.last_execution_date = now.date()
                            else:    
                                self.logger.error("Inverter bulk setting update failed")
                        else:   
                            self.logger.error("Inverter float setting update failed")                                                                                            

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
  
  