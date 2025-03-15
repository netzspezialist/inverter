
from inverter_commands import InverterCommands
from inverter_mqtt import InverterMqtt


class InverterChargeManager:
    def __init__(self, logger, inverterCommands: InverterCommands):
        self.logger = logger
        self.inverterCommands = inverterCommands
        self.mqtt = InverterMqtt(logger)

    def __loop(self):
        while self.serviceRunning:
    
        self.mqtt.disconnect()
        self.logger.info('Inverter monitor loop stopped')



    def start(self):
        self.logger.info('Starting inverter monitoring ...')        
        self.mqtt.connect()
        self.serviceRunning = True

        self.__loop();

        self.logger.info('Inverter monitoring stopped')

    def stop(self):
        self.logger.info('Stopping inverter monitoring ...')
        self.serviceRunning = False   
  