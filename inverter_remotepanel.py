import time
from inverter_energy_data import InverterEnergyData
from inverter_mqtt import InverterMqtt

class InverterRemotePanel:
    def __init__(self, logger, inverterEnergyData: InverterEnergyData):
        self.logger = logger
        self.inverterMqtt : InverterMqtt = InverterMqtt(logger)
        self.inverterEnergyData = inverterEnergyData

    def __loop(self):
        while self.serviceRunning:
            try:
                self.logger.debug('Inverter remote panel loop running ...')
                energy = self.inverterEnergyData.getEnergy('Output', 20240000)
                self.inverterMqtt.publish_message('energyOutput', energy)
                time.sleep(60)
            except Exception as e:
                self.logger.error(f'Error in inverter remote panel loop: {e}')

    def start(self):
        self.logger.info('Starting remote panel ...')
        self.serviceRunning = True
        self.__loop()

    def stop(self):
        self.logger.info('Stopping remote panel ...')
        self.serviceRunning = False
